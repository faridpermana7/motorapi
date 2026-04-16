
from datetime import datetime
from enum import Enum
from model.master.location_master import ListCuaca, VsText, WeatherDesc, Cuaca, WeatherDescEn


def parse_datetime(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        try:
            return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return None

def parse_enum(enum_cls: Enum, value: str):
    if value is None:
        return None
    for member in enum_cls:
        if member.value == value or member.name == value:
            return member
    return None

def parse_cuaca_item(d: dict) -> Cuaca:
    payload = {
        "cuaca_datetime": parse_datetime(d.get("cuaca_datetime") or d.get("utc_datetime") or d.get("local_datetime")),
        "t": d.get("t"),
        "tcc": d.get("tcc"),
        "tp": d.get("tp"),
        "weather": d.get("weather"),
        "weather_desc": parse_enum(WeatherDesc, d.get("weather_desc")),
        "weather_desc_en": parse_enum(WeatherDescEn, d.get("weather_desc_en")),
        "wd_deg": d.get("wd_deg"),
        "wd": d.get("wd"),
        "wd_to": d.get("wd_to"),
        "ws": d.get("ws"),
        "hu": d.get("hu"),
        "vs": d.get("vs"),
        "vs_text": parse_enum(VsText, d.get("vs_text")),
        "time_index": d.get("time_index"),
        "analysis_date": parse_datetime(d.get("analysis_date")),
        "image": d.get("image"),
        "utc_datetime": parse_datetime(d.get("utc_datetime")),
        "local_datetime": parse_datetime(d.get("local_datetime")),
    }
    # support both pydantic v2 and v1
    try:
        return Cuaca.model_validate(payload)  # pydantic v2
    except Exception:
        try:
            return Cuaca.parse_obj(payload)   # pydantic v1
        except Exception as e:
            raise

def parse_cuaca_matrix(raw: list) -> list:
    # raw is expected to be a list of lists: [[{...}, {...}], [{...}], ...]
    return [
        [parse_cuaca_item(item) for item in day if isinstance(item, dict)]
        for day in raw
    ]

def cuaca_to_dict(c: Cuaca) -> dict:
    def conv(v):
        if v is None:
            return None
        if isinstance(v, Enum):
            return v.value
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    return {k: conv(v) for k, v in c.model_dump().items() if v is not None} if hasattr(c, "model_dump") else {k: conv(v) for k, v in vars(c).items()}

# Ensure forward refs for ListCuaca (ListCuaca references 'Cuaca' as a string)
try:
    # pydantic v2
    ListCuaca.model_rebuild()
except Exception:
    try:
        # pydantic v1
        ListCuaca.update_forward_refs(Cuaca=Cuaca)
    except Exception:
        pass

def parse_cuaca_matrix_for_listcuaca(raw: list) -> ListCuaca:
    """Parse raw cuaca (list-of-lists) into a ListCuaca instance.

    Maps index 0 -> now, 1 -> day1, 2 -> day2. Missing days are left as None.
    """
    if not isinstance(raw, list):
        raw = []

    days = [
        [parse_cuaca_item(item) for item in day if isinstance(item, dict)]
        for day in raw
    ]

    payload = {}
    if len(days) > 0:
        payload["now"] = [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in days[0]]
    if len(days) > 1:
        payload["day1"] = [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in days[1]]
    if len(days) > 2:
        payload["day2"] = [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in days[2]]

    try:
        return ListCuaca.model_validate(payload)
    except Exception:
        try:
            return ListCuaca.parse_obj(payload)
        except Exception:
            # As a last resort, construct manually
            instance = ListCuaca()
            if "now" in payload:
                object.__setattr__(instance, "now", [parse_cuaca_item(x) if isinstance(x, dict) else x for x in payload["now"]])
            if "day1" in payload:
                object.__setattr__(instance, "day1", [parse_cuaca_item(x) if isinstance(x, dict) else x for x in payload["day1"]])
            if "day2" in payload:
                object.__setattr__(instance, "day2", [parse_cuaca_item(x) if isinstance(x, dict) else x for x in payload["day2"]])
            return instance

