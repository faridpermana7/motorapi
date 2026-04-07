from fastapi import APIRouter, HTTPException, Depends
from model.login_model import LoginDTO, LoginResponseDTO
from typing import List
from database_sqlalchemy import get_db
from services.login_service import LoginService, LoginRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Dependency to get LoginService
def get_login_service(db: AsyncSession = Depends(get_db)) -> LoginService:
    repo = LoginRepository(db)
    return LoginService(repo)

@router.post("/logins", response_model=LoginResponseDTO)
async def create_login(data: LoginDTO, service: LoginService = Depends(get_login_service)):
    result = await service.create_login(data)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create login")
    return result

@router.get("/logins", response_model=List[LoginResponseDTO])
async def list_logins(service: LoginService = Depends(get_login_service)):
    return await service.get_all_logins()

@router.get("/logins/{login_id}", response_model=LoginResponseDTO)
async def get_login(login_id: int, service: LoginService = Depends(get_login_service)):
    result = await service.get_login_by_id(login_id)
    if not result:
        raise HTTPException(status_code=404, detail="Login not found")
    return result

@router.put("/logins/{login_id}", response_model=LoginResponseDTO)
async def update_login(login_id: int, data: LoginDTO, service: LoginService = Depends(get_login_service)):
    result = await service.update_login(login_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Login not found")
    return result

@router.delete("/logins/{login_id}")
async def delete_login(login_id: int, service: LoginService = Depends(get_login_service)):
    success = await service.delete_login(login_id)
    if not success:
        raise HTTPException(status_code=404, detail="Login not found")
    return {"message": "Login deleted"}