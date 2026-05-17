from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import null 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from sqlalchemy.orm import selectinload
from model.master.item_model import ItemEntity
from model.transaction.transaction_item_model import TransactionItemEntity
from model.transaction.transaction_model import TransactionEntity, TransactionDTO, TransactionResponseDTO 

class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

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
        query = select(TransactionEntity).options(selectinload(TransactionEntity.customer), 
                                                  selectinload(TransactionEntity.tax)
                                                  ).where(TransactionEntity.deleted_at == null())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [TransactionResponseDTO.from_orm(e) for e in entities]

    async def get_transaction_by_id(self, transaction_id: int) -> Optional[TransactionResponseDTO]: 
        query = select(TransactionEntity).options(selectinload(TransactionEntity.customer), 
                                                  selectinload(TransactionEntity.tax)
                                                  ).where(TransactionEntity.deleted_at == null()
                                                          ).filter(TransactionEntity.id == transaction_id)
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