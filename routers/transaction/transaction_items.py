from fastapi import APIRouter, HTTPException, Depends
from model.transaction.transaction_item_model import TransactionItemDTO, TransactionItemResponseDTO
from model.auth_model import UserInDB
from typing import List
from core.database_sqlalchemy import get_db
from services.auth_service import get_current_user
from services.transaction.transaction_item_service import TransactionItemService, TransactionItemRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Dependency to get TransactionItemService
def get_transaction_item_service(db: AsyncSession = Depends(get_db)) -> TransactionItemService:
    repo = TransactionItemRepository(db)
    return TransactionItemService(repo)

@router.post("/transaction_items", response_model=TransactionItemResponseDTO)
async def create_transaction_item(data: TransactionItemDTO, service: TransactionItemService = Depends(get_transaction_item_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.create_transaction_item(data, user=current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create transaction_item")
    return result

@router.get("/transaction_items", response_model=List[TransactionItemResponseDTO])
async def list_transaction_items(service: TransactionItemService = Depends(get_transaction_item_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    return await service.get_all_transaction_items()

@router.get("/transaction_items/{transaction_id}", response_model=List[TransactionItemResponseDTO])
async def get_transaction_item(transaction_id: int, service: TransactionItemService = Depends(get_transaction_item_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.get_transaction_item_by_transaction_id(transaction_id)
    if not result:
        raise HTTPException(status_code=404, detail="TransactionItem not found")
    return result

@router.put("/transaction_items/{transaction_item_id}", response_model=TransactionItemResponseDTO)
async def update_transaction_item(transaction_item_id: int, data: TransactionItemDTO, service: TransactionItemService = Depends(get_transaction_item_service),
                       current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                       ):
    result = await service.update_transaction_item(transaction_item_id, data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="TransactionItem not found")
    return result

@router.put("/transaction_items/softdel/{transaction_item_id}")
async def delete_soft_transaction_item(transaction_item_id: int, service: TransactionItemService = Depends(get_transaction_item_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_transaction_item(transaction_item_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="TransactionItem not found")
    return {"message": "TransactionItem deleted"}

@router.delete("/transaction_items/{transaction_item_id}")
async def delete_transaction_item(transaction_item_id: int, service: TransactionItemService = Depends(get_transaction_item_service),
                       current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                       ):
    success = await service.delete_transaction_item(transaction_item_id)
    if not success:
        raise HTTPException(status_code=404, detail="TransactionItem not found")
    return {"message": "TransactionItem deleted"}