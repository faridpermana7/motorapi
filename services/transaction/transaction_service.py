from datetime import datetime, timezone

from sqlalchemy import null
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from sqlalchemy.orm import selectinload
from model.transaction.transaction_model import TransactionEntity, TransactionDTO, TransactionResponseDTO
from model.master.enum_table_model import EnumTableEntity

class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_transaction(self, data: TransactionDTO, user: str = None) -> Optional[TransactionResponseDTO]:           
        # 1. Create transaction entry
        entity = TransactionEntity(**data.dict())
        entity.created_at = datetime.utcnow()   
        entity.created_by = user
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity) 
        return TransactionResponseDTO.from_orm(entity) if entity else None
    
    async def get_all_transactions(self) -> List[TransactionResponseDTO]:
        query = select(TransactionEntity).where(TransactionEntity.deleted_at == null())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [TransactionResponseDTO.from_orm(e) for e in entities]

    async def get_transaction_by_id(self, transaction_id: int) -> Optional[TransactionResponseDTO]: 
        query = select(TransactionEntity).where(TransactionEntity.deleted_at == null()).filter(TransactionEntity.id == transaction_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return TransactionResponseDTO.from_orm(entity) if entity else None
    

    async def get_last_transaction_by_id(self, user_id: int) -> Optional[TransactionResponseDTO]: 
        query = select(TransactionEntity).where(TransactionEntity.deleted_at == null()).filter(TransactionEntity.user_id == user_id).order_by(TransactionEntity.time.desc())
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return TransactionResponseDTO.from_orm(entity) if entity else None

    async def update_transaction(self, transaction_id: int, data: TransactionDTO, user: str) -> Optional[TransactionResponseDTO]:
        
        query = select(TransactionEntity).where(TransactionEntity.deleted_at == null()).filter(TransactionEntity.id == transaction_id)
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