from datetime import datetime, timezone
from fastapi import HTTPException

from sqlalchemy import func, null
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from sqlalchemy.orm import selectinload
from model.master.item_model import ItemEntity, ItemDTO, ItemImportDTO, ItemResponseDTO
from model.master.enum_table_model import EnumTableEntity, EnumTableResponseDTO


async def check_enum_exists(session: AsyncSession, enum_id: int) -> bool:
    result = await session.execute(select(EnumTableEntity).where(EnumTableEntity.id == enum_id))
    enum = result.scalars().first()
    return enum is not None

class ItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_item(self, data: ItemDTO, user: str = None) -> Optional[ItemResponseDTO]: 
        
        try:
                    
            # 1. Check if uom exists
            if not await check_enum_exists(self.session, data.uom_id):
                return None  # Or raise an exception if you prefer  
            
            # 2. Check if category exists
            if not await check_enum_exists(self.session, data.category_id):
                return None  # Or raise an exception if you prefer  
            
            # 3. Generate Item Code based on category
            category = await self.get_category_id(data.category_id)
            category_code = category.type[:3].upper() if category else "COD"
            date_code = datetime.utcnow().strftime("%Y%m%d")
            timestamp_code = datetime.utcnow().strftime("%H%M%S")
            data.code = f"{category_code}-{date_code}-{timestamp_code}"
                    
            # 4. Create item entry  
            entity = ItemEntity(
                uom_id=data.uom_id,
                category_id=data.category_id,
                name=data.name,
                code=data.code,
                barcode=data.barcode if data.barcode else f"BAR-{data.code}",  # Use generated code as fallback if barcode is not provided
                brand=data.brand,
                description=data.description,
                minimum_stock=data.minimum_stock,
                stock=data.stock,
                cost_price=data.cost_price,
                selling_price=data.selling_price,
                created_at=datetime.utcnow(),
                created_by=user,
            )
            entity.created_at = datetime.utcnow()   
            entity.created_by = user
            self.session.add(entity)
            await self.session.commit()
            await self.session.refresh(entity)
            result = await self.session.execute(
                select(ItemEntity).options(selectinload(ItemEntity.uom), selectinload(ItemEntity.category)).where(ItemEntity.id == entity.id)
            )
            entity = result.scalars().first()
            return ItemResponseDTO.from_orm(entity) if entity else None
         
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    async def bulk_import_items(self, items: list[ItemImportDTO], user: str = None):
        try:
            now = datetime.utcnow()
            enum_cache = {}
            imported_count = 0

            for index, data in enumerate(items, start=1):
                required_fields = {
                    "UOM": data.uom_name,
                    "category": data.category_name,
                    "name": data.name,
                    "brand": data.brand,
                }
                for field_name, value in required_fields.items():
                    if not isinstance(value, str) or not value.strip():
                        raise HTTPException(
                            status_code=400,
                            detail=f"Row {index}: {field_name} is required",
                        )

                uom_name = data.uom_name.strip()
                category_name = data.category_name.strip()
                name = data.name.strip()

                uom_key = ("UOM", uom_name.casefold())
                category_key = ("ItemCategory", category_name.casefold())
                if uom_key not in enum_cache:
                    enum_cache[uom_key] = await self._get_or_create_import_enum(
                        "UOM", uom_name, user
                    )
                if category_key not in enum_cache:
                    enum_cache[category_key] = await self._get_or_create_import_enum(
                        "ItemCategory", category_name, user
                    )

                uom = enum_cache[uom_key]
                category = enum_cache[category_key]
                category_code = category.type[:3].upper() if category else "COD"
                generated_code = f"{category_code}-{now:%Y%m%d-%H%M%S}-{index:03d}"
                provided_code = data.code.strip() if data.code and data.code.strip() else None
                provided_barcode = (
                    data.barcode.strip()
                    if data.barcode and data.barcode.strip()
                    else None
                )
                entity = await self._find_import_item(
                    barcode=provided_barcode,
                    name=name,
                    category_id=category.id,
                )

                if entity:
                    entity.uom_id = uom.id
                    entity.category_id = category.id
                    entity.name = name
                    if provided_code:
                        entity.code = provided_code
                    if provided_barcode:
                        entity.barcode = provided_barcode
                    entity.brand = data.brand
                    entity.description = data.description
                    entity.minimum_stock = data.minimum_stock
                    entity.stock = data.stock
                    entity.cost_price = data.cost_price
                    entity.selling_price = data.selling_price
                    entity.updated_at = now
                    entity.updated_by = user
                else:
                    entity = ItemEntity(
                        uom_id=uom.id,
                        category_id=category.id,
                        name=name,
                        code=provided_code or generated_code,
                        barcode=provided_barcode or f"BAR-{provided_code or generated_code}",
                        brand=data.brand,
                        description=data.description,
                        minimum_stock=data.minimum_stock,
                        stock=data.stock,
                        cost_price=data.cost_price,
                        selling_price=data.selling_price,
                        created_at=now,
                        created_by=user,
                    )
                    self.session.add(entity)

                await self.session.flush()
                imported_count += 1

            await self.session.commit()

            return {"status": "success", "count": imported_count}

        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")  

    async def _find_import_item(
        self, barcode: Optional[str], name: str, category_id: int
    ) -> Optional[ItemEntity]:
        active_item = ItemEntity.deleted_at == null()

        if barcode:
            result = await self.session.execute(
                select(ItemEntity).where(
                    active_item,
                    func.lower(func.trim(ItemEntity.barcode)) == barcode.casefold(),
                )
            )
            entity = result.scalars().first()
            if entity:
                return entity

        result = await self.session.execute(
            select(ItemEntity).where(
                active_item,
                ItemEntity.category_id == category_id,
                func.lower(func.trim(ItemEntity.name)) == name.casefold(),
            )
        )
        return result.scalars().first()

    async def _get_or_create_import_enum(self, enum_type: str, name: str, user: str):
        result = await self.session.execute(
            select(EnumTableEntity).where(
                EnumTableEntity.type == enum_type,
                func.lower(func.trim(EnumTableEntity.name)) == name.casefold(),
                EnumTableEntity.deleted_at == null(),
            )
        )
        entity = result.scalars().first()
        if entity:
            return entity

        entity = EnumTableEntity(
            type=enum_type,
            name=name,
            description=f"Auto-created {enum_type} for import",
            created_at=datetime.utcnow(),
            created_by=user,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_all_items(self) -> List[ItemResponseDTO]:
        query = select(ItemEntity).options(selectinload(ItemEntity.uom), selectinload(ItemEntity.category)).where(ItemEntity.deleted_at == null())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [ItemResponseDTO.from_orm(e) for e in entities]
    
    
    async def get_category_id(self, category_id: int) -> Optional[EnumTableResponseDTO]: 
        query = select(EnumTableEntity).where(EnumTableEntity.id == category_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return EnumTableResponseDTO.from_orm(entity) if entity else None

    async def get_item_by_id(self, item_id: int) -> Optional[ItemResponseDTO]: 
        query = select(ItemEntity).options(selectinload(ItemEntity.uom), selectinload(ItemEntity.category)).where(ItemEntity.deleted_at == null()).filter(ItemEntity.id == item_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return ItemResponseDTO.from_orm(entity) if entity else None
    

    async def get_last_item_by_id(self, user_id: int) -> Optional[ItemResponseDTO]: 
        query = select(ItemEntity).options(selectinload(ItemEntity.uom), selectinload(ItemEntity.category)).where(ItemEntity.deleted_at == null()).filter(ItemEntity.user_id == user_id).order_by(ItemEntity.time.desc())
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return ItemResponseDTO.from_orm(entity) if entity else None

    async def update_item(self, item_id: int, data: ItemDTO, user: str) -> Optional[ItemResponseDTO]:
        
         # 1. Check if uom exists
        if not await check_enum_exists(self.session, data.uom_id):
            return None  # Or raise an exception if you prefer  
        
         # 2. Check if category exists
        if not await check_enum_exists(self.session, data.category_id):
            return None  # Or raise an exception if you prefer  
        
        query = select(ItemEntity).options(selectinload(ItemEntity.uom), selectinload(ItemEntity.category)).where(ItemEntity.deleted_at == null()).filter(ItemEntity.id == item_id)
        result = await self.session.execute(query)
        entity = result.scalars().first() 

        if not entity:
            return None
        for key, value in data.dict().items():
            setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()   
        entity.updated_by = user
        await self.session.commit()
        await self.session.refresh(entity)
        result = await self.session.execute(
            select(ItemEntity).options(selectinload(ItemEntity.uom), selectinload(ItemEntity.category)).where(ItemEntity.id == entity.id)
        )
        entity = result.scalars().first()
        return ItemResponseDTO.from_orm(entity) if entity else None

    async def delete_soft_item(self, item_id: int, user: str) -> bool:
        query = select(ItemEntity).where(ItemEntity.deleted_at == null()).filter(ItemEntity.id == item_id)
        result = await self.session.execute(query) 
        entity = result.scalars().first()
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = user
        await self.session.commit()
        await self.session.refresh(entity)
        return True
    

    async def delete_item(self, item_id: int) -> bool:
        result = await self.session.execute(select(ItemEntity).where(ItemEntity.id == item_id))
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class ItemService:
    def __init__(self, repo: ItemRepository):
        self.repo = repo

    async def create_item(self, data: ItemDTO, user: str) -> Optional[ItemResponseDTO]:
        return await self.repo.create_item(data, user=user)
    
    async def bulk_import_items(self, data: list[ItemImportDTO], user: str) -> Optional[ItemResponseDTO]:
        return await self.repo.bulk_import_items(data, user=user)

    async def get_all_items(self) -> List[ItemResponseDTO]:
        return await self.repo.get_all_items()

    async def get_item_by_id(self, item_id: int) -> Optional[ItemResponseDTO]:
        return await self.repo.get_item_by_id(item_id) 

    async def get_last_item_by_id(self, user_id: int) -> Optional[ItemResponseDTO]:
        return await self.repo.get_last_item_by_id(user_id)

    async def update_item(self, item_id: int, data: ItemDTO, user: str) -> Optional[ItemResponseDTO]:
        return await self.repo.update_item(item_id, data, user)

    async def delete_soft_item(self, item_id: int, user: str) -> bool:
        return await self.repo.delete_soft_item(item_id, user)
    
    async def delete_item(self, item_id: int) -> bool:
        return await self.repo.delete_item(item_id)