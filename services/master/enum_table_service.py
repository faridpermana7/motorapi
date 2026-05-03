from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from model.master.enum_table_model import EnumTableEntity, EnumTableDTO, EnumTableResponseDTO  

class EnumTableRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_enum_tables(self) -> List[EnumTableResponseDTO]:
        query = select(EnumTableEntity).where(EnumTableEntity.deleted_at == None)
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [EnumTableResponseDTO.from_orm(e) for e in entities]

    async def get_enum_table_by_id(self, enum_table_id: int) -> Optional[EnumTableResponseDTO]:
        query = select(EnumTableEntity).where(EnumTableEntity.deleted_at == None).where(EnumTableEntity.id == enum_table_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return EnumTableResponseDTO.from_orm(entity) if entity else None

    async def create_enum_table(self, data: EnumTableDTO, user: str) -> Optional[EnumTableResponseDTO]:
        entity = EnumTableEntity(**data.dict())
        entity.created_at = datetime.utcnow()
        entity.created_by = user
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return EnumTableResponseDTO.from_orm(entity)
    
    async def update_enum_table(self, enum_table_id: int, data: EnumTableDTO, user: str) -> Optional[EnumTableResponseDTO]:
        query = select(EnumTableEntity).where(EnumTableEntity.deleted_at == None).where(EnumTableEntity.id == enum_table_id)
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
        return EnumTableResponseDTO.from_orm(entity)

    async def delete_soft_enum_table(self, enum_table_id: int, user: str) -> bool:
        query = select(EnumTableEntity).where(EnumTableEntity.deleted_at == None).where(EnumTableEntity.id == enum_table_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = user
        await self.session.commit()
        await self.session.refresh(entity)
        return True

    async def delete_enum_table(self, enum_table_id: int) -> bool:
        result = await self.session.execute(select(EnumTableEntity).where(EnumTableEntity.id == enum_table_id))
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class EnumTableService:
    def __init__(self, repo: EnumTableRepository):
        self.repo = repo

    async def create_enum_table(self, data: EnumTableDTO, user: str) -> Optional[EnumTableResponseDTO]:
        return await self.repo.create_enum_table(data, user)

    async def get_all_enum_tables(self) -> List[EnumTableResponseDTO]:
        return await self.repo.get_all_enum_tables()

    async def get_enum_table_by_id(self, enum_table_id: int) -> Optional[EnumTableResponseDTO]:
        return await self.repo.get_enum_table_by_id(enum_table_id)

    async def update_enum_table(self, enum_table_id: int, data: EnumTableDTO,  user: str) -> Optional[EnumTableResponseDTO]:
        return await self.repo.update_enum_table(enum_table_id, data, user)

    async def delete_soft_enum_table(self, enum_table_id: int, user: str) -> bool:
        return await self.repo.delete_soft_enum_table(enum_table_id, user)

    async def delete_enum_table(self, enum_table_id: int) -> bool:
        return await self.repo.delete_enum_table(enum_table_id)