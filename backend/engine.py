"""Small, explicitly experimental flood-risk model for the Amritsar demo area."""

from __future__ import annotations

import csv
import difflib
import json
import logging
import math
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import numpy as np

from backend.community import get_experiences
from backend.historical import get_historical_flood_context
from backend.india_dataset import INDIA_FLOOD_DATABASE, _norm, find_matching_localities, get_all_locations_directory

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CELL_METRES = 10
GRID_WIDTH = 800
GRID_HEIGHT = 800
GRID_CENTER = (31.6446, 74.8725)
EARTH_RADIUS_METRES = 6_371_008.8
RISK_CLASSES = ("Low", "Moderate", "High")
CITY_CENTERS = {
    "amritsar": (31.6340, 74.8723),
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "chennai": (13.0827, 80.2707),
    "bengaluru": (12.9716, 77.5946),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "kadapa": (14.4673, 78.8242),
    "cuddapah": (14.4673, 78.8242),
    "darbhanga": (26.1542, 85.8918),
    "dharbanga": (26.1542, 85.8918),
    "patna": (25.5941, 85.1376),
    "muzaffarpur": (26.1226, 85.3906),
}
# Populate CITY_CENTERS with all cities and aliases from INDIA_FLOOD_DATABASE
for _item in INDIA_FLOOD_DATABASE:
    _ck = _item["city"].lower()
    if _ck not in CITY_CENTERS:
        CITY_CENTERS[_ck] = (_item["latitude"], _item["longitude"])
    for _alias in _item.get("aliases", []):
        _ak = _alias.lower()
        if _ak not in CITY_CENTERS:
            CITY_CENTERS[_ak] = (_item["latitude"], _item["longitude"])

# Geographic centroids for all 28 Indian states and 8 union territories
STATE_CENTERS: dict[str, tuple[float, float]] = {
    "andhra pradesh": (15.9129, 79.7400),
    "arunachal pradesh": (28.2180, 94.7278),
    "assam": (26.2006, 92.9376),
    "bihar": (25.0961, 85.3131),
    "chhattisgarh": (21.2787, 81.8661),
    "goa": (15.2993, 74.1240),
    "gujarat": (22.2587, 71.1924),
    "haryana": (29.0588, 76.0856),
    "himachal pradesh": (31.1048, 77.1734),
    "jharkhand": (23.6102, 85.2799),
    "karnataka": (15.3173, 75.7139),
    "kerala": (10.8505, 76.2711),
    "madhya pradesh": (22.9734, 78.6569),
    "maharashtra": (19.7515, 75.7139),
    "manipur": (24.6637, 93.9063),
    "meghalaya": (25.4670, 91.3662),
    "mizoram": (23.1645, 92.9376),
    "nagaland": (26.1584, 94.5624),
    "odisha": (20.9517, 85.0985),
    "punjab": (31.1471, 75.3412),
    "rajasthan": (27.0238, 74.2179),
    "sikkim": (27.5330, 88.5122),
    "tamil nadu": (11.1271, 78.6569),
    "telangana": (18.1124, 79.0193),
    "tripura": (23.9408, 91.9882),
    "uttar pradesh": (26.8467, 80.9462),
    "uttarakhand": (30.0668, 79.0193),
    "west bengal": (22.9868, 87.8550),
    "andaman and nicobar islands": (11.7401, 92.6586),
    "chandigarh": (30.7333, 76.7794),
    "dadra and nagar haveli and daman and diu": (20.4283, 72.8397),
    "delhi": (28.7041, 77.1025),
    "jammu and kashmir": (33.7782, 76.5762),
    "ladakh": (34.1526, 77.5771),
    "lakshadweep": (10.5667, 72.6417),
    "puducherry": (11.9416, 79.8083),
}

AREA_CENTERS = {
    "ranjit avenue": (31.6446, 74.8725),
    "ranjit avenue, amritsar": (31.6446, 74.8725),
    "golden temple": (31.6200, 74.8765),
    "chashoti": (33.3778917, 76.2782699),
    "chishoti": (33.3778917, 76.2782699),
    "chositi": (33.3778917, 76.2782699),
}
AREA_CITIES = {
    "chashoti": "kishtwar",
    "chishoti": "kishtwar",
    "chositi": "kishtwar",
}
_FORECAST_CACHE: dict[tuple[float, float], tuple[float, dict]] = {}
_FORECAST_TTL = 15 * 60
_RISK_GRID_CACHE: dict[tuple[float, float], tuple[float, dict]] = {}
_IMD_CACHE: dict[str, tuple[float, dict]] = {}
_LOGGER = logging.getLogger(__name__)


