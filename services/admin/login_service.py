from datetime import datetime, timezone

from sqlalchemy import null
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from sqlalchemy.orm import selectinload
from model.admin.login_model import LoginEntity, LoginDTO, LoginResponseDTO
from model.admin.user_model import UserEntity


async def check_user_exists(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(select(UserEntity).where(UserEntity.id == user_id))
    user = result.scalars().first()
    return user is not None 


def _normalize_datetime_to_utc(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

class LoginRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_login(self, data: LoginDTO, user: str = None) -> Optional[LoginResponseDTO]: 
         # 1. Check if user exists
        if not await check_user_exists(self.session, data.user_id):
            return None  # Or raise an exception if you prefer  
                
        # 2. Create login entry
        entity = LoginEntity(**data.dict())
        entity.time = _normalize_datetime_to_utc(entity.time)
        entity.created_at = datetime.utcnow()   
        entity.created_by = user
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        result = await self.session.execute(
            select(LoginEntity).options(selectinload(LoginEntity.user)).where(LoginEntity.id == entity.id)
        )
        entity = result.scalars().first()
        return LoginResponseDTO.from_orm(entity) if entity else None

    # async def get_all_logins(self) -> List[LoginResponseDTO]:
    #     result = await self.session.execute(select(LoginEntity))
    #     entities = result.scalars().all()
    #     return [LoginResponseDTO.from_orm(e) for e in entities]
    
    async def get_all_logins(self) -> List[LoginResponseDTO]:
        query = select(LoginEntity).options(selectinload(LoginEntity.user)).where(LoginEntity.deleted_at == null())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [LoginResponseDTO.from_orm(e) for e in entities]

    async def get_login_by_id(self, login_id: int) -> Optional[LoginResponseDTO]: 
        query = select(LoginEntity).options(selectinload(LoginEntity.user)).where(LoginEntity.deleted_at == null()).filter(LoginEntity.id == login_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return LoginResponseDTO.from_orm(entity) if entity else None
    

    async def get_last_login_by_id(self, user_id: int) -> Optional[LoginResponseDTO]: 
        query = select(LoginEntity).options(selectinload(LoginEntity.user)).where(LoginEntity.deleted_at == null()).filter(LoginEntity.user_id == user_id).order_by(LoginEntity.time.desc())
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return LoginResponseDTO.from_orm(entity) if entity else None

    async def update_login(self, login_id: int, data: LoginDTO, updated_by: str) -> Optional[LoginResponseDTO]:
         # 1. Check if user exists
        if not await check_user_exists(self.session, data.user_id):
            return None  # Or raise an exception if you prefer  
        query = select(LoginEntity).options(selectinload(LoginEntity.user)).where(LoginEntity.deleted_at == null()).filter(LoginEntity.id == login_id)
        result = await self.session.execute(query)
        entity = result.scalars().first() 

        if not entity:
            return None
        for key, value in data.dict().items():
            if isinstance(value, datetime):
                value = _normalize_datetime_to_utc(value)
            setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()   
        entity.updated_by = updated_by
        await self.session.commit()
        await self.session.refresh(entity)
        result = await self.session.execute(
            select(LoginEntity).options(selectinload(LoginEntity.user)).where(LoginEntity.id == entity.id)
        )
        entity = result.scalars().first()
        return LoginResponseDTO.from_orm(entity) if entity else None

    async def delete_soft_login(self, login_id: int, deleted_by: str) -> bool:
        query = select(LoginEntity).where(LoginEntity.deleted_at == null()).filter(LoginEntity.id == login_id)
        result = await self.session.execute(query) 
        entity = result.scalars().first()
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = deleted_by
        await self.session.commit()
        await self.session.refresh(entity)
        return True
    

    async def delete_login(self, login_id: int) -> bool:
        result = await self.session.execute(select(LoginEntity).where(LoginEntity.id == login_id))
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class LoginService:
    def __init__(self, repo: LoginRepository):
        self.repo = repo

    async def create_login(self, data: LoginDTO, user: str) -> Optional[LoginResponseDTO]:
        return await self.repo.create_login(data, user=user)

    async def get_all_logins(self) -> List[LoginResponseDTO]:
        return await self.repo.get_all_logins()

    async def get_login_by_id(self, login_id: int) -> Optional[LoginResponseDTO]:
        return await self.repo.get_login_by_id(login_id)

    async def get_last_login_by_id(self, user_id: int) -> Optional[LoginResponseDTO]:
        return await self.repo.get_last_login_by_id(user_id)

    async def update_login(self, login_id: int, data: LoginDTO, updated_by: str) -> Optional[LoginResponseDTO]:
        return await self.repo.update_login(login_id, data, updated_by=updated_by)

    async def delete_soft_login(self, login_id: int, deleted_by: str) -> bool:
        return await self.repo.delete_soft_login(login_id, deleted_by)
    
    async def delete_login(self, login_id: int) -> bool:
        return await self.repo.delete_login(login_id)