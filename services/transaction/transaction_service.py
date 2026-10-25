from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation


from fastapi import HTTPException
from sqlalchemy import case, extract, func, null, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from sqlalchemy.orm import selectinload
from model.master.customer_model import CustomerEntity
from model.master.enum_table_model import EnumTableEntity
from model.master.item_model import ItemEntity
from model.admin.configuration_model import ConfigurationEntity
from model.pagination_model import PaginationResponseDTO
from model.transaction.transaction_item_model import TransactionItemEntity
from model.transaction.transaction_model import (
    TopCreditCustomerDTO,
    TopPointCustomerDTO,
    TopProductDTO,
    TransactionDashboardPerDayDTO,
    TransactionDTO,
    TransactionEntity,
    TransactionResponseDTO,
)

class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    
    @staticmethod
    def subtract_months(date: datetime, months: int) -> datetime:
        year = date.year
        month = date.month - months
        while month <= 0:
            month += 12
            year -= 1
        return datetime(year, month, 1)

    @staticmethod
    def parse_point_tiers(value: str) -> List[tuple[Decimal, int]]:
        try:
            tiers = []
            for tier in value.split(";"):
                point_text, threshold_text = tier.split(">", maxsplit=1)
                points = int(point_text.strip())
                threshold = Decimal(threshold_text.strip())
                if points < 0 or not threshold.is_finite() or threshold <= 0:
                    raise ValueError
                tiers.append((threshold, points))

            if not tiers or len({threshold for threshold, _ in tiers}) != len(tiers):
                raise ValueError
            return sorted(tiers)
        except (InvalidOperation, ValueError) as exc:
            raise HTTPException(
                status_code=500,
                detail="Invalid Application.points configuration",
            ) from exc

    async def create_transaction(self, data: TransactionDTO, user: str = None
                                 ) -> Optional[TransactionResponseDTO]:     
        
        try:
                
            # 1. Create transaction entry
            entity = TransactionEntity(
                customer_id=data.customer_id,
                payment_method=data.payment_method,
                discount=data.discount,
                tax_id=data.tax_id,
                tax_value=data.tax_value,
                total=data.total,
                created_at=datetime.utcnow(),
                created_by=user,
            )
            self.session.add(entity)
            await self.session.flush()  
            
            # 2. Create transaction items (if any)
            item_ids = []
            if data.items:
                for item in data.items:
                    detail = TransactionItemEntity(
                        transaction_id=entity.id,   # ✅ link to parent
                        item_id=item.item_id,
                        quantity=item.quantity,
                        price=item.price,
                        created_at=datetime.utcnow(),
                        created_by=user,
                    )
                    self.session.add(detail)
                    item_ids.append(item.item_id)

            
                    
            # Fetch the item from the database
            if item_ids:
                item_result = await self.session.execute(select(ItemEntity).where(ItemEntity.id.in_(item_ids))) 
                item_entities = {i.id: i for i in item_result.scalars().all()}

                # Update stock
                for item in data.items:
                    item_entity = item_entities.get(item.item_id)
                    if not item_entity:
                        raise HTTPException(status_code=404, detail=f"Item with ID {item.item_id} not found")
                    
                    if item_entity.stock < item.quantity:
                        raise HTTPException(status_code=400, detail=f"Not enough stock for item ID {item.item_id}")
                    
                    item_entity.stock -= item.quantity
                    item_entity.updated_at = datetime.utcnow()
                    item_entity.updated_by = user

            await self.session.commit()
            await self.session.refresh(entity)
            return await self.get_transaction_by_id(entity.id)
         
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    async def get_all_transactions(self) -> List[TransactionResponseDTO]:
            query = (
                select(TransactionEntity)
                .options(
                    selectinload(TransactionEntity.customer).selectinload(CustomerEntity.type), 
                    selectinload(TransactionEntity.tax),
                    selectinload(
                        TransactionEntity.transaction_transaction_items
                    ).selectinload(TransactionItemEntity.item),
                )
                .where(TransactionEntity.deleted_at == null())
            )
            result = await self.session.execute(query)
            entities = result.scalars().all()
            return [TransactionResponseDTO.from_orm(e) for e in entities]

    async def get_dashboard_data(self) -> TransactionDashboardPerDayDTO:
        query = select(
            ConfigurationEntity.attribute,
            ConfigurationEntity.value
        ).where(
            ConfigurationEntity.attribute.in_(["total_per_month", "top_rank"])
        )
        result = await self.session.execute(query)
        configuration_values = dict(result.all())
        months_back = int(configuration_values.get("total_per_month") or 6)
        top_rank = int(configuration_values.get("top_rank") or 5)

        points_result = await self.session.execute(
            select(ConfigurationEntity.value).where(
                ConfigurationEntity.module == "Application",
                ConfigurationEntity.attribute == "points",
                ConfigurationEntity.deleted_at == None,
            )
        )
        points_configurations = points_result.scalars().all()
        if not points_configurations:
            raise HTTPException(
                status_code=500,
                detail="Missing Application.points configuration",
            )
        if len(points_configurations) != 1:
            raise HTTPException(
                status_code=500,
                detail="Multiple Application.points configurations found",
            )
        points_configuration = points_configurations[0]
        if not isinstance(points_configuration, str) or not points_configuration.strip():
            raise HTTPException(
                status_code=500,
                detail="Invalid Application.points configuration",
            )
        point_tiers = self.parse_point_tiers(points_configuration)

        # 1. Find start (Monday) and end (Sunday) of current week
        today = datetime.utcnow().date()
        # Go back to last Monday (6 days ago)
        start_of_week = today - timedelta(days=6)
        end_of_week = datetime.combine(today, datetime.max.time())    # inclusive


        # 2. Query transactions within this week
        query = (
            select(
                func.date(TransactionEntity.created_at).label("day"),
                func.sum(TransactionItemEntity.quantity).label("items_sold"),   # total products sold
                func.sum(TransactionEntity.total).label("sales_total")          # total revenue
            ) 
            .join(TransactionItemEntity, TransactionEntity.id == TransactionItemEntity.transaction_id)
            .where(TransactionEntity.deleted_at == None)
            .where(TransactionEntity.created_at >= start_of_week)
            .where(TransactionEntity.created_at <= end_of_week)
            .group_by(func.date(TransactionEntity.created_at))
            .order_by(func.date(TransactionEntity.created_at))
        )

        result = await self.session.execute(query)
        rows = result.all()

        
        # 3. Build labels and data arrays for each day in the week
        labels = []
        month_labels = []
        month_totals = []
        month_tax = []
        month_credit = []
        month_profits = []
        items_sold = []
        totals = []

        for i in range(7):
            day = start_of_week + timedelta(days=i)
            labels.append(day.strftime("%A"))  # Mon → Sun
            match = next((r for r in rows if r.day == day), None)
            items_sold.append(int(match.items_sold) if match and match.items_sold else 0)
            totals.append(float(match.sales_total) if match and match.sales_total else 0.0)
 
        start_month = self.subtract_months(datetime(today.year, today.month, 1), months_back-1) # e.g. if today is June and months_back=6, start_month will be January 1st
        # First day of next month
        if today.month == 12:
            first_day_next_month = datetime(today.year + 1, 1, 1)
        else:
            first_day_next_month = datetime(today.year, today.month + 1, 1)

        # Last day of current month
        end_month = datetime.combine(first_day_next_month - timedelta(days=1), datetime.max.time()) 

        # Rank credit customers by their transaction totals during the configured period.
        top_credit_query = (
            select(
                CustomerEntity.name.label("customer_name"),
                func.sum(TransactionEntity.total).label("value"),
            )
            .join(CustomerEntity, TransactionEntity.customer_id == CustomerEntity.id)
            .join(EnumTableEntity, CustomerEntity.type_id == EnumTableEntity.id)
            .where(TransactionEntity.deleted_at == None)
            .where(TransactionEntity.created_at >= start_month)
            .where(TransactionEntity.created_at <= end_month)
            .where(EnumTableEntity.name == "Credit")
            .group_by(CustomerEntity.id, CustomerEntity.name)
            .order_by(func.sum(TransactionEntity.total).desc())
            .limit(top_rank)
        )
        top_credit_result = await self.session.execute(top_credit_query)
        top_credit_customers = [
            TopCreditCustomerDTO(
                customer_name=row.customer_name,
                value=row.value if row.value is not None else Decimal("0.00"),
            )
            for row in top_credit_result.all()
        ]

        # Each non-credit transaction earns the highest tier it meets; rank by summed points.
        point_value = case(
            *[
                (TransactionEntity.total > threshold, points)
                for threshold, points in reversed(point_tiers)
            ],
            else_=0,
        )
        top_points_query = (
            select(
                CustomerEntity.name.label("customer_name"),
                func.sum(point_value).label("value"),
            )
            .join(CustomerEntity, TransactionEntity.customer_id == CustomerEntity.id)
            .outerjoin(EnumTableEntity, CustomerEntity.type_id == EnumTableEntity.id)
            .where(TransactionEntity.deleted_at == None)
            .where(TransactionEntity.created_at >= start_month)
            .where(TransactionEntity.created_at <= end_month)
            .where(or_(EnumTableEntity.name != "Credit", EnumTableEntity.name.is_(None)))
            .group_by(CustomerEntity.id, CustomerEntity.name)
            .order_by(func.sum(point_value).desc())
            .limit(top_rank)
        )
        top_points_result = await self.session.execute(top_points_query)
        top_point_customers = [
            TopPointCustomerDTO(customer_name=row.customer_name, value=int(row.value or 0))
            for row in top_points_result.all()
        ]

        monthly_query = (
            select(
                extract("year", TransactionEntity.created_at).label("year"),
                extract("month", TransactionEntity.created_at).label("month"),
                func.sum(TransactionEntity.total).label("sales_total"),
                func.sum(TransactionEntity.tax_value).label("tax_total"),
                func.sum(
                    case(
                        (EnumTableEntity.name == "Credit", TransactionEntity.total),
                        else_=0
                    )
                ).label("credit_total")
            )
            .outerjoin(CustomerEntity, TransactionEntity.customer_id == CustomerEntity.id)
            .outerjoin(EnumTableEntity, CustomerEntity.type_id == EnumTableEntity.id)
            .where(TransactionEntity.deleted_at == None)
            .where(TransactionEntity.created_at >= start_month)
            .where(TransactionEntity.created_at <= end_month)
            .group_by(extract("year", TransactionEntity.created_at), extract("month", TransactionEntity.created_at))
            .order_by(extract("year", TransactionEntity.created_at), extract("month", TransactionEntity.created_at))
        )
        monthly_result = await self.session.execute(monthly_query)
        monthly_rows = monthly_result.all()

        monthly_profit_query = (
            select(
                extract("year", TransactionEntity.created_at).label("year"),
                extract("month", TransactionEntity.created_at).label("month"),
                func.sum(
                    TransactionItemEntity.quantity
                    * (
                        func.coalesce(ItemEntity.selling_price, 0)
                        - func.coalesce(ItemEntity.cost_price, 0)
                    )
                ).label("net_profit")
            )
            .join(TransactionItemEntity, TransactionEntity.id == TransactionItemEntity.transaction_id)
            .join(ItemEntity, ItemEntity.id == TransactionItemEntity.item_id)
            .where(TransactionEntity.deleted_at == None)
            .where(TransactionEntity.created_at >= start_month)
            .where(TransactionEntity.created_at <= end_month)
            .group_by(extract("year", TransactionEntity.created_at), extract("month", TransactionEntity.created_at))
            .order_by(extract("year", TransactionEntity.created_at), extract("month", TransactionEntity.created_at))
        )
        monthly_profit_result = await self.session.execute(monthly_profit_query)
        monthly_profit_rows = monthly_profit_result.all()
        
        cur = start_month
        end = datetime(today.year, today.month, 1) 
        while cur <= end:
            month_labels.append(cur.strftime("%B"))
            match = next(
                (r for r in monthly_rows if int(r.month) == cur.month and int(r.year) == cur.year),
                None
            )
            profit_match = next(
                (r for r in monthly_profit_rows if int(r.month) == cur.month and int(r.year) == cur.year),
                None
            )
            month_totals.append(float(match.sales_total) if match and match.sales_total else 0.0)
            month_tax.append(float(match.tax_total) if match and match.tax_total else 0.0)
            month_credit.append(float(match.credit_total) if match and match.credit_total else 0.0)
            month_profits.append(float(profit_match.net_profit) if profit_match and profit_match.net_profit else 0.0)

            # move to next month
            if cur.month == 12:
                cur = datetime(cur.year + 1, 1, 1)
            else:
                cur = datetime(cur.year, cur.month + 1, 1)

        # 4. Get top products by quantity sold
        top_qty_query = (
            select(
                ItemEntity.id.label("item_id"),
                ItemEntity.name.label("name"),
                ItemEntity.code.label("code"),
                func.sum(TransactionItemEntity.quantity).label("quantity_sold"),
                func.sum(TransactionEntity.total).label("total_revenue"),
                func.sum(
                    TransactionItemEntity.quantity
                    * (
                        func.coalesce(ItemEntity.selling_price, 0)
                        - func.coalesce(ItemEntity.cost_price, 0)
                    )
                ).label("net_profit"),
                func.avg(TransactionItemEntity.price).label("average_price")
            )
            .join(TransactionItemEntity, ItemEntity.id == TransactionItemEntity.item_id)
            .join(TransactionEntity, TransactionEntity.id == TransactionItemEntity.transaction_id)
            .where(TransactionEntity.deleted_at == None)
            .group_by(ItemEntity.id, ItemEntity.name, ItemEntity.code)
            .order_by(func.sum(TransactionItemEntity.quantity).desc())
            .limit(top_rank)
        )
        top_qty_result = await self.session.execute(top_qty_query)
        top_qty_rows = top_qty_result.all()

        # Convert to TopProductDTO
        top_products_by_quantity = []
        for row in top_qty_rows:
            top_products_by_quantity.append(TopProductDTO(
                item_id=row.item_id,
                name=row.name,
                code=row.code,
                quantity_sold=int(row.quantity_sold) if row.quantity_sold else 0,
                total_revenue=float(row.total_revenue) if row.total_revenue else 0.0,
                net_profit=float(row.net_profit) if row.net_profit else 0.0,
                average_price=float(row.average_price) if row.average_price else 0.0
            ))

        # 5. Get top products by revenue
        top_revenue_query = (
            select(
                ItemEntity.id.label("item_id"),
                ItemEntity.name.label("name"),
                ItemEntity.code.label("code"),
                func.sum(TransactionItemEntity.quantity).label("quantity_sold"),
                func.sum(TransactionEntity.total).label("total_revenue"),
                func.sum(
                    TransactionItemEntity.quantity
                    * (
                        func.coalesce(ItemEntity.selling_price, 0)
                        - func.coalesce(ItemEntity.cost_price, 0)
                    )
                ).label("net_profit"),
                func.avg(TransactionItemEntity.price).label("average_price")
            )
            .join(TransactionItemEntity, ItemEntity.id == TransactionItemEntity.item_id)
            .join(TransactionEntity, TransactionEntity.id == TransactionItemEntity.transaction_id)
            .where(TransactionEntity.deleted_at == None)
            .group_by(ItemEntity.id, ItemEntity.name, ItemEntity.code)
            .order_by(func.sum(TransactionEntity.total).desc())
            .limit(top_rank)
        )
        top_revenue_result = await self.session.execute(top_revenue_query)
        top_revenue_rows = top_revenue_result.all()

        # Convert to TopProductDTO
        top_products_by_revenue = []
        for row in top_revenue_rows:
            top_products_by_revenue.append(TopProductDTO(
                item_id=row.item_id,
                name=row.name,
                code=row.code,
                quantity_sold=int(row.quantity_sold) if row.quantity_sold else 0,
                total_revenue=float(row.total_revenue) if row.total_revenue else 0.0,
                net_profit=float(row.net_profit) if row.net_profit else 0.0,
                average_price=float(row.average_price) if row.average_price else 0.0
            ))

            
        return TransactionDashboardPerDayDTO(
            items_sold=items_sold,
            totals=totals,
            labels=labels,
            month_labels=month_labels,
            month_totals=month_totals,
            month_tax=month_tax,
            month_credit=month_credit,
            month_profits=month_profits,
            top_products_by_quantity=top_products_by_quantity,
            top_products_by_revenue=top_products_by_revenue,
            top_credit_customers=top_credit_customers,
            top_point_customers=top_point_customers,
        )

    async def get_paginated_transactions(
            self,
            skip: int,
            limit: int,
            search: Optional[str],
            sort_by: str,
            sort_order: str,
        ) -> PaginationResponseDTO[TransactionResponseDTO]:
            sort_columns = {
                "id": TransactionEntity.id,
                "customer_name": TransactionEntity.customer_name,
                "customer_type": TransactionEntity.customer_type,
                "payment_method": TransactionEntity.payment_method,
                "discount": TransactionEntity.discount,
                "tax_value": TransactionEntity.tax_value,
                "tax_name": TransactionEntity.tax_name,
                "total": TransactionEntity.total,
                "created_at": TransactionEntity.created_at,
            }
            sort_column = sort_columns.get(sort_by)
            if sort_column is None:
                raise HTTPException(status_code=400, detail="Unsupported sort field")

            conditions = [TransactionEntity.deleted_at == null()]
            search_term = search.strip() if search else ""
            if search_term:
                search_pattern = f"%{search_term}%"
                conditions.append(
                    or_(
                        TransactionEntity.customer_name.ilike(search_pattern),
                        TransactionEntity.customer_type.ilike(search_pattern),
                        TransactionEntity.payment_method.ilike(search_pattern),
                        TransactionEntity.discount.ilike(search_pattern),
                        TransactionEntity.tax_value.ilike(search_pattern),
                        TransactionEntity.tax_name.ilike(search_pattern),
                        TransactionEntity.total_amount.ilike(search_pattern),
                    )
                )

            total_result = await self.session.execute(
                select(func.count(TransactionEntity.id)).where(*conditions)
            )
            total = total_result.scalar_one()

            order_expression = (
                sort_column.desc() if sort_order == "desc" else sort_column.asc()
            )
            query = (
                select(TransactionEntity)
                .options(
                    selectinload(TransactionEntity.customer).selectinload(CustomerEntity.type),
                    selectinload(TransactionEntity.tax),
                    selectinload(
                        TransactionEntity.transaction_transaction_items
                    ).selectinload(TransactionItemEntity.item),
                )
                .where(*conditions)
                .order_by(order_expression, TransactionEntity.id.asc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(query)
            entities = result.scalars().all()

            return PaginationResponseDTO[TransactionResponseDTO](
                records=[TransactionResponseDTO.from_orm(entity) for entity in entities],
                total=total,
                skip=skip,
                limit=limit,
            )

    async def get_transaction_by_id(self, transaction_id: int) -> Optional[TransactionResponseDTO]: 
        query = (
            select(TransactionEntity)
            .options(
                selectinload(TransactionEntity.customer).selectinload(CustomerEntity.type),
                selectinload(TransactionEntity.tax),
                selectinload(
                    TransactionEntity.transaction_transaction_items
                ).selectinload(TransactionItemEntity.item),
            )
            .where(
                TransactionEntity.deleted_at == null(),
                TransactionEntity.id == transaction_id,
            )
        )
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return TransactionResponseDTO.from_orm(entity) if entity else None
    
    async def get_last_transaction_by_id(self, user_id: int) -> Optional[TransactionResponseDTO]: 
        query = select(TransactionEntity).where(TransactionEntity.deleted_at == null()).filter(TransactionEntity.user_id == user_id).order_by(TransactionEntity.time.desc())
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return TransactionResponseDTO.from_orm(entity) if entity else None

    async def update_transaction(
        self, transaction_id: int, data: TransactionDTO, user: str = None
    ) -> Optional[TransactionResponseDTO]:
        try:
            # 1. Fetch existing transaction
            entity = await self.session.get(TransactionEntity, transaction_id)
            if not entity:
                raise HTTPException(status_code=404, detail="Transaction not found")

            # 2. Update transaction fields
            entity.customer_id = data.customer_id
            entity.payment_method = data.payment_method
            entity.discount = data.discount
            entity.tax_id = data.tax_id
            entity.tax_value = data.tax_value
            entity.total = data.total
            entity.updated_at = datetime.utcnow()
            entity.updated_by = user

                
            # 3. Sync transaction items
            # Load existing items from DB
            existing_items = await self.session.execute(
                select(TransactionItemEntity).where(TransactionItemEntity.transaction_id == transaction_id)
            )
            existing_items = {i.item_id: i for i in existing_items.scalars().all()}

            # 4.Convert incoming items to dict for quick lookup
            incoming_items = {i.item_id: i for i in (data.items or [])}

            # Collect all item_ids we need to touch (existing + incoming)
            all_item_ids = set(existing_items.keys()) | set(incoming_items.keys()) 
            
            # 5. Fetch all ItemEntity rows in one query
            if all_item_ids:
                result = await self.session.execute(
                    select(ItemEntity).where(ItemEntity.id.in_(all_item_ids))
                )
                item_entities = {i.id: i for i in result.scalars().all()}
            
            # 6. Sync items and adjust stock
            # Case A: db exist & data.item exist → update
            for item_id, db_item in existing_items.items():
                old_qty = db_item.quantity
                if item_id in incoming_items:
                    dto_item = incoming_items[item_id]
                    new_qty = dto_item.quantity
                    qty_diff = new_qty - old_qty

                    # Update transaction item
                    db_item.quantity = new_qty
                    db_item.price = dto_item.price
                    db_item.updated_at = datetime.utcnow()
                    db_item.updated_by = user

                    # Update stock
                    item_entity = item_entities.get(item_id)
                    if not item_entity:
                        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
                    if item_entity.stock < qty_diff and qty_diff > 0:
                        raise HTTPException(status_code=400, detail=f"Not enough stock for {item_entity.name} ({item_entity.code})")
                    item_entity.stock -= qty_diff
                    item_entity.updated_at = datetime.utcnow()
                    item_entity.updated_by = user

                else:
                    # Case B: db exist & data.item not exist → delete 
                    await self.session.delete(db_item)

                    # Return stock
                    item_entity = item_entities.get(item_id)
                    if item_entity:
                        item_entity.stock += old_qty
                        item_entity.updated_at = datetime.utcnow()
                        item_entity.updated_by = user

            # Case C: db not exist & data.item exist → add
            for item_id, dto_item in incoming_items.items():
                if item_id not in existing_items:
                    new_item = TransactionItemEntity(
                        transaction_id=transaction_id,
                        item_id=dto_item.item_id,
                        quantity=dto_item.quantity,
                        price=dto_item.price,
                        created_at=datetime.utcnow(),
                        created_by=user,
                    )
                    self.session.add(new_item)
                    
                    # Update stock
                    item_entity = item_entities.get(item_id)
                    if not item_entity:
                        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found") 
                    # Update stock
                    if item_entity.stock < dto_item.quantity:
                        raise HTTPException(status_code=400, detail=f"Not enough stock for {item_entity.name} ({item_entity.code})")
                    item_entity.stock -= dto_item.quantity
                    item_entity.updated_at = datetime.utcnow()
                    item_entity.updated_by = user 

            # 5. Commit and refresh
            await self.session.commit()
            await self.session.refresh(entity)
            return await self.get_transaction_by_id(entity.id)
     
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    async def delete_soft_transaction(self, transaction_id: int, user: str) -> bool:
        query = select(TransactionEntity).where(TransactionEntity.deleted_at == null()).filter(TransactionEntity.id == transaction_id)
        result = await self.session.execute(query) 
        entity = result.scalars().first()
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = user
        await self.session.commit()
        await self.session.refresh(entity)
        return True
    
    async def delete_transaction(self, transaction_id: int) -> bool:
        result = await self.session.execute(select(TransactionEntity).where(TransactionEntity.id == transaction_id))
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class TransactionService:
    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    async def create_transaction(self, data: TransactionDTO, user: str) -> Optional[TransactionResponseDTO]:
        return await self.repo.create_transaction(data, user=user)

    async def get_all_transactions(self) -> List[TransactionResponseDTO]:
        return await self.repo.get_all_transactions()

    async def get_paginated_transactions(
        self,
        skip: int,
        limit: int,
        search: Optional[str],
        sort_by: str,
        sort_order: str,
    ) -> PaginationResponseDTO[TransactionResponseDTO]:
        return await self.repo.get_paginated_transactions(
            skip, limit, search, sort_by, sort_order
        )

    async def get_dashboard_data(self) -> TransactionDashboardPerDayDTO:
        return await self.repo.get_dashboard_data()

    async def get_transaction_by_id(self, transaction_id: int) -> Optional[TransactionResponseDTO]:
        return await self.repo.get_transaction_by_id(transaction_id)

    async def get_last_transaction_by_id(self, user_id: int) -> Optional[TransactionResponseDTO]:
        return await self.repo.get_last_transaction_by_id(user_id)

    async def update_transaction(self, transaction_id: int, data: TransactionDTO, user: str) -> Optional[TransactionResponseDTO]:
        return await self.repo.update_transaction(transaction_id, data, user)

    async def delete_soft_transaction(self, transaction_id: int, user: str) -> bool:
        return await self.repo.delete_soft_transaction(transaction_id, user)
    
    async def delete_transaction(self, transaction_id: int) -> bool:
        return await self.repo.delete_transaction(transaction_id)