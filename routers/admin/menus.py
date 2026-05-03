from fastapi import APIRouter, HTTPException, Depends
from model.admin.menu_model import MenuDTO, MenuResponseDTO, MenuTreeDTO
from typing import List
from core.database_sqlalchemy import get_db
from model.auth_model import UserInDB
from services.admin.menu_service import MenuService, MenuRepository
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import get_current_user

router = APIRouter()

# Dependency to get MenuService
def get_menu_service(db: AsyncSession = Depends(get_db)) -> MenuService:
    repo = MenuRepository(db)
    return MenuService(repo)

@router.post("/menus", response_model=MenuResponseDTO)
async def create_menu(data: MenuDTO, service: MenuService = Depends(get_menu_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.create_menu(data, current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create menu")
    return result

@router.get("/menus/parents", response_model=List[MenuResponseDTO])
async def list_parent_menus(service: MenuService = Depends(get_menu_service),
                            current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                            ):
    return await service.get_all_parents()


@router.get("/menu_trees", response_model=List[MenuTreeDTO])
async def list_menu_trees(service: MenuService = Depends(get_menu_service),
                          current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                          ):
    return await service.get_menu_tree()

@router.get("/menus", response_model=List[MenuResponseDTO])
async def list_menus(service: MenuService = Depends(get_menu_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    return await service.get_all_menus()

@router.get("/menus/{menu_id}", response_model=MenuResponseDTO)
async def get_menu(menu_id: int, service: MenuService = Depends(get_menu_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.get_menu_by_id(menu_id)
    if not result:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return result

@router.put("/menus/{menu_id}", response_model=MenuResponseDTO)
async def update_menu(menu_id: int, data: MenuDTO, service: MenuService = Depends(get_menu_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.update_menu(menu_id, data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return result


@router.put("/menus/softdel/{menu_id}")
async def delete_soft_menu(menu_id: int, service: MenuService = Depends(get_menu_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_menu(menu_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return {"message": "Enum Table deleted"}

@router.delete("/menus/{menu_id}")
async def delete_menu(menu_id: int, service: MenuService = Depends(get_menu_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    success = await service.delete_menu(menu_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return {"message": "Enum Table deleted"}