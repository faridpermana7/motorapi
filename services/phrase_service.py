from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from model.phrase_model import PhraseEntity, PhraseDTO, PhraseResponseDTO

class PhraseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_phrase(self, data: PhraseDTO) -> Optional[PhraseResponseDTO]:
        entity = PhraseEntity(**data.dict())
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return PhraseResponseDTO.from_orm(entity)

    async def get_all_phrases(self) -> List[PhraseResponseDTO]:
        result = await self.session.execute(select(PhraseEntity))
        entities = result.scalars().all()
        return [PhraseResponseDTO.from_orm(e) for e in entities]

    async def get_phrase_by_id(self, phrase_id: int) -> Optional[PhraseResponseDTO]:
        result = await self.session.execute(select(PhraseEntity).where(PhraseEntity.id == phrase_id))
        entity = result.scalars().first()
        return PhraseResponseDTO.from_orm(entity) if entity else None

    async def update_phrase(self, phrase_id: int, data: PhraseDTO) -> Optional[PhraseResponseDTO]:
        result = await self.session.execute(select(PhraseEntity).where(PhraseEntity.id == phrase_id))
        entity = result.scalars().first()
        if not entity:
            return None
        for key, value in data.dict().items():
            setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(entity)
        return PhraseResponseDTO.from_orm(entity)

    async def delete_phrase(self, phrase_id: int) -> bool:
        result = await self.session.execute(select(PhraseEntity).where(PhraseEntity.id == phrase_id))
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class PhraseService:
    def __init__(self, repo: PhraseRepository):
        self.repo = repo

    async def create_phrase(self, data: PhraseDTO) -> Optional[PhraseResponseDTO]:
        return await self.repo.create_phrase(data)

    async def get_all_phrases(self) -> List[PhraseResponseDTO]:
        return await self.repo.get_all_phrases()

    async def get_phrase_by_id(self, phrase_id: int) -> Optional[PhraseResponseDTO]:
        return await self.repo.get_phrase_by_id(phrase_id)

    async def update_phrase(self, phrase_id: int, data: PhraseDTO) -> Optional[PhraseResponseDTO]:
        return await self.repo.update_phrase(phrase_id, data)

    async def delete_phrase(self, phrase_id: int) -> bool:
        return await self.repo.delete_phrase(phrase_id)