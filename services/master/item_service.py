from datetime import datetime, timezone
from http.client import HTTPException

from sqlalchemy import insert, null
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
            # Preprocess rows into dicts
            entities_data = []
            now = datetime.utcnow()

            i=1
            for data in items:
                # 1. Validate enums
                if not await check_enum_exists(self.session, data.uom_id):
                    continue
                if not await check_enum_exists(self.session, data.category_id):
                    continue

                # 2. Generate code
                category = await self.get_category_id(data.category_id)
                category_code = category.type[:3].upper() if category else "COD"
                date_code = now.strftime("%Y%m%d")
                timestamp_code = now.strftime("%H%M%S")
                code = f"{category_code}-{date_code}-{timestamp_code}-{i:03d}"  # Add sequence number to ensure uniqueness
                i += 1

                # 3. Prepare dict for bulk insert
                entities_data.append({
                    "uom_id": data.uom_id,
                    "category_id": data.category_id,
                    "name": data.name,
                    "code": code,
                    "barcode": data.barcode if data.barcode else f"BAR-{code}",
                    "brand": data.brand,
                    "description": data.description,
                    "minimum_stock": data.minimum_stock,
                    "stock": data.stock,
                    "cost_price": data.cost_price,
                    "selling_price": data.selling_price,
                    "created_at": now,
                    "created_by": user,
                })

            # 🔹 Bulk insert in one query
            if entities_data:
                stmt = insert(ItemEntity).values(entities_data)
                await self.session.execute(stmt)
                await self.session.commit()

            return {"status": "success", "count": len(entities_data)}

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")  

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