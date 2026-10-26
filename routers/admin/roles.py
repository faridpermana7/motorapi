from fastapi import APIRouter, HTTPException, Depends, status
from model.admin.role_model import RoleDTO, RoleResponseDTO
from typing import List
from core.database_sqlalchemy import get_db
from model.auth_model import UserInDB
from services.admin.role_service import RoleService, RoleRepository
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import get_current_user

router = APIRouter()

# Dependency to get RoleService
def get_role_service(db: AsyncSession = Depends(get_db)) -> RoleService:
    repo = RoleRepository(db)
    return RoleService(repo)

@router.post("", response_model=RoleResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleDTO, 
    service: RoleService = Depends(get_role_service),
    current_user: UserInDB = Depends(get_current_user)
):
    result = await service.create_role(data, current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create role")
    return result

@router.get("", response_model=List[RoleResponseDTO])
async def list_roles(
    service: RoleService = Depends(get_role_service),
    current_user: UserInDB = Depends(get_current_user)
):
    return await service.get_all_roles()

@router.get("/{role_id}", response_model=RoleResponseDTO)
async def get_role(
    role_id: int, 
    service: RoleService = Depends(get_role_service),
    current_user: UserInDB = Depends(get_current_user)
):
    result = await service.get_role_by_id(role_id)
    if not result:
        raise HTTPException(status_code=404, detail="Role not found")
    return result

@router.put("/{role_id}", response_model=RoleResponseDTO)
async def update_role(
    role_id: int, 
    data: RoleDTO, 
    service: RoleService = Depends(get_role_service),
    current_user: UserInDB = Depends(get_current_user)
):
    result = await service.update_role(role_id, data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Role not found")
    return result

@router.put("/softdel/{role_id}")
async def delete_soft_role(
    role_id: int, 
    service: RoleService = Depends(get_role_service),
    current_user: UserInDB = Depends(get_current_user)
):
    success = await service.delete_soft_role(role_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted successfully"}

@router.delete("/{role_id}")
async def delete_role(
    role_id: int, 
    service: RoleService = Depends(get_role_service),
    current_user: UserInDB = Depends(get_current_user)
):
    success = await service.delete_hard_role(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role permanently deleted"}