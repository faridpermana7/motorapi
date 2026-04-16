from fastapi import APIRouter, HTTPException, Depends
from model.admin.user_model import UserDTO, UserResponseDTO
from model.auth_model import UserInDB
from typing import List
from core.database_sqlalchemy import get_db
from services.admin.user_service import UserService, UserRepository
from services.auth_service import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Dependency to get UserService
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)

@router.post("/users", response_model=UserResponseDTO)
async def create_user(data: UserDTO, 
                      service: UserService = Depends(get_user_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    result = await service.create_user(data, current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create user")
    return result

@router.get("/users", response_model=List[UserResponseDTO])
async def list_users(
    service: UserService = Depends(get_user_service),
    current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    return await service.get_all_users()

@router.get("/users/{user_id}", response_model=UserResponseDTO)
async def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    result = await service.get_user_by_id(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result

@router.put("/users/{user_id}", response_model=UserResponseDTO)
async def update_user(user_id: int, data: UserDTO, service: UserService = Depends(get_user_service)
                      ,current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    result = await service.update_user(user_id, data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result

@router.put("/users/softdel/{user_id}")
async def delete_soft_user(user_id: int, service: UserService = Depends(get_user_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_user(user_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}

@router.delete("/users/{user_id}")
async def delete_hard_user(user_id: int, service: UserService = Depends(get_user_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_hard_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}