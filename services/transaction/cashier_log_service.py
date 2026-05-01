from datetime import datetime, timezone

from sqlalchemy import null
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from sqlalchemy.orm import selectinload
from model.transaction.cashier_log_model import CashierLogEntity, CashierLogDTO, CashierLogResponseDTO
from model.transaction.transaction_model import TransactionEntity


async def check_transaction_exists(session: AsyncSession, transaction_id: int) -> bool:
    result = await session.execute(select(TransactionEntity).where(TransactionEntity.id == transaction_id))
    transaction = result.scalars().first()
    return transaction is not None

class CashierLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_cashier_log(self, data: CashierLogDTO, user: str = None) -> Optional[CashierLogResponseDTO]: 
         # 1. Check if transaction exists
        if not await check_transaction_exists(self.session, data.transaction_id):
            return None  # Or raise an exception if you prefer  
                
        # 2. Create cashier_log entry
        entity = CashierLogEntity(**data.dict())
        entity.created_at = datetime.utcnow()   
        entity.created_by = user
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        result = await self.session.execute(
            select(CashierLogEntity).options(selectinload(CashierLogEntity.transaction)).where(CashierLogEntity.id == entity.id)
        )
        entity = result.scalars().first()
        return CashierLogResponseDTO.from_orm(entity) if entity else None
    
    async def get_all_cashier_logs(self) -> List[CashierLogResponseDTO]:
        query = select(CashierLogEntity).options(selectinload(CashierLogEntity.transaction)).where(CashierLogEntity.deleted_at == null())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [CashierLogResponseDTO.from_orm(e) for e in entities]

    async def get_cashier_log_by_id(self, cashier_log_id: int) -> Optional[CashierLogResponseDTO]: 
        query = select(CashierLogEntity).options(selectinload(CashierLogEntity.transaction)).where(CashierLogEntity.deleted_at == null())
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return CashierLogResponseDTO.from_orm(entity) if entity else None

    async def update_cashier_log(self, cashier_log_id: int, data: CashierLogDTO, user: str) -> Optional[CashierLogResponseDTO]:
        
         # 1. Check if transaction exists
        if not await check_transaction_exists(self.session, data.transaction_id):
            return None  # Or raise an exception if you prefer  
        
        query = select(CashierLogEntity).options(selectinload(CashierLogEntity.transaction)).where(CashierLogEntity.deleted_at == null()).filter(CashierLogEntity.id == cashier_log_id)
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
            select(CashierLogEntity).options(selectinload(CashierLogEntity.transaction)).where(CashierLogEntity.id == entity.id)
        )
        entity = result.scalars().first()
        return CashierLogResponseDTO.from_orm(entity) if entity else None

    async def delete_soft_cashier_log(self, cashier_log_id: int, user: str) -> bool:
        query = select(CashierLogEntity).where(CashierLogEntity.deleted_at == null()).filter(CashierLogEntity.id == cashier_log_id)
        result = await self.session.execute(query) 
        entity = result.scalars().first()
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = user
        await self.session.commit()
        await self.session.refresh(entity)
        return True
    

    async def delete_cashier_log(self, cashier_log_id: int) -> bool:
        result = await self.session.execute(select(CashierLogEntity).where(CashierLogEntity.id == cashier_log_id))
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class CashierLogService:
    def __init__(self, repo: CashierLogRepository):
        self.repo = repo

    async def create_cashier_log(self, data: CashierLogDTO, user: str) -> Optional[CashierLogResponseDTO]:
        return await self.repo.create_cashier_log(data, user=user)

    async def get_all_cashier_logs(self) -> List[CashierLogResponseDTO]:
        return await self.repo.get_all_cashier_logs()

    async def get_cashier_log_by_id(self, cashier_log_id: int) -> Optional[CashierLogResponseDTO]:
        return await self.repo.get_cashier_log_by_id(cashier_log_id)

    async def update_cashier_log(self, cashier_log_id: int, data: CashierLogDTO, user: str) -> Optional[CashierLogResponseDTO]:
        return await self.repo.update_cashier_log(cashier_log_id, data, user)

    async def delete_soft_cashier_log(self, cashier_log_id: int, user: str) -> bool:
        return await self.repo.delete_soft_cashier_log(cashier_log_id, user)
    
    async def delete_cashier_log(self, cashier_log_id: int) -> bool:
        return await self.repo.delete_cashier_log(cashier_log_id)