def _to_local_xy(longitude, latitude) -> tuple[np.ndarray, np.ndarray]:
    center_latitude, center_longitude = GRID_CENTER
    x = (
        np.deg2rad(np.asarray(longitude, dtype=float) - center_longitude)
        * EARTH_RADIUS_METRES
        * math.cos(math.radians(center_latitude))
    )
    y = np.deg2rad(np.asarray(latitude, dtype=float) - center_latitude) * EARTH_RADIUS_METRES
    return x, y


def _to_geographic(x, y) -> tuple[np.ndarray, np.ndarray]:
    center_latitude, center_longitude = GRID_CENTER
    longitude = (
        center_longitude
        + np.rad2deg(np.asarray(x, dtype=float))
        / (EARTH_RADIUS_METRES * math.cos(math.radians(center_latitude)))
    )
    latitude = center_latitude + np.rad2deg(np.asarray(y, dtype=float) / EARTH_RADIUS_METRES)
    return longitude, latitude


def _build_model() -> dict[str, np.ndarray]:
    """Build the synthetic pilot terrain and cell features without geospatial binaries."""
    size = GRID_WIDTH // CELL_METRES
    columns = np.arange(size)
    rows = np.arange(size)
    xs = -GRID_WIDTH / 2 + (columns + 0.5) * CELL_METRES
    ys = GRID_HEIGHT / 2 - (rows + 0.5) * CELL_METRES
    xx, yy = np.meshgrid(xs, ys)
    normalized_x = np.linspace(-1, 1, size, dtype=np.float32)
    normalized_y = np.linspace(-1, 1, size, dtype=np.float32)
    terrain_x, terrain_y = np.meshgrid(normalized_x, normalized_y)
    bowl = np.exp(-((terrain_x + 0.28) ** 2 / 0.14 + (terrain_y - 0.12) ** 2 / 0.22))
    terrain = (231.0 + 1.9 * terrain_y + 0.8 * terrain_x - 2.5 * bowl).astype(np.float32)
    gradient_y, gradient_x = np.gradient(terrain, CELL_METRES, CELL_METRES)
    slope = np.hypot(gradient_x, gradient_y)
    elevations = terrain.ravel()
    low_reference = float(np.percentile(elevations, 20))
    basin_depth = np.maximum(0.0, low_reference - elevations)
    return {
        "x": xx.ravel(),
        "y": yy.ravel(),
        "elevation_m": elevations,
        "slope": slope.ravel(),
        "basin_capacity_m3": (0.015 + basin_depth) * CELL_METRES**2,
    }


@lru_cache(maxsize=1)
def _model_bundle() -> dict[str, np.ndarray]:
    return _build_model()


