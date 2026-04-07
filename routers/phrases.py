from fastapi import APIRouter, HTTPException, Depends
from model.phrase_model import PhraseDTO, PhraseResponseDTO
from typing import List
from database_sqlalchemy import get_db
from services.phrase_service import PhraseService, PhraseRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Dependency to get PhraseService
def get_phrase_service(db: AsyncSession = Depends(get_db)) -> PhraseService:
    repo = PhraseRepository(db)
    return PhraseService(repo)

@router.post("/phrases", response_model=PhraseResponseDTO)
async def create_phrase(data: PhraseDTO, service: PhraseService = Depends(get_phrase_service)):
    result = await service.create_phrase(data)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create phrase")
    return result

@router.get("/phrases", response_model=List[PhraseResponseDTO])
async def list_phrases(service: PhraseService = Depends(get_phrase_service)):
    return await service.get_all_phrases()

@router.get("/phrases/{phrase_id}", response_model=PhraseResponseDTO)
async def get_phrase(phrase_id: int, service: PhraseService = Depends(get_phrase_service)):
    result = await service.get_phrase_by_id(phrase_id)
    if not result:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return result

@router.put("/phrases/{phrase_id}", response_model=PhraseResponseDTO)
async def update_phrase(phrase_id: int, data: PhraseDTO, service: PhraseService = Depends(get_phrase_service)):
    result = await service.update_phrase(phrase_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return result

@router.delete("/phrases/{phrase_id}")
async def delete_phrase(phrase_id: int, service: PhraseService = Depends(get_phrase_service)):
    success = await service.delete_phrase(phrase_id)
    if not success:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return {"message": "Phrase deleted"}