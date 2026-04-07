from typing import List, Optional
from pathlib import Path
import json
from model.model_master import Provinces, Cities, Districts, Village

class LocationsService:
    def __init__(self):
        self.provinces = self._load_provinces()
        self.cities = self._load_cities()
        self.districts = self._load_districts()
        self.villages = self._load_villages()

    def _load_json_with_fallback(self, primary_path: str, fallback_path: Optional[str] = None) -> List[dict]:
        """Load JSON from primary_path, falling back to fallback_path."""
        base = Path(__file__).resolve().parent.parent

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

    def _load_provinces(self) -> List[Provinces]:
        provinces_data = self._load_json_with_fallback('tempdata/provinces.json', 'provinces.json')
        return [Provinces(**p) for p in provinces_data]

    def _load_cities(self) -> List[Cities]:
        cities_data = self._load_json_with_fallback('tempdata/cities.json', 'cities.json')
        return [Cities(**c) for c in cities_data]

    def _load_districts(self) -> List[Districts]:
        districts_data = self._load_json_with_fallback('tempdata/districts.json', 'districts.json')
        return [Districts(**d) for d in districts_data]

    def _load_villages(self) -> List[Village]:
        villages_data = self._load_json_with_fallback('tempdata/villages.json', 'villages.json')
        return [Village(**v) for v in villages_data]

    def get_provinces(self) -> List[Provinces]:
        return self.provinces

    def get_cities_by_province(self, province_id: int) -> List[Cities]:
        return [city for city in self.cities if city.province_id == province_id]

    def get_districts_by_city(self, city_id: int) -> List[Districts]:
        return [district for district in self.districts if district.city_id == city_id]

    def get_villages_by_district(self, district_id: int) -> List[Village]:
        return [village for village in self.villages if village.district_id == district_id]