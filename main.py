from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from model_master import Provinces, Cities, Districts, Village
from typing import List
from database import Database
from services.phrases_service import PhraseService, PhraseIn
from services.locations_service import LocationsService
from services.weather_service import WeatherService
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = Database()
phrases_service = PhraseService(db)
locations_service = LocationsService()
weather_service = WeatherService()

# Phrases API endpoints
@app.post("/phrases")
async def create_phrase(data: PhraseIn):
    result = await phrases_service.create_phrase(data)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create phrase")
    return result

@app.get("/phrases")
async def list_phrases():
    return await phrases_service.get_all_phrases()

@app.get("/phrases/{phrase_id}")
async def get_phrase(phrase_id: int):
    result = await phrases_service.get_phrase_by_id(phrase_id)
    if not result:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return result

@app.put("/phrases/{phrase_id}")
async def update_phrase(phrase_id: int, data: PhraseIn):
    result = await phrases_service.update_phrase(phrase_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return result

@app.delete("/phrases/{phrase_id}")
async def delete_phrase(phrase_id: int):
    success = await phrases_service.delete_phrase(phrase_id)
    if not success:
        raise HTTPException(status_code=404, detail="Phrase not found")
    return {"status": "deleted", "id": phrase_id}

# Weather API endpoints
@app.get("/weather/{code}")
def prakiraan_cuaca(code: str):
    return weather_service.get_weather_by_code(code)

# Location API endpoints
@app.get("/provinces", response_model=List[Provinces])
def list_provinces():
    return locations_service.get_provinces()

@app.get("/cities/byparentid/{parent_id}", response_model=List[Cities])
def list_cities_by_parent_id(parent_id: int):
    return locations_service.get_cities_by_province(parent_id)

@app.get("/districts/byparentid/{parent_id}", response_model=List[Districts])
def list_districts_by_parent_id(parent_id: int):
    return locations_service.get_districts_by_city(parent_id)

@app.get("/villages/byparentid/{parent_id}", response_model=List[Village])
def list_villages_by_parent_id(parent_id: int):
    return locations_service.get_villages_by_district(parent_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9999)
