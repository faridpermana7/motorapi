from fastapi import APIRouter, HTTPException, Depends
from model.master.customer_model import CustomerDTO, CustomerResponseDTO
from typing import List
from core.database_sqlalchemy import get_db
from model.auth_model import UserInDB
from services.master.customer_service import CustomerService, CustomerRepository
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import get_current_user

router = APIRouter()

# Dependency to get CustomerService
def get_customer_service(db: AsyncSession = Depends(get_db)) -> CustomerService:
    repo = CustomerRepository(db)
    return CustomerService(repo)

@router.post("/customers", response_model=CustomerResponseDTO)
async def create_customer(data: CustomerDTO, service: CustomerService = Depends(get_customer_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.create_customer(data, current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create customer")
    return result

@router.get("/customers", response_model=List[CustomerResponseDTO])
async def list_customers(service: CustomerService = Depends(get_customer_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    return await service.get_all_customers()

@router.get("/customers/{customer_id}", response_model=CustomerResponseDTO)
async def get_customer(customer_id: int, service: CustomerService = Depends(get_customer_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.get_customer_by_id(customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return result

@router.put("/customers/{customer_id}", response_model=CustomerResponseDTO)
async def update_customer(customer_id: int, data: CustomerDTO, service: CustomerService = Depends(get_customer_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.update_customer(customer_id, data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return result


@router.put("/customers/softdel/{customer_id}")
async def delete_soft_customer(customer_id: int, service: CustomerService = Depends(get_customer_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_customer(customer_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return {"message": "Enum Table deleted"}

@router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: int, service: CustomerService = Depends(get_customer_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    success = await service.delete_customer(customer_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return {"message": "Enum Table deleted"}