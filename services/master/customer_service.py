from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from model.master.customer_model import CustomerEntity, CustomerDTO, CustomerResponseDTO  

class CustomerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_customers(self) -> List[CustomerResponseDTO]:
        query = select(CustomerEntity).where(CustomerEntity.deleted_at == None)
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [CustomerResponseDTO.from_orm(e) for e in entities]

    async def get_customer_by_id(self, customer_id: int) -> Optional[CustomerResponseDTO]:
        query = select(CustomerEntity).where(CustomerEntity.deleted_at == None).where(CustomerEntity.id == customer_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return CustomerResponseDTO.from_orm(entity) if entity else None

    async def create_customer(self, data: CustomerDTO, user: str) -> Optional[CustomerResponseDTO]:
        entity = CustomerEntity(**data.dict())
        entity.created_at = datetime.utcnow()
        entity.created_by = user
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return CustomerResponseDTO.from_orm(entity)
    
    async def update_customer(self, customer_id: int, data: CustomerDTO, user: str) -> Optional[CustomerResponseDTO]:
        query = select(CustomerEntity).where(CustomerEntity.deleted_at == None).where(CustomerEntity.id == customer_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return None
        for key, value in data.dict().items():
            setattr(entity, key, value)

        entity.updated_by = user
        entity.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(entity)
        return CustomerResponseDTO.from_orm(entity)

    async def delete_soft_customer(self, customer_id: int, user: str) -> bool:
        query = select(CustomerEntity).where(CustomerEntity.deleted_at == None).where(CustomerEntity.id == customer_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = user
        await self.session.commit()
        await self.session.refresh(entity)
        return True

    async def delete_customer(self, customer_id: int) -> bool:
        result = await self.session.execute(select(CustomerEntity).where(CustomerEntity.id == customer_id))
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class CustomerService:
    def __init__(self, repo: CustomerRepository):
        self.repo = repo

    async def create_customer(self, data: CustomerDTO, user: str) -> Optional[CustomerResponseDTO]:
        return await self.repo.create_customer(data, user)

    async def get_all_customers(self) -> List[CustomerResponseDTO]:
        return await self.repo.get_all_customers()

    async def get_customer_by_id(self, customer_id: int) -> Optional[CustomerResponseDTO]:
        return await self.repo.get_customer_by_id(customer_id)

    async def update_customer(self, customer_id: int, data: CustomerDTO,  user: str) -> Optional[CustomerResponseDTO]:
        return await self.repo.update_customer(customer_id, data, user)

    async def delete_soft_customer(self, customer_id: int, user: str) -> bool:
        return await self.repo.delete_soft_customer(customer_id, user)

    async def delete_customer(self, customer_id: int) -> bool:
        return await self.repo.delete_customer(customer_id)