from datetime import datetime, timezone

from sqlalchemy import null
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from sqlalchemy.orm import selectinload
from model.master.item_model import ItemEntity, ItemDTO, ItemResponseDTO
from model.master.enum_table_model import EnumTableEntity


async def check_enum_exists(session: AsyncSession, enum_id: int) -> bool:
    result = await session.execute(select(EnumTableEntity).where(EnumTableEntity.id == enum_id))
    enum = result.scalars().first()
    return enum is not None


def _normalize_datetime_to_utc(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

class ItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_item(self, data: ItemDTO, user: str = None) -> Optional[ItemResponseDTO]: 
         # 1. Check if uom exists
        if not await check_enum_exists(self.session, data.uom_id):
            return None  # Or raise an exception if you prefer  
        
         # 2. Check if category exists
        if not await check_enum_exists(self.session, data.category_id):
            return None  # Or raise an exception if you prefer  
                
        # 3. Create item entry
        entity = ItemEntity(**data.dict())
        entity.time = _normalize_datetime_to_utc(entity.time)
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
    
    async def get_all_items(self) -> List[ItemResponseDTO]:
        query = select(ItemEntity).options(selectinload(ItemEntity.uom), selectinload(ItemEntity.category)).where(ItemEntity.deleted_at == null())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [ItemResponseDTO.from_orm(e) for e in entities]

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
            if isinstance(value, datetime):
                value = _normalize_datetime_to_utc(value)
            setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()   
        entity.updated_by = user
        await self.session.commit()
        await self.session.refresh(entity)
        result = await self.session.execute(
            select(ItemEntity).options(selectinload(ItemEntity.user)).where(ItemEntity.id == entity.id)
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

    async def get_all_items(self) -> List[ItemResponseDTO]:
        return await self.repo.get_all_items()

    async def get_item_by_id(self, item_id: int) -> Optional[ItemResponseDTO]:
        return await self.repo.get_item_by_id(item_id)

    async def get_last_item_by_id(self, user_id: int) -> Optional[ItemResponseDTO]:
        return await self.repo.get_last_item_by_id(user_id)

    async def update_item(self, item_id: int, data: ItemDTO, user: str) -> Optional[ItemResponseDTO]:
        return await self.repo.update_item(item_id, data, user=user)

    async def delete_soft_item(self, item_id: int, user: str) -> bool:
        return await self.repo.delete_soft_item(item_id, user)
    
    async def delete_item(self, item_id: int) -> bool:
        return await self.repo.delete_item(item_id)