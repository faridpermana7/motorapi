from fastapi import APIRouter, HTTPException, Depends
from model.admin.phrase_model import PhraseDTO, PhraseResponseDTO
from typing import List
from core.database_sqlalchemy import get_db
from model.auth_model import UserInDB
from services.admin.phrase_service import PhraseService, PhraseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import get_current_user

router = APIRouter()

# Dependency to get PhraseService
def get_phrase_service(db: AsyncSession = Depends(get_db)) -> PhraseService:
    repo = PhraseRepository(db)
    return PhraseService(repo)

@router.post("/phrases", response_model=PhraseResponseDTO)
async def create_phrase(data: PhraseDTO, service: PhraseService = Depends(get_phrase_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.create_phrase(data, current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create phrase")
    return result

@router.get("/phrases", response_model=List[PhraseResponseDTO])
async def list_phrases(service: PhraseService = Depends(get_phrase_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    return await service.get_all_phrases()

@router.get("/phrases/{phrase_id}", response_model=PhraseResponseDTO)
async def get_phrase(phrase_id: int, service: PhraseService = Depends(get_phrase_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.get_phrase_by_id(phrase_id)
    if not result:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return result

@router.put("/phrases/{phrase_id}", response_model=PhraseResponseDTO)
async def update_phrase(phrase_id: int, data: PhraseDTO, service: PhraseService = Depends(get_phrase_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.update_phrase(phrase_id, data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return result

@router.put("/phrases/softdel/{phrase_id}")
async def delete_soft_phrase(phrase_id: int, service: PhraseService = Depends(get_phrase_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_phrase(phrase_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return {"message": "Phrase deleted"}

@router.delete("/phrases/{phrase_id}")
async def delete_phrase(phrase_id: int, service: PhraseService = Depends(get_phrase_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    success = await service.delete_phrase(phrase_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return {"message": "Phrase deleted"}