from fastapi import APIRouter, HTTPException, Depends
from model.admin.configuration_model import ConfigurationDTO, ConfigurationResponseDTO
from typing import List
from core.database_sqlalchemy import get_db
from model.auth_model import UserInDB
from services.admin.configuration_service import ConfigurationService, ConfigurationRepository
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import get_current_user

router = APIRouter()

# Dependency to get ConfigurationService
def get_configuration_service(db: AsyncSession = Depends(get_db)) -> ConfigurationService:
    repo = ConfigurationRepository(db)
    return ConfigurationService(repo)

@router.post("/configurations", response_model=ConfigurationResponseDTO)
async def create_configuration(data: ConfigurationDTO, service: ConfigurationService = Depends(get_configuration_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.create_configuration(data, current_user.username)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create configuration")
    return result

@router.get("/configurations", response_model=List[ConfigurationResponseDTO])
async def list_configurations(service: ConfigurationService = Depends(get_configuration_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    return await service.get_all_configurations()

@router.get("/configurations/{configuration_id}", response_model=ConfigurationResponseDTO)
async def get_configuration(configuration_id: int, service: ConfigurationService = Depends(get_configuration_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.get_configuration_by_id(configuration_id)
    if not result:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return result


@router.put("/configurations/list", response_model=List[ConfigurationResponseDTO])
async def update_configuration_list(data: List[ConfigurationDTO], service: ConfigurationService = Depends(get_configuration_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.update_configuration_list(data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return result

@router.put("/configurations/{configuration_id}", response_model=ConfigurationResponseDTO)
async def update_configuration(configuration_id: int, data: ConfigurationDTO, service: ConfigurationService = Depends(get_configuration_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    result = await service.update_configuration(configuration_id, data, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return result

@router.put("/configurations/softdel/{configuration_id}")
async def delete_soft_configuration(configuration_id: int, service: ConfigurationService = Depends(get_configuration_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
):
    success = await service.delete_soft_configuration(configuration_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"message": "Configuration deleted"}

@router.delete("/configurations/{configuration_id}")
async def delete_configuration(configuration_id: int, service: ConfigurationService = Depends(get_configuration_service),
                      current_user: UserInDB = Depends(get_current_user)  # Protected endpoint
                      ):
    success = await service.delete_configuration(configuration_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"message": "Configuration deleted"}