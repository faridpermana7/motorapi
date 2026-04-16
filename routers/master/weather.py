from fastapi import APIRouter
from services.master.weather_service import WeatherService

router = APIRouter()
weather_service = WeatherService()

@router.get("/weather/{code}")
def prakiraan_cuaca(code: str):
    return weather_service.get_weather_by_code(code)