def _forecast(lat: float, lon: float) -> dict:
    key = (round(lat, 3), round(lon, 3))
    now = datetime.now(timezone.utc).timestamp()
    cached = _FORECAST_CACHE.get(key)
    if cached and now - cached[0] < _FORECAST_TTL:
        return cached[1]
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "hourly": "precipitation",
            "current": "temperature_2m,apparent_temperature,precipitation,is_day",
            "forecast_days": 2,
            "timezone": "Asia/Kolkata",
        }
    )
    try:
        with urllib.request.urlopen(url, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
        hourly = payload["hourly"]
        forecast_start = datetime.now(ZoneInfo("Asia/Kolkata")).replace(
            minute=0, second=0, microsecond=0
        ).replace(tzinfo=None)
        start_index = next(
            (
                index
                for index, hour in enumerate(hourly["time"])
                if datetime.fromisoformat(hour) >= forecast_start
            ),
            None,
        )
        if start_index is None:
            raise ValueError("Open-Meteo did not return a future forecast hour.")
        hours = hourly["time"][start_index : start_index + 6]
        rain = hourly["precipitation"][start_index : start_index + 6]
        if len(hours) < 6 or len(rain) < 6:
            raise ValueError("Open-Meteo returned fewer than six forecast hours.")
        current = payload.get("current", {})
        temperature = _finite_float(current.get("temperature_2m"))
        apparent_temperature = _finite_float(current.get("apparent_temperature"))
        current_rain = _finite_float(current.get("precipitation"))
        result = {
            "hours": [str(hour)[11:16] for hour in hours],
            "rain_mm": [round(float(value or 0), 1) for value in rain],
            "source": "Open-Meteo forecast (not an official IMD warning)",
            "simulated": False,
            "current_conditions": {
                "available": temperature is not None,
                "temperature_c": round(temperature, 1) if temperature is not None else None,
                "apparent_temperature_c": (
                    round(apparent_temperature, 1) if apparent_temperature is not None else None
                ),
                "precipitation_mm": round(current_rain, 1) if current_rain is not None else None,
                "time": current.get("time"),
                "is_day": current.get("is_day"),
                "source": "Open-Meteo current model, not an IMD station observation",
                "model_grid_location": {
                    "latitude": _finite_float(payload.get("latitude")),
                    "longitude": _finite_float(payload.get("longitude")),
                    "elevation_m": _finite_float(payload.get("elevation")),
                },
            },
        }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        result = _simulated_rainfall(lat, lon)
    _FORECAST_CACHE[key] = (now, result)
    return result


def _finite_float(value) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _imd_temperature(value) -> float | None:
    temperature = _finite_float(value)
    if temperature is None or not -80 <= temperature <= 70:
        return None
    return temperature


def _imd_city_report_fields(row: dict) -> dict:
    forecast = row.get("forecast0")
    if not forecast and isinstance(row.get("ffc"), list) and row["ffc"]:
        forecast = row["ffc"][0]
    warning = row.get("wText0")
    if not warning and isinstance(row.get("wText"), list) and row["wText"]:
        warning = row["wText"][0]
    return {
        "rainfall_24h_mm": _finite_float(row.get("rainfall")),
        "today_forecast": str(forecast or "").strip() or None,
        "today_warning": str(warning or "").strip() or None,
    }


def _simulated_rainfall(lat: float = 20.5, lon: float = 78.9, city: str = "") -> dict:
    start = datetime.now(ZoneInfo("Asia/Kolkata")).replace(minute=0, second=0, microsecond=0)
    hours = [(start + timedelta(hours=hour)).strftime("%H:%M") for hour in range(6)]

    # Deterministic city-name hash → reproducible per-city values
    name = (city or "").lower()
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    frac = (h % 1000) / 1000.0

    # Climate-zone base totals (mm in 6 hours)
    if any(k in name for k in ["mumbai", "pune", "goa", "kokan", "thane", "ratnagiri"]):
        base_mm = 62 + frac * 18
    elif any(k in name for k in ["guwahati", "assam", "shillong", "silchar", "imphal"]):
        base_mm = 74 + frac * 20
    elif any(k in name for k in ["cherrapunji", "mawsynram", "northeast", "arunachal"]):
        base_mm = 95 + frac * 25
    elif any(k in name for k in ["kolkata", "howrah", "hooghly"]):
        base_mm = 52 + frac * 16
    elif any(k in name for k in ["patna", "darbhanga", "muzaffarpur"]):
        base_mm = 48 + frac * 14
    elif any(k in name for k in ["bhubaneswar", "cuttack", "puri"]):
        base_mm = 44 + frac * 12
    elif any(k in name for k in ["chennai", "velachery", "tambaram"]):
        base_mm = 42 + frac * 14
    elif any(k in name for k in ["bengaluru", "bangalore", "bellandur"]):
        base_mm = 38 + frac * 12
    elif any(k in name for k in ["hyderabad", "secunderabad"]):
        base_mm = 34 + frac * 10
    elif any(k in name for k in ["delhi", "noida", "gurugram", "ghaziabad"]):
        base_mm = 28 + frac * 10
    elif any(k in name for k in ["lucknow", "kanpur", "varanasi", "allahabad"]):
        base_mm = 32 + frac * 12
    elif any(k in name for k in ["amritsar", "ludhiana", "chandigarh"]):
        base_mm = 14 + frac * 8
    elif any(k in name for k in ["jaipur", "jodhpur", "bikaner"]):
        base_mm = 10 + frac * 6
    elif any(k in name for k in ["ahmedabad", "surat", "vadodara"]):
        base_mm = 30 + frac * 10
    elif any(k in name for k in ["leh", "ladakh", "kargil"]):
        base_mm = 3 + frac * 3
    elif any(k in name for k in ["srinagar", "kashmir"]):
        base_mm = 18 + frac * 8
    elif any(k in name for k in ["shimla", "dehradun", "uttarakhand", "himachal"]):
        base_mm = 22 + frac * 10
    else:
        # Coordinate-based fallback
        if lon < 77 and 8 < lat < 22:
            base_mm = 52 + frac * 18      # West coast
        elif lon > 88 and lat > 22:
            base_mm = 60 + frac * 20      # Northeast / Bengal
        elif 24 < lat < 28 and 78 < lon < 88:
            base_mm = 38 + frac * 12      # Gangetic plains
        elif 12 < lat < 20 and 75 < lon < 82:
            base_mm = 32 + frac * 10      # Deccan
        elif lat > 26 and lon < 73:
            base_mm = 8 + frac * 6        # Arid NW
        elif lat > 32:
            base_mm = 12 + frac * 8       # High altitude
        else:
            base_mm = 18 + frac * 10

    base_mm = max(0.5, round(base_mm, 1))

    # Asymmetric shape: coastal = sharp spike, interior = gradual
    is_coastal = (lon < 77.5 or lon > 85 or
                  any(k in name for k in ["mumbai", "goa", "chennai", "kochi", "kolkata", "guwahati"]))
    shape = [0.08, 0.20, 0.34, 0.22, 0.11, 0.05] if is_coastal else [0.12, 0.18, 0.26, 0.22, 0.14, 0.08]
    hashes = [((h >> (i * 4)) & 0xF) / 30.0 - 0.25 for i in range(6)]
    raw = [max(0.0, round((shape[i] + hashes[i] * 0.05) * base_mm, 1)) for i in range(6)]
    raw_sum = sum(raw) or 1
    values = [round(v / raw_sum * base_mm, 1) for v in raw]

    return {
        "hours": hours,
        "rain_mm": values,
        "source": "SIMULATED regional model; live weather source unavailable",
        "simulated": True,
        "current_conditions": {
            "available": False,
            "temperature_c": None,
            "source": "Current temperature unavailable; no temperature is simulated",
        },
    }


def _predict(cells: dict[str, np.ndarray], rain: dict):
    rain_values = np.asarray(rain["rain_mm"], dtype=float)
    rate = float(np.max(rain_values))
    mean_rate = float(np.mean(rain_values))
    runoff = 0.85
    inflow_m3_hour = mean_rate / 1000 * CELL_METRES**2 * runoff
    time_to_threshold = np.clip(
        cells["basin_capacity_m3"] / max(inflow_m3_hour, 0.02), 0.1, 24
    )
    hotspot_factor = np.zeros(len(cells["x"]), dtype=float)
    hot_path = DATA / "waterlogging_spots.csv"
    if hot_path.exists():
        with hot_path.open(newline="", encoding="utf-8-sig") as stream:
            for item in csv.DictReader(stream):
                if item.get("data_status") != "SIMULATED":
                    continue
                lat, lon = float(item["latitude"]), float(item["longitude"])
                gx, gy = _to_local_xy(lon, lat)
                distance = np.hypot(cells["x"] - gx.item(), cells["y"] - gy.item())
                hotspot_factor = np.maximum(hotspot_factor, np.exp(-distance / 65))

    risk_score = (
        0.26 * np.maximum(0, 232.0 - cells["elevation_m"])
        + 0.48 * cells["basin_capacity_m3"]
        + 0.055 * rate
        + 0.65 / np.maximum(time_to_threshold, 0.15)
        + 1.6 * hotspot_factor
        - 0.8 * cells["slope"]
    )
    predicted = np.select([risk_score < 1.4, risk_score < 3.2], [0, 1], default=2)
    # Historical sample hotspots only amplify heavy-rain demo conditions; sample locations are unverified.
    active_hotspots = (hotspot_factor >= 0.7) & (rate >= 8.0)
    predicted[active_hotspots] = 2

    # Run 100 perturbed rainfall scenarios to bound risk-class uncertainty.
    rng = np.random.default_rng(104)
    factors = rng.uniform(0.65, 1.45, 100)
    scenario_scores = (
        risk_score[np.newaxis, :]
        + 0.055 * rate * (factors[:, np.newaxis] - 1)
        + 0.65 / np.maximum(time_to_threshold[np.newaxis, :] / factors[:, np.newaxis], 0.15)
        - 0.65 / np.maximum(time_to_threshold[np.newaxis, :], 0.15)
    )
    scenario_predictions = np.select(
        [scenario_scores < 1.4, scenario_scores < 3.2], [0, 1], default=2
    )
    scenario_predictions[:, active_hotspots] = 2
    low, high = np.quantile(scenario_predictions, [0.1, 0.9], axis=0)
    confidence = np.clip(
        55 + np.min(np.abs(risk_score[:, np.newaxis] - [1.4, 3.2]), axis=1) * 15,
        55,
        95,
    )
    return predicted, confidence, low, high, time_to_threshold, rate


def _class_name(index: int) -> str:
    return RISK_CLASSES[index]


def get_risk_grid(lat: float = GRID_CENTER[0], lon: float = GRID_CENTER[1]) -> dict:
    key = (round(lat, 3), round(lon, 3))
    now = datetime.now(timezone.utc).timestamp()
    cached = _RISK_GRID_CACHE.get(key)
    if cached and now - cached[0] < _FORECAST_TTL:
        return cached[1]
    x, y = _to_local_xy(lon, lat)
    if not (
        -GRID_WIDTH / 2 <= x.item() <= GRID_WIDTH / 2
        and -GRID_HEIGHT / 2 <= y.item() <= GRID_HEIGHT / 2
    ):
        return {
            "type": "FeatureCollection",
            "features": [],
            "data_status": "NO LOCAL TERRAIN COVERAGE",
            "method": "The synthetic pilot grid covers Ranjit Avenue, Amritsar only.",
            "forecast_source": "No location-specific risk grid available",
        }
    cells = _model_bundle()
    rain = _forecast(lat, lon)
    predicted, confidence, low, high, _, rate = _predict(cells, rain)
    features = []
    grid_size = GRID_WIDTH // CELL_METRES
    summary_cells = 50 // CELL_METRES
    risk_grid = predicted.reshape(grid_size, grid_size)
    confidence_grid = confidence.reshape(grid_size, grid_size)
    low_grid = low.reshape(grid_size, grid_size)
    high_grid = high.reshape(grid_size, grid_size)
    for gy in range(GRID_HEIGHT // 50):
        for gx in range(GRID_WIDTH // 50):
            row_slice = slice(gy * summary_cells, (gy + 1) * summary_cells)
            column_slice = slice(gx * summary_cells, (gx + 1) * summary_cells)
            cell_slice = np.s_[row_slice, column_slice]
            index = int(np.rint(np.mean(risk_grid[cell_slice])))
            average_confidence = float(np.mean(confidence_grid[cell_slice]))
            range_low = float(np.mean(low_grid[cell_slice]))
            range_high = float(np.mean(high_grid[cell_slice]))
            min_x = -GRID_WIDTH / 2 + gx * 50
            max_y = GRID_HEIGHT / 2 - gy * 50
            polygon_x = [min_x, min_x + 50, min_x + 50, min_x, min_x]
            polygon_y = [max_y - 50, max_y - 50, max_y, max_y, max_y - 50]
            longitudes, latitudes = _to_geographic(polygon_x, polygon_y)
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [float(point_lon), float(point_lat)]
                            for point_lon, point_lat in zip(longitudes, latitudes)
                        ]],
                    },
                    "properties": {
                        "risk": _class_name(index),
                        "risk_index": index,
                        "confidence_pct": round(average_confidence, 1),
                        "class_range": [
                            _class_name(max(0, min(2, int(math.floor(range_low))))),
                            _class_name(max(0, min(2, int(math.ceil(range_high))))),
                        ],
                        "rain_intensity_mm_h": round(rate, 1),
                        "grid_resolution_m": CELL_METRES,
                        "display_cell_m": 50,
                    },
                }
            )
    result = {
        "type": "FeatureCollection",
        "features": features,
        "data_status": _terrain_data_status(),
        "method": "Synthetic terrain and transparent heuristic on 10 m cells; 50 m summaries",
        "forecast_source": rain["source"],
        "location": {"lat": lat, "lon": lon},
    }
    _RISK_GRID_CACHE[key] = (now, result)
    return result


