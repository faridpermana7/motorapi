from fastapi import APIRouter, HTTPException, Depends, Query
from model.pagination_model import PaginationResponseDTO
from model.transaction.transaction_model import TransactionDTO, TransactionDashboardPerDayDTO, TransactionResponseDTO
from model.auth_model import UserInDB
from typing import List, Literal, Optional
from core.database_sqlalchemy import get_db
from services.auth_service import get_current_user
from services.transaction.transaction_service import TransactionService, TransactionRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Dependency to get TransactionService
def get_transaction_service(db: AsyncSession = Depends(get_db)) -> TransactionService:
    repo = TransactionRepository(db)
    return TransactionService(repo)

@router.post("/transactions", response_model=TransactionResponseDTO)
async def create_transaction(data: TransactionDTO, service: TransactionService = Depends(get_transaction_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.create_transaction(data, user=current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create transaction")
    return result

@router.get("/transactions", response_model=List[TransactionResponseDTO])
async def list_transactions(service: TransactionService = Depends(get_transaction_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    try:
        res = await service.get_all_transactions()
        return res
    except HTTPException as e:
        # re-raise FastAPI HTTPExceptions so they propagate correctly
        raise e
    except Exception as e:
        # catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get(
    "/transactions/pagination",
    response_model=PaginationResponseDTO[TransactionResponseDTO],
)
async def list_transactions_paginated(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Literal[
        "id", "name", "code", "barcode", "brand", "stock",
        "cost_price", "selling_price", "created_at",
    ] = "id",
    sort_order: Literal["asc", "desc"] = "asc",
    service: TransactionService = Depends(get_transaction_service),
    current_user: UserInDB = Depends(get_current_user),
):
    return await service.get_paginated_transactions(
        skip, limit, search, sort_by, sort_order
    )


@router.get("/transactions/dashboard/perday", response_model=TransactionDashboardPerDayDTO)
async def get_dashboard_data(service: TransactionService = Depends(get_transaction_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    return await service.get_dashboard_data()

@router.get("/transactions/{transaction_id}", response_model=TransactionResponseDTO)
async def get_transaction(transaction_id: int, service: TransactionService = Depends(get_transaction_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.get_transaction_by_id(transaction_id)
    if not result:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return result

@router.put("/transactions/{transaction_id}", response_model=TransactionResponseDTO)
async def update_transaction(transaction_id: int, data: TransactionDTO, service: TransactionService = Depends(get_transaction_service),
                       current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                       ):
    result = await service.update_transaction(transaction_id, data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return result

@router.put("/transactions/softdel/{transaction_id}")
async def delete_soft_transaction(transaction_id: int, service: TransactionService = Depends(get_transaction_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_transaction(transaction_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}

@router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int, service: TransactionService = Depends(get_transaction_service),
                       current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                       ):
    success = await service.delete_transaction(transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}