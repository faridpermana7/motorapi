from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from model_master import Lokasi,Provinces, Districts, Cities, Village, Cuaca, VsText, WeatherDesc, WeatherDescEn, cuaca_to_dict, parse_cuaca_matrix, parse_cuaca_matrix_for_listcuaca
from typing import List, Optional   
import requests
from pathlib import Path
import json

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
 
def _load_json_with_fallback(primary_path: str, fallback_path: Optional[str] = None):
    """Load JSON from primary_path, falling back to fallback_path.

    Both paths are tried relative to the script directory first, then as provided.
    Returns the parsed JSON (usually a list/dict) or an empty list on failure.
    """
    base = Path(__file__).resolve().parent

    def candidates(path_str: str):
        p = Path(path_str)
        if not p.is_absolute():
            yield base / p
        yield p

    tried = []
    # try primary candidates
    for p in candidates(primary_path):
        tried.append(p)
        try:
            with p.open('r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"Error loading JSON from {p}: {e}")
            return []

    # try fallback candidates
    if fallback_path:
        for p in candidates(fallback_path):
            tried.append(p)
            try:
                with p.open('r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Error loading JSON from {p}: {e}")
                return []

    print(f"File not found: tried paths: {', '.join(str(x) for x in tried)}")
    return []


def load_provinces() -> List[Provinces]:
    provinces_data = _load_json_with_fallback('tempdata/provinces.json', 'provinces.json')
    return [Provinces(**p) for p in provinces_data]


def load_cities() -> List[Cities]:
    cities_data = _load_json_with_fallback('tempdata/cities.json', 'cities.json')
    return [Cities(**c) for c in cities_data]


def load_districts() -> List[Districts]:
    districts_data = _load_json_with_fallback('tempdata/districts.json', 'districts.json')
    return [Districts(**d) for d in districts_data]


def load_villages() -> List[Village]:
    villages_data = _load_json_with_fallback('tempdata/villages.json', 'villages.json')
    return [Village(**v) for v in villages_data]


provinces = load_provinces()
cities = load_cities()
districts = load_districts()
villages = load_villages()

@app.get("/weather/{code}")
def prakiraan_cuaca(code: str):
    api_url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={code}"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json() 
        # parse Lokasi using pydantic (support v2/v1)
        lokasi_raw = data.get("lokasi", {})
        try:
            loc = Lokasi.model_validate(lokasi_raw)
        except Exception:
            try:
                loc = Lokasi.parse_obj(lokasi_raw)
            except Exception:
                loc = Lokasi(**lokasi_raw)

        cuaca_raw = data.get("data", [{}])[0].get("cuaca", [[]])
        list_cuaca = parse_cuaca_matrix_for_listcuaca(cuaca_raw)

        def serialize_model(m):
            if hasattr(m, "model_dump"):
                return m.model_dump()
            if hasattr(m, "dict"):
                return m.dict()
            try:
                return vars(m)
            except Exception:
                return None

        cuaca_serialized = {
            "now": [cuaca_to_dict(c) for c in (list_cuaca.now or [])],
            "day1": [cuaca_to_dict(c) for c in (list_cuaca.day1 or [])],
            "day2": [cuaca_to_dict(c) for c in (list_cuaca.day2 or [])],
        }

        return JSONResponse(content={
            "lokasi": serialize_model(loc),
            "cuaca": cuaca_serialized
        })
    except Exception as e:
        return Response(
            content=f"ERROR: Gagal mengambil data. ({e})",
            media_type="text/plain"
        )
  

@app.get("/provinces", response_model=List[Provinces])
def list_provinces():
    return provinces

@app.get("/cities/byparentid/{parent_id}", response_model=List[Cities])
def list_cities_by_parent_id(parent_id: int):
    return [city for city in cities if city.province_id == parent_id]

@app.get("/districts/byparentid/{parent_id}", response_model=List[Districts])
def list_districts_by_parent_id(parent_id: int):
    return [district for district in districts if district.city_id == parent_id]

@app.get("/villages/byparentid/{parent_id}", response_model=List[Village])
def list_villages_by_parent_id(parent_id: int):
    return [village for village in villages if village.district_id == parent_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9999)