def _terrain_data_status() -> str:
    return "SIMULATED TERRAIN · generated in memory; not measured elevation"


def _imd_city_observation(city: str | None) -> dict:
    city_name = (city or "").strip()
    if not city_name:
        return {"available": False, "source": "IMD city observation unavailable for this location"}
    cache_key = city_name.casefold()
    now = datetime.now(timezone.utc).timestamp()
    cached = _IMD_CACHE.get(cache_key)
    if cached and now - cached[0] < 10 * 60:
        return cached[1]

    base_url = "https://city.imd.gov.in/citywx/responsive/api"
    headers = {
        "User-Agent": "Mozilla/5.0 AURA-Flood experimental weather viewer",
        "Referer": "https://city.imd.gov.in/citywx/responsive/",
        "Origin": "https://city.imd.gov.in",
        "Accept": "application/json, text/plain, */*",
    }
    try:
        query = urllib.parse.urlencode({"query": city_name})
        search_request = urllib.request.Request(f"{base_url}/search.php?{query}", headers=headers)
        with urllib.request.urlopen(search_request, timeout=5) as response:
            search = json.loads(response.read().decode("utf-8"))
        stations = search.get("data") or []
        if not stations:
            result = {"available": False, "source": f"No IMD city station found for {city_name}"}
        else:
            normalized_city = city_name.casefold()
            station = next(
                (item for item in stations if str(item.get("station", "")).casefold() == normalized_city),
                stations[0],
            )
            station_id = str(station["station_id"])
            body = urllib.parse.urlencode({"ID": station_id}).encode("ascii")
            observation_request = urllib.request.Request(
                f"{base_url}/fetchCity_static.php",
                data=body,
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(observation_request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, list) or not payload:
                result = {"available": False, "source": f"IMD city observations unavailable for {city_name}"}
            else:
                row = payload[0]
                maximum = _imd_temperature(row.get("max"))
                minimum = _imd_temperature(row.get("min"))
                report_fields = _imd_city_report_fields(row)
                result = {
                    "available": any(
                        value is not None
                        for value in (
                            maximum,
                            minimum,
                            report_fields["rainfall_24h_mm"],
                            report_fields["today_forecast"],
                            report_fields["today_warning"],
                        )
                    ),
                    "station_id": station_id,
                    "station": row.get("station") or station.get("station") or city_name,
                    "date": row.get("dat"),
                    "updated_at": row.get("updat"),
                    "observed_max_c": maximum,
                    "observed_min_c": minimum,
                    **report_fields,
                    "source": "India Meteorological Department (IMD) city weather report",
                    "note": "Includes the city forecast and rainfall observed over the previous 24 hours through 0830 IST; it is not an instantaneous rain observation.",
                }
    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        _LOGGER.warning("Could not retrieve IMD observations for %s: %s", city_name, exc)
        result = {"available": False, "source": f"IMD city observations unavailable for {city_name}"}
    _IMD_CACHE[cache_key] = (now, result)
    return result


def _nearest_city_name(lat: float, lon: float) -> str | None:
    nearest = min(
        CITY_CENTERS.items(),
        key=lambda item: (item[1][0] - lat) ** 2 + (item[1][1] - lon) ** 2,
    )
    distance_squared = (nearest[1][0] - lat) ** 2 + (nearest[1][1] - lon) ** 2
    return nearest[0].title() if distance_squared <= 0.4**2 else None


def get_rainfall(lat: float, lon: float, city: str | None = None) -> dict:
    rain = _forecast(lat, lon)
    return {
        **rain,
        "imd_observation": _imd_city_observation(city or _nearest_city_name(lat, lon)),
        "location": {"lat": lat, "lon": lon},
        "total_mm": round(sum(rain["rain_mm"]), 1),
        "data_status": "SIMULATED" if rain["simulated"] else "LIVE FORECAST",
        "notice": "Experimental model output, not an official warning.",
    }


def get_hotspots() -> dict:
    path = DATA / "waterlogging_spots.csv"
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["latitude"] = float(row["latitude"])
        row["longitude"] = float(row["longitude"])
    reports = get_experiences()
    community_spots = [
        {
            "id": f"community-{report['id']}",
            "name": report["location_label"],
            "city": report["city"],
            "state": report["state"],
            "latitude": report["latitude"],
            "longitude": report["longitude"],
            "kind": report["category"],
            "experience": report["experience"],
            "data_status": report["data_status"],
            "created_at": report["created_at"],
        }
        for report in reports
    ]
    return {
        "spots": [*community_spots, *rows],
        "data_status": (
            f"{len(community_spots)} community reports · unverified; "
            "bundled sample locations · SIMULATED"
        ),
    }


def _resolve_coordinates(lat, lon, state, city, area) -> tuple[float, float, str, bool]:
    if lat is not None and lon is not None:
        if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Enter valid latitude and longitude coordinates.")
        # Proximity lookup to nearest known locality in India flood database
        prox_matches = find_matching_localities(lat=lat, lon=lon)
        if prox_matches:
            near = prox_matches[0]
            dist_sq = (near["latitude"] - lat) ** 2 + (near["longitude"] - lon) ** 2
            if dist_sq <= 0.45**2:  # within ~50 km
                label = f"{near['locality']}, {near['city']} ({near['state']}) · Device Location"
                return lat, lon, label, False
        city_nearby = _nearest_city_name(lat, lon)
        if city_nearby:
            return lat, lon, f"Near {city_nearby} · Coordinates ({lat:.4f}, {lon:.4f})", False
        return lat, lon, f"Selected coordinates ({lat:.5f}, {lon:.5f})", False
    if (lat is None) != (lon is None):
        raise ValueError("Latitude and longitude must be supplied together.")
    
    area_key = (area or "").strip().lower()
    expected_city = AREA_CITIES.get(area_key, "amritsar")
    if area_key in AREA_CENTERS and (not city or city.strip().lower() == expected_city):
        point = AREA_CENTERS[area_key]
        approximate = area_key in AREA_CITIES
        suffix = " (approximate hamlet point)" if approximate else ""
        return point[0], point[1], f"{area.strip()}, {city or expected_city.title()}{suffix}", approximate

    # 1. Check nationwide comprehensive India flood & drainage dataset first
    matches = find_matching_localities(query_text=area, city=city, state=state, allow_state_fallback=True)
    if matches:
        first = matches[0]
        resolved_city = first["city"]
        resolved_state = first.get("state") or state or ""
        if not city and state:
            label = f"{state.strip().title()} (State Overview · {resolved_city} Basin)"
            state_key = _norm(state)
            if state_key in STATE_CENTERS:
                sc = STATE_CENTERS[state_key]
                return float(sc[0]), float(sc[1]), label, False
            return float(first["latitude"]), float(first["longitude"]), label, False
        display_parts = [part for part in (area, resolved_city, resolved_state) if part]
        return float(first["latitude"]), float(first["longitude"]), ", ".join(display_parts), False

    # 2. Check exact or alias match in CITY_CENTERS
    city_key = (city or "").strip().lower()
    if city_key:
        if city_key in CITY_CENTERS:
            point = CITY_CENTERS[city_key]
            display = ", ".join(part for part in (area, city.strip().title(), state) if part)
            return point[0], point[1], display or city.title(), False

        # 3. Fuzzy matching for typos or spelling variants (e.g., Dharbanga -> Darbhanga)
        close_city_matches = difflib.get_close_matches(city_key, list(CITY_CENTERS.keys()), n=1, cutoff=0.72)
        if close_city_matches:
            matched_key = close_city_matches[0]
            point = CITY_CENTERS[matched_key]
            display = ", ".join(part for part in (area, matched_key.title(), state) if part)
            return point[0], point[1], display, False

    # Check state alone fallback if not in INDIA_FLOOD_DATABASE
    if state and not city:
        state_key = _norm(state)
        if state_key in STATE_CENTERS:
            sc = STATE_CENTERS[state_key]
            return float(sc[0]), float(sc[1]), f"{state.strip().title()} (State Overview)", False

    # 4. Attempt online geocoding for unrecognized towns/villages
    if city:
        try:
            query = urllib.parse.urlencode({"name": city, "count": 1, "countryCode": "IN", "language": "en", "format": "json"})
            with urllib.request.urlopen(
                "https://geocoding-api.open-meteo.com/v1/search?" + query, timeout=3
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
            result = payload.get("results", [])[0]
            display = ", ".join(part for part in (area, result.get("name"), state) if part)
            return float(result["latitude"]), float(result["longitude"]), display, True
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError):
            # Offline fallback for small villages without hardcoded points: use state centroid while preserving city name
            state_key = _norm(state or "")
            if state_key in STATE_CENTERS:
                sc = STATE_CENTERS[state_key]
                display = ", ".join(part for part in (area, city.strip().title(), state) if part)
                return sc[0], sc[1], f"{display} (offline regional estimate)", True
            display = ", ".join(part for part in (area, city, state) if part)
            return (
                GRID_CENTER[0],
                GRID_CENTER[1],
                f"{display} (offline fallback coordinates)",
                True,
            )
    raise ValueError("Choose device location or enter a city or state.")


def resolve_location(lat, lon, state, city, area) -> dict:
    point_lat, point_lon, label, approximate = _resolve_coordinates(lat, lon, state, city, area)
    area_key = (area or "").strip().lower()
    area_geocoded = area_key in AREA_CENTERS
    if area and area_geocoded and area_key in AREA_CITIES:
        weather_location_note = (
            "Location uses an approximate OpenStreetMap hamlet point; "
            "the temperature is a regional model-grid estimate, not a village observation."
        )
    elif area and not area_geocoded and lat is None and lon is None:
        weather_location_note = (
            f"'{area}' localized; weather uses {city or 'city'} regional grid coordinates."
        )
    else:
        weather_location_note = (
            "Temperature is a numerical weather-model estimate for a nearby grid cell, "
            "not an on-site or station observation."
        )

    inferred_city = (city or "").strip()
    inferred_state = (state or "").strip()
    if not inferred_city:
        prox = find_matching_localities(lat=point_lat, lon=point_lon)
        if prox:
            inferred_city = prox[0]["city"]
            if not inferred_state:
                inferred_state = prox[0].get("state", "")
        else:
            inferred_city = _nearest_city_name(point_lat, point_lon) or ""

    if not inferred_state and inferred_city:
        c_norm = _norm(inferred_city)
        for item in INDIA_FLOOD_DATABASE:
            if _norm(item["city"]) == c_norm or any(_norm(a) == c_norm for a in item.get("aliases", [])):
                inferred_state = item["state"]
                break

    is_state_level = not city and bool(state)

    return {
        "lat": point_lat,
        "lon": point_lon,
        "city": inferred_city,
        "state": inferred_state,
        "area": area or "",
        "weather_location_note": weather_location_note,
        "label": label,
        "approximate": approximate,
        "is_state_level": is_state_level,
    }


def get_alert(location: dict) -> dict:
    lat, lon = location["lat"], location["lon"]
    unresolved = "not geocoded" in location.get("label", "")
    rain = _simulated_rainfall(lat, lon, location.get("city", "")) if unresolved else {
        **_forecast(lat, lon),
        "imd_observation": _imd_city_observation(location.get("city")),
    }
    if rain.get("current_conditions"):
        rain["current_conditions"]["location_note"] = location.get("weather_location_note")

    historical_context = get_historical_flood_context(location, rain)
    clogging_info = historical_context.get("clogging_assessment", {})
    clog_status = clogging_info.get("status", "CLEAR")

    point_x, point_y = _to_local_xy(lon, lat)
    inside_pilot = (
        abs(point_x.item()) <= GRID_WIDTH / 2
        and abs(point_y.item()) <= GRID_HEIGHT / 2
    )
    if inside_pilot and not unresolved:
        cells = _model_bundle()
        predicted, confidence, low, high, time_to_threshold, _ = _predict(cells, rain)
        distances = (cells["x"] - point_x.item()) ** 2 + (cells["y"] - point_y.item()) ** 2
        selected = int(np.argmin(distances))
        index = int(predicted[selected])
        risk_confidence = float(confidence[selected])
        class_low = max(0, int(math.floor(low[selected])))
        class_high = min(2, int(math.ceil(high[selected])))
        threshold = float(time_to_threshold[selected])
        risk = _class_name(index)
        confidence_pct = round(risk_confidence, 1)
        uncertainty = {
            "risk_range": [_class_name(class_low), _class_name(class_high)],
            "scenarios": 100,
            "method": "10th–90th percentile from perturbed rainfall scenarios",
        }
        message = (
            f"{clogging_info.get('status_badge', 'Terrain Screening')}: {clogging_info.get('summary', 'Screening evaluated.')}"
        )
    else:
        # Nationwide India Hydrological & Drainage Assessment
        # Use dynamic, calibrated multi-factor calculation from clogging_assessment
        risk = clogging_info.get("risk_class", "Moderate")
        threshold = clogging_info.get("time_to_threshold_hours", 2.0)
        confidence_pct = clogging_info.get("screening_score", 75.0)
        risk_range = clogging_info.get("risk_range", ["Low", "High"])

        uncertainty = {
            "risk_range": risk_range,
            "scenarios": 100,
            "method": "Multi-factor hydrological synthesis: 100 perturbed rainfall scenarios evaluated against terrain elevation, drainage network capacity, and resident reports",
        }
        message = (
            f"{clogging_info.get('status_badge', 'Civic Drainage Evaluation')}: {clogging_info.get('summary', 'Drainage and flood evaluation active.')}"
        )

    return {
        "location": {
            "label": location["label"],
            "city": location.get("city"),
            "lat": None if unresolved else lat,
            "lon": None if unresolved else lon,
            "approximate": location.get("approximate", False),
            "geocoded": not unresolved,
            "weather_location_note": location.get("weather_location_note"),
        },
        "risk": risk,
        "screening_available": True,
        "time_to_threshold_hours": round(threshold, 1) if threshold is not None else None,
        "confidence_pct": confidence_pct,
        "uncertainty": uncertainty,
        "rainfall": rain,
        "historical_context": historical_context,
        "data_status": {
            "forecast": "SIMULATED" if rain["simulated"] else "LIVE FORECAST",
            "terrain": _terrain_data_status(),
            "nationwide_coverage": "28 States & 8 Union Territories Active",
        },
        "message": message,
        "notice": "Not an official forecast or emergency warning. Follow IMD / NDMA advisories.",
    }


def get_evaluation() -> dict:
    path = DATA / "evaluation_sample.csv"
    with path.open(newline="", encoding="utf-8-sig") as stream:
        events = list(csv.DictReader(stream))
    correct = sum(event["predicted_risk"] == event["observed_risk"] for event in events)
    return {
        "data_status": "SIMULATED evaluation examples; not measured model performance",
        "metrics": {
            "events": len(events),
            "accuracy_pct": round(correct / len(events) * 100, 1) if events else 0.0,
        },
        "events": events,
        "limitations": [
            "All included rainfall, terrain, hotspot and event samples are calibrated demo data, not official or independently validated observations.",
            "The Amritsar pilot grid uses a transparent synthetic heuristic; it is not a trained or validated flood-prediction model.",
            "Open-Meteo provides numerical weather forecasts, not IMD warnings; an official IMD warning feed is not integrated.",
            "Instantaneous temperature is Open-Meteo model data, not an IMD station observation. IMD's city report supplies today's observed high and low, not a live instant temperature; station observations may be delayed.",
            "The 10 m computational grid is not proof of 10 m terrain accuracy. Terrain is generated synthetically in memory; no real SRTM elevation file is used.",
            "Drainage capacity, land cover, sewer condition, road closures and municipal response are synthesized from documented disaster records and resident reports.",
            "Nationwide coverage spans all 28 States and 8 Union Territories with historical flood context and chronic drainage chokepoints.",
            "Do not use this prototype for travel, evacuation or emergency decisions. Follow IMD, NDMA and local authorities.",
        ],
    }
