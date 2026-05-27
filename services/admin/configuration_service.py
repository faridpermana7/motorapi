from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from model.admin.configuration_model import ConfigurationEntity, ConfigurationDTO, ConfigurationResponseDTO

class ConfigurationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_configurations(self) -> List[ConfigurationResponseDTO]:
        query = select(ConfigurationEntity).where(ConfigurationEntity.deleted_at == None)
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [ConfigurationResponseDTO.from_orm(e) for e in entities]

    async def get_configuration_by_id(self, configuration_id: int) -> Optional[ConfigurationResponseDTO]:
        query = select(ConfigurationEntity).where(ConfigurationEntity.deleted_at == None).where(ConfigurationEntity.id == configuration_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return ConfigurationResponseDTO.from_orm(entity) if entity else None

    async def create_configuration(self, data: ConfigurationDTO, user: str) -> Optional[ConfigurationResponseDTO]:
        entity = ConfigurationEntity(**data.dict())
        entity.created_at = datetime.utcnow()
        entity.created_by = user
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return ConfigurationResponseDTO.from_orm(entity)
    
    async def update_configuration(self, configuration_id: int, data: ConfigurationDTO, user: str) -> Optional[ConfigurationResponseDTO]:
        query = select(ConfigurationEntity).where(ConfigurationEntity.deleted_at == None).where(ConfigurationEntity.id == configuration_id)
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
        return ConfigurationResponseDTO.from_orm(entity)
    
    
    async def update_configuration_list(
        self, data: List[ConfigurationDTO], user: str
    ) -> List[ConfigurationResponseDTO]:
        updated_entities = []
        
        for dto in data:
            # Fetch entity by id
            query = select(ConfigurationEntity).where(
                ConfigurationEntity.deleted_at == None,
                ConfigurationEntity.id == dto.id
            )
            result = await self.session.execute(query)
            entity = result.scalars().first()

            if not entity:
                continue  # skip if not found

            # Update fields from DTO
            for key, value in dto.dict(exclude_unset=True).items():
                setattr(entity, key, value)

            entity.updated_by = user
            entity.updated_at = datetime.utcnow()
            updated_entities.append(entity)

        # Commit once for all updates
        await self.session.commit()

        # Refresh all updated entities
        for entity in updated_entities:
            await self.session.refresh(entity)

        # Return list of response DTOs
        return [ConfigurationResponseDTO.from_orm(e) for e in updated_entities]

    async def delete_soft_configuration(self, configuration_id: int, user: str) -> bool:
        query = select(ConfigurationEntity).where(ConfigurationEntity.deleted_at == None).where(ConfigurationEntity.id == configuration_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = user
        await self.session.commit()
        await self.session.refresh(entity)
        return True

    async def delete_configuration(self, configuration_id: int) -> bool:
        result = await self.session.execute(select(ConfigurationEntity).where(ConfigurationEntity.id == configuration_id))
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class ConfigurationService:
    def __init__(self, repo: ConfigurationRepository):
        self.repo = repo

    async def create_configuration(self, data: ConfigurationDTO, user: str) -> Optional[ConfigurationResponseDTO]:
        return await self.repo.create_configuration(data, user)

    async def get_all_configurations(self) -> List[ConfigurationResponseDTO]:
        return await self.repo.get_all_configurations()

    async def get_configuration_by_id(self, configuration_id: int) -> Optional[ConfigurationResponseDTO]:
        return await self.repo.get_configuration_by_id(configuration_id)

    async def update_configuration(self, configuration_id: int, data: ConfigurationDTO,  user: str) -> Optional[ConfigurationResponseDTO]:
        return await self.repo.update_configuration(configuration_id, data, user)
    
    async def update_configuration_list(self, data: List[ConfigurationDTO], user: str) -> List[ConfigurationResponseDTO]:
        return await self.repo.update_configuration_list(data, user)

    async def delete_soft_configuration(self, configuration_id: int, user: str) -> bool:
        return await self.repo.delete_soft_configuration(configuration_id, user)

    async def delete_configuration(self, configuration_id: int) -> bool:
        return await self.repo.delete_configuration(configuration_id)