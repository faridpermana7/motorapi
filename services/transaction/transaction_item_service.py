from datetime import datetime, timezone

from sqlalchemy import null
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from sqlalchemy.orm import selectinload
from model.master.item_model import ItemEntity
from model.transaction.transaction_item_model import TransactionItemEntity, TransactionItemDTO, TransactionItemResponseDTO
from model.transaction.transaction_model import TransactionEntity


async def check_transaction_exists(session: AsyncSession, transaction_id: int) -> bool:
    result = await session.execute(select(TransactionEntity).where(TransactionEntity.id == transaction_id))
    transaction = result.scalars().first()
    return transaction is not None


async def check_item_exists(session: AsyncSession, item_id: int) -> bool:
    result = await session.execute(select(ItemEntity).where(ItemEntity.id == item_id))
    item = result.scalars().first()
    return item is not None

class TransactionItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_transaction_item(self, data: TransactionItemDTO, user: str = None) -> Optional[TransactionItemResponseDTO]: 
         # 1. Check if transaction exists
        if not await check_transaction_exists(self.session, data.transaction_id):
            return None  # Or raise an exception if you prefer  
        
         # 2. Check if item exists
        if not await check_item_exists(self.session, data.item_id):
            return None  # Or raise an exception if you prefer  
                
        # 3. Create transaction_item entry
        entity = TransactionItemEntity(**data.dict())
        entity.created_at = datetime.utcnow()   
        entity.created_by = user
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        result = await self.session.execute(
            select(TransactionItemEntity).options(selectinload(TransactionItemEntity.transaction), selectinload(TransactionItemEntity.item)).where(TransactionItemEntity.id == entity.id)
        )
        entity = result.scalars().first()
        return TransactionItemResponseDTO.from_orm(entity) if entity else None
    
    async def get_all_transaction_items(self) -> List[TransactionItemResponseDTO]:
        query = select(TransactionItemEntity).options(selectinload(TransactionItemEntity.transaction), selectinload(TransactionItemEntity.item)).where(TransactionItemEntity.deleted_at == null())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [TransactionItemResponseDTO.from_orm(e) for e in entities]

    async def get_transaction_item_by_transaction_id(self, transaction_id: int) -> Optional[TransactionItemResponseDTO]: 
        query = select(TransactionItemEntity).options(selectinload(TransactionItemEntity.transaction), 
                                                      selectinload(TransactionItemEntity.item)
                                                      ).where(TransactionItemEntity.deleted_at == null()
                                                              ).where(TransactionItemEntity.transaction_id == transaction_id)
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [TransactionItemResponseDTO.from_orm(e) for e in entities]

    async def update_transaction_item(self, transaction_item_id: int, data: TransactionItemDTO, user: str) -> Optional[TransactionItemResponseDTO]:
        
         # 1. Check if transaction exists
        if not await check_transaction_exists(self.session, data.transaction_id):
            return None  # Or raise an exception if you prefer  
        
         # 2. Check if item exists
        if not await check_item_exists(self.session, data.item_id):
            return None  # Or raise an exception if you prefer  
        
        query = select(TransactionItemEntity).options(selectinload(TransactionItemEntity.transaction), selectinload(TransactionItemEntity.item)).where(TransactionItemEntity.deleted_at == null()).filter(TransactionItemEntity.id == transaction_item_id)
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
            select(TransactionItemEntity).options(selectinload(TransactionItemEntity.transaction), selectinload(TransactionItemEntity.item)).where(TransactionItemEntity.id == entity.id)
        )
        entity = result.scalars().first()
        return TransactionItemResponseDTO.from_orm(entity) if entity else None

    async def delete_soft_transaction_item(self, transaction_item_id: int, user: str) -> bool:
        query = select(TransactionItemEntity).where(TransactionItemEntity.deleted_at == null()).filter(TransactionItemEntity.id == transaction_item_id)
        result = await self.session.execute(query) 
        entity = result.scalars().first()
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = user
        await self.session.commit()
        await self.session.refresh(entity)
        return True
    

    async def delete_transaction_item(self, transaction_item_id: int) -> bool:
        result = await self.session.execute(select(TransactionItemEntity).where(TransactionItemEntity.id == transaction_item_id))
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class TransactionItemService:
    def __init__(self, repo: TransactionItemRepository):
        self.repo = repo

    async def create_transaction_item(self, data: TransactionItemDTO, user: str) -> Optional[TransactionItemResponseDTO]:
        return await self.repo.create_transaction_item(data, user=user)

    async def get_all_transaction_items(self) -> List[TransactionItemResponseDTO]:
        return await self.repo.get_all_transaction_items()

    async def get_transaction_item_by_transaction_id(self, transaction_id: int) -> Optional[TransactionItemResponseDTO]:
        return await self.repo.get_transaction_item_by_transaction_id(transaction_id)

    async def update_transaction_item(self, transaction_item_id: int, data: TransactionItemDTO, user: str) -> Optional[TransactionItemResponseDTO]:
        return await self.repo.update_transaction_item(transaction_item_id, data, user)

    async def delete_soft_transaction_item(self, transaction_item_id: int, user: str) -> bool:
        return await self.repo.delete_soft_transaction_item(transaction_item_id, user)
    
    async def delete_transaction_item(self, transaction_item_id: int) -> bool:
        return await self.repo.delete_transaction_item(transaction_item_id)