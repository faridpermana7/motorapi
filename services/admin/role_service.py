from datetime import datetime
from sqlalchemy import null
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from model.admin.role_model import RoleEntity, RoleDTO, RoleResponseDTO  # Update path according to your project structure

class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_role(self, data: RoleDTO, created_by: str) -> Optional[RoleResponseDTO]:
        entity = RoleEntity(
            **data.dict(
                exclude={
                    "created_by", 
                    "updated_by", 
                    "created_at", 
                    "updated_at", 
                    "deleted_at"
                }
            )
        )
        entity.created_by = created_by
        entity.created_at = datetime.utcnow()
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return RoleResponseDTO.from_orm(entity)

    async def get_all_roles(self) -> List[RoleResponseDTO]:
        query = select(RoleEntity).where(RoleEntity.deleted_at == null())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [RoleResponseDTO.from_orm(e) for e in entities]

    async def get_role_by_id(self, role_id: int) -> Optional[RoleResponseDTO]:
        query = select(RoleEntity).where(RoleEntity.deleted_at == null(), RoleEntity.id == role_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return RoleResponseDTO.from_orm(entity) if entity else None

    async def update_role(self, role_id: int, data: RoleDTO, updated_by: str) -> Optional[RoleResponseDTO]:
        query = select(RoleEntity).where(RoleEntity.deleted_at == null(), RoleEntity.id == role_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return None
            
        for key, value in data.dict().items():
            setattr(entity, key, value)

        entity.updated_at = datetime.utcnow()
        entity.updated_by = updated_by
        await self.session.commit()
        await self.session.refresh(entity)
        return RoleResponseDTO.from_orm(entity)

    async def delete_soft_role(self, role_id: int, deleted_by: str) -> bool:
        query = select(RoleEntity).where(RoleEntity.deleted_at == null(), RoleEntity.id == role_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return False
            
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = deleted_by
        await self.session.commit()
        await self.session.refresh(entity)
        return True
    
    async def delete_hard_role(self, role_id: int) -> bool:
        query = select(RoleEntity).where(RoleEntity.deleted_at == null(), RoleEntity.id == role_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return False
            
        await self.session.delete(entity)
        await self.session.commit()
        return True


class RoleService:
    def __init__(self, repo: RoleRepository):
        self.repo = repo

    async def create_role(self, data: RoleDTO, created_by: str) -> Optional[RoleResponseDTO]:
        return await self.repo.create_role(data, created_by)

    async def get_all_roles(self) -> List[RoleResponseDTO]:
        return await self.repo.get_all_roles()

    async def get_role_by_id(self, role_id: int) -> Optional[RoleResponseDTO]:
        return await self.repo.get_role_by_id(role_id)

    async def update_role(self, role_id: int, data: RoleDTO, updated_by: str) -> Optional[RoleResponseDTO]:
        return await self.repo.update_role(role_id, data, updated_by)

    async def delete_soft_role(self, role_id: int, deleted_by: str) -> bool:
        return await self.repo.delete_soft_role(role_id, deleted_by)

    async def delete_hard_role(self, role_id: int) -> bool:
        return await self.repo.delete_hard_role(role_id)