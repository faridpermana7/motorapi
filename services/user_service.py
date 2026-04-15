from datetime import datetime

from sqlalchemy import null
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from model.user_model import UserEntity, UserDTO, UserResponseDTO
from passlib.context import CryptContext

# Use Argon2 instead of bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, data: UserDTO, created_by: str) -> Optional[UserResponseDTO]: 
        entity = UserEntity(
            **data.dict(
                exclude={
                    "password", 
                    "created_by", 
                    "updated_by", 
                    "created_at", 
                    "updated_at", 
                    "deleted_at"
                }
            )
        )
        entity.password_hash = hash_password(data.password)
        entity.created_by = created_by
        entity.created_at = datetime.utcnow()
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return UserResponseDTO.from_orm(entity)

    async def get_all_users(self) -> List[UserResponseDTO]:
        query = select(UserEntity).where(UserEntity.deleted_at == null())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [UserResponseDTO.from_orm(e) for e in entities]

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponseDTO]:
        query = select(UserEntity).where(UserEntity.deleted_at == null() & UserEntity.id == user_id) 
        result = await self.session.execute(query) 
        entity = result.scalars().first()
        return UserResponseDTO.from_orm(entity) if entity else None

    async def update_user(self, user_id: int, data: UserDTO, updated_by: str) -> Optional[UserResponseDTO]:
        query = select(UserEntity).where(UserEntity.deleted_at == null()).where(UserEntity.id == user_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return None
        for key, value in data.dict(exclude={"password"}).items():
            setattr(entity, key, value)
        if data.password:
            entity.password_hash = hash_password(data.password)

        entity.updated_at = datetime.utcnow()
        entity.updated_by = updated_by
        await self.session.commit()
        await self.session.refresh(entity)
        return UserResponseDTO.from_orm(entity)

    async def delete_soft_user(self, user_id: int, deleted_by: str) -> bool:
        query = select(UserEntity).where(UserEntity.deleted_at == null()).where(UserEntity.id == user_id)
        result = await self.session.execute(query) 
        entity = result.scalars().first()
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = deleted_by
        await self.session.commit()
        await self.session.refresh(entity)
        return True
    
    async def delete_hard_user(self, user_id: int) -> bool:
        query = select(UserEntity).where(UserEntity.deleted_at == null()).where(UserEntity.id == user_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, data: UserDTO, updated_by: str) -> Optional[UserResponseDTO]:
        return await self.repo.create_user(data, updated_by)

    async def get_all_users(self) -> List[UserResponseDTO]:
        return await self.repo.get_all_users()

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponseDTO]:
        return await self.repo.get_user_by_id(user_id)

    async def update_user(self, user_id: int, data: UserDTO, updated_by: str) -> Optional[UserResponseDTO]:
        return await self.repo.update_user(user_id, data, updated_by)

    async def delete_soft_user(self, user_id: int, deleted_by: str) -> bool:
        return await self.repo.delete_soft_user(user_id, deleted_by)

    async def delete_hard_user(self, user_id: int) -> bool:
        return await self.repo.delete_hard_user(user_id)