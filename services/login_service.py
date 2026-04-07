from datetime import datetime

from sqlalchemy import null
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from model.login_model import LoginEntity, LoginDTO, LoginResponseDTO
from model.user_model import UserEntity


async def check_user_exists(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(select(UserEntity).where(UserEntity.id == user_id))
    user = result.scalars().first()
    return user is not None 

class LoginRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_login(self, data: LoginDTO) -> Optional[LoginResponseDTO]: 
         # 1. Check if user exists
        if not await check_user_exists(self.session, data.user_id):
            return None  # Or raise an exception if you prefer  
                
        # 2. Create login entry
        entity = LoginEntity(**data.dict() )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return LoginResponseDTO.from_orm(entity)

    async def get_all_logins(self) -> List[LoginResponseDTO]:
        result = await self.session.execute(select(LoginEntity))
        entities = result.scalars().all()
        return [LoginResponseDTO.from_orm(e) for e in entities]

    async def get_login_by_id(self, login_id: int) -> Optional[LoginResponseDTO]:
        result = await self.session.execute(select(LoginEntity).where(LoginEntity.id == login_id))
        entity = result.scalars().first()
        return LoginResponseDTO.from_orm(entity) if entity else None

    async def update_login(self, login_id: int, data: LoginDTO) -> Optional[LoginResponseDTO]:
         # 1. Check if user exists
        if not await check_user_exists(self.session, data.user_id):
            return None  # Or raise an exception if you prefer  
        
        result = await self.session.execute(select(LoginEntity).where(LoginEntity.id == login_id))
        entity = result.scalars().first()
        if not entity:
            return None
        for key, value in data.dict().items():
            setattr(entity, key, value)
        await self.session.commit()
        await self.session.refresh(entity)
        return LoginResponseDTO.from_orm(entity)

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

    async def create_login(self, data: LoginDTO) -> Optional[LoginResponseDTO]:
        return await self.repo.create_login(data)

    async def get_all_logins(self) -> List[LoginResponseDTO]:
        return await self.repo.get_all_logins()

    async def get_login_by_id(self, login_id: int) -> Optional[LoginResponseDTO]:
        return await self.repo.get_login_by_id(login_id)

    async def update_login(self, login_id: int, data: LoginDTO) -> Optional[LoginResponseDTO]:
        return await self.repo.update_login(login_id, data)
    
    async def delete_login(self, login_id: int) -> bool:
        return await self.repo.delete_login(login_id)