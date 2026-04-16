import requests
from fastapi.responses import JSONResponse
from fastapi import Response
from model.master.location_master import Lokasi
from utils.parsers import cuaca_to_dict, parse_cuaca_matrix_for_listcuaca

class WeatherService:
    def __init__(self):
        self.base_url = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

    def get_weather_by_code(self, code: str) -> JSONResponse | Response:
        api_url = f"{self.base_url}?adm4={code}"
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