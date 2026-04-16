from fastapi import APIRouter, HTTPException, Depends
from model.admin.login_model import LoginDTO, LoginResponseDTO
from model.auth_model import UserInDB
from typing import List
from core.database_sqlalchemy import get_db
from services.auth_service import get_current_user
from services.admin.login_service import LoginService, LoginRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Dependency to get LoginService
def get_login_service(db: AsyncSession = Depends(get_db)) -> LoginService:
    repo = LoginRepository(db)
    return LoginService(repo)

@router.post("/logins", response_model=LoginResponseDTO)
async def create_login(data: LoginDTO, service: LoginService = Depends(get_login_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.create_login(data, user=current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create login")
    return result

@router.get("/logins", response_model=List[LoginResponseDTO])
async def list_logins(service: LoginService = Depends(get_login_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    return await service.get_all_logins()

@router.get("/logins/{login_id}", response_model=LoginResponseDTO)
async def get_login(login_id: int, service: LoginService = Depends(get_login_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.get_login_by_id(login_id)
    if not result:
        raise HTTPException(status_code=404, detail="Login not found")
    return result

@router.put("/logins/{login_id}", response_model=LoginResponseDTO)
async def update_login(login_id: int, data: LoginDTO, service: LoginService = Depends(get_login_service),
                       current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                       ):
    result = await service.update_login(login_id, data, updated_by=current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Login not found")
    return result

@router.put("/logins/softdel/{login_id}")
async def delete_soft_login(login_id: int, service: LoginService = Depends(get_login_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_login(login_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Login not found")
    return {"message": "Login deleted"}

@router.delete("/logins/{login_id}")
async def delete_login(login_id: int, service: LoginService = Depends(get_login_service),
                       current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                       ):
    success = await service.delete_login(login_id)
    if not success:
        raise HTTPException(status_code=404, detail="Login not found")
    return {"message": "Login deleted"}