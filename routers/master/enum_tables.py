from fastapi import APIRouter, HTTPException, Depends
from model.master.enum_table_model import EnumTableDTO, EnumTableResponseDTO
from typing import List
from core.database_sqlalchemy import get_db
from model.auth_model import UserInDB
from services.master.enum_table_service import EnumTableService, EnumTableRepository
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import get_current_user

router = APIRouter()

# Dependency to get EnumTableService
def get_enum_table_service(db: AsyncSession = Depends(get_db)) -> EnumTableService:
    repo = EnumTableRepository(db)
    return EnumTableService(repo)

@router.post("/enum_tables", response_model=EnumTableResponseDTO)
async def create_enum_table(data: EnumTableDTO, service: EnumTableService = Depends(get_enum_table_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.create_enum_table(data, current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create enum_table")
    return result

@router.get("/enum_tables", response_model=List[EnumTableResponseDTO])
async def list_enum_tables(service: EnumTableService = Depends(get_enum_table_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    return await service.get_all_enum_tables()

@router.get("/enum_tables/{enum_table_id}", response_model=EnumTableResponseDTO)
async def get_enum_table(enum_table_id: int, service: EnumTableService = Depends(get_enum_table_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.get_enum_table_by_id(enum_table_id)
    if not result:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return result

@router.put("/enum_tables/{enum_table_id}", response_model=EnumTableResponseDTO)
async def update_enum_table(enum_table_id: int, data: EnumTableDTO, service: EnumTableService = Depends(get_enum_table_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.update_enum_table(enum_table_id, data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return result


@router.put("/enum_tables/softdel/{enum_table_id}")
async def delete_soft_enum_table(enum_table_id: int, service: EnumTableService = Depends(get_enum_table_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_enum_table(enum_table_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return {"message": "Enum Table deleted"}

@router.delete("/enum_tables/{enum_table_id}")
async def delete_enum_table(enum_table_id: int, service: EnumTableService = Depends(get_enum_table_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    success = await service.delete_enum_table(enum_table_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Enum Table not found")
    return {"message": "Enum Table deleted"}