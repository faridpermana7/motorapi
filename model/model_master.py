from enum import Enum
from pydantic import BaseModel, ValidationError
from datetime import datetime
from typing import Optional, List

class VsText(Enum):
    THE_10_KM = "> 10 km"

class Provinces(BaseModel):
    id: int
    code: Optional[str] = None
    name: Optional[str] = None
    
class Cities(BaseModel):
    id: int
    province_id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None
    
class Districts(BaseModel):
    id: int
    city_id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None

class Village(BaseModel):
    id: int
    code: Optional[str] = None
    district_id: Optional[int] = None
    name: Optional[str] = None

class WeatherDesc(Enum):
    BERAWAN = "Berawan"
    CERAH = "Cerah"
    CERAH_BERAWAN = "Cerah Berawan"
    HUJAN_RINGAN = "Hujan Ringan"

class WeatherDescEn(Enum):
    LIGHT_RAIN = "Light Rain"
    MOSTLY_CLOUDY = "Mostly Cloudy"
    PARTLY_CLOUDY = "Partly Cloudy"
    SUNNY = "Sunny"

class ListCuaca(BaseModel):
    now: Optional[List['Cuaca']] = None
    day1: Optional[List['Cuaca']] = None
    day2: Optional[List['Cuaca']] = None

class Cuaca(BaseModel):
    cuaca_datetime: Optional[datetime] = None
    t: Optional[float] = None
    tcc: Optional[int] = None
    tp: Optional[float] = None
    weather: Optional[int] = None
    weather_desc: Optional[WeatherDesc] = None
    weather_desc_en: Optional[WeatherDescEn] = None
    wd_deg: Optional[int] = None
    wd: Optional[str] = None
    wd_to: Optional[str] = None
    ws: Optional[float] = None
    hu: Optional[int] = None
    vs: Optional[int] = None
    vs_text: Optional[VsText] = None
    time_index: Optional[str] = None
    analysis_date: Optional[datetime] = None
    image: Optional[str] = None
    utc_datetime: Optional[datetime] = None
    local_datetime: Optional[datetime] = None

class Lokasi(BaseModel):
    adm1: Optional[str] = None
    adm2: Optional[str] = None
    adm3: Optional[str] = None
    adm4: Optional[str] = None
    provinsi: Optional[str] = None
    kotkab: Optional[str] = None
    kecamatan: Optional[str] = None
    desa: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    timezone: Optional[str] = None

class Datum:
    lokasi: Lokasi
    cuaca: List[List[Cuaca]]

    def __init__(self, lokasi: Lokasi, cuaca: List[List[Cuaca]]) -> None:
        self.lokasi = lokasi
        self.cuaca = cuaca

class Welcome:
    lokasi: Lokasi
    data: List[Datum]

    def __init__(self, lokasi: Lokasi, data: List[Datum]) -> None:
        self.lokasi = lokasi
        self.data = data