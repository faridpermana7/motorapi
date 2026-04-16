from fastapi import APIRouter, HTTPException, Depends
from model.master.item_model import ItemDTO, ItemResponseDTO
from model.auth_model import UserInDB
from typing import List
from core.database_sqlalchemy import get_db
from services.auth_service import get_current_user
from services.master.item_service import ItemService, ItemRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Dependency to get ItemService
def get_item_service(db: AsyncSession = Depends(get_db)) -> ItemService:
    repo = ItemRepository(db)
    return ItemService(repo)

@router.post("/items", response_model=ItemResponseDTO)
async def create_item(data: ItemDTO, service: ItemService = Depends(get_item_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.create_item(data, user=current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create item")
    return result

@router.get("/items", response_model=List[ItemResponseDTO])
async def list_items(service: ItemService = Depends(get_item_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    return await service.get_all_items()

@router.get("/items/{item_id}", response_model=ItemResponseDTO)
async def get_item(item_id: int, service: ItemService = Depends(get_item_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.get_item_by_id(item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result

@router.put("/items/{item_id}", response_model=ItemResponseDTO)
async def update_item(item_id: int, data: ItemDTO, service: ItemService = Depends(get_item_service),
                       current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                       ):
    result = await service.update_item(item_id, data, updated_by=current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result

@router.put("/items/softdel/{item_id}")
async def delete_soft_item(item_id: int, service: ItemService = Depends(get_item_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_item(item_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}

@router.delete("/items/{item_id}")
async def delete_item(item_id: int, service: ItemService = Depends(get_item_service),
                       current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                       ):
    success = await service.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}