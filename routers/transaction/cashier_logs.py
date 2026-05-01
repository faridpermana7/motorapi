from fastapi import APIRouter, HTTPException, Depends
from model.transaction.cashier_log_model import CashierLogDTO, CashierLogResponseDTO
from model.auth_model import UserInDB
from typing import List
from core.database_sqlalchemy import get_db
from services.auth_service import get_current_user
from services.transaction.cashier_log_service import CashierLogService, CashierLogRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Dependency to get CashierLogService
def get_cashier_log_service(db: AsyncSession = Depends(get_db)) -> CashierLogService:
    repo = CashierLogRepository(db)
    return CashierLogService(repo)

@router.post("/cashier_logs", response_model=CashierLogResponseDTO)
async def create_cashier_log(data: CashierLogDTO, service: CashierLogService = Depends(get_cashier_log_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.create_cashier_log(data, user=current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create cashier_log")
    return result

@router.get("/cashier_logs", response_model=List[CashierLogResponseDTO])
async def list_cashier_logs(service: CashierLogService = Depends(get_cashier_log_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    return await service.get_all_cashier_logs()

@router.get("/cashier_logs/{cashier_log_id}", response_model=CashierLogResponseDTO)
async def get_cashier_log(cashier_log_id: int, service: CashierLogService = Depends(get_cashier_log_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.get_cashier_log_by_id(cashier_log_id)
    if not result:
        raise HTTPException(status_code=404, detail="CashierLog not found")
    return result

@router.put("/cashier_logs/{cashier_log_id}", response_model=CashierLogResponseDTO)
async def update_cashier_log(cashier_log_id: int, data: CashierLogDTO, service: CashierLogService = Depends(get_cashier_log_service),
                       current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                       ):
    result = await service.update_cashier_log(cashier_log_id, data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="CashierLog not found")
    return result

@router.put("/cashier_logs/softdel/{cashier_log_id}")
async def delete_soft_cashier_log(cashier_log_id: int, service: CashierLogService = Depends(get_cashier_log_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_cashier_log(cashier_log_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="CashierLog not found")
    return {"message": "CashierLog deleted"}

@router.delete("/cashier_logs/{cashier_log_id}")
async def delete_cashier_log(cashier_log_id: int, service: CashierLogService = Depends(get_cashier_log_service),
                       current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                       ):
    success = await service.delete_cashier_log(cashier_log_id)
    if not success:
        raise HTTPException(status_code=404, detail="CashierLog not found")
    return {"message": "CashierLog deleted"}