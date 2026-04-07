from fastapi import APIRouter
from model.model_master import Provinces, Cities, Districts, Village
from typing import List
from services.location_service import LocationsService

router = APIRouter()
locations_service = LocationsService()

@router.get("/provinces", response_model=List[Provinces])
def list_provinces():
    return locations_service.get_provinces()

@router.get("/cities/byparentid/{parent_id}", response_model=List[Cities])
def list_cities_by_parent_id(parent_id: int):
    return locations_service.get_cities_by_province(parent_id)

@router.get("/districts/byparentid/{parent_id}", response_model=List[Districts])
def list_districts_by_parent_id(parent_id: int):
    return locations_service.get_districts_by_city(parent_id)

@router.get("/villages/byparentid/{parent_id}", response_model=List[Village])
def list_villages_by_parent_id(parent_id: int):
    return locations_service.get_villages_by_district(parent_id)