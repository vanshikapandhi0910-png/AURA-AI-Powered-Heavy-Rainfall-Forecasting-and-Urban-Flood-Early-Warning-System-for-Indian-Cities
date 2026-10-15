"""Small, explicitly experimental flood-risk model for the Amritsar demo area."""

from __future__ import annotations

import csv
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

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform as transform_coordinates
from shapely.geometry import box
from sklearn.ensemble import RandomForestClassifier

import difflib
from backend.community import get_experiences
from backend.historical import get_historical_flood_context
from backend.india_dataset import INDIA_FLOOD_DATABASE, _norm, find_matching_localities, get_all_locations_directory

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TERRAIN_FILE = DATA / "demo_terrain.tif"
CRS = "EPSG:32643"
CELL_METRES = 10
GRID_WIDTH = 800
GRID_HEIGHT = 800
GRID_CENTER = (31.6446, 74.8725)
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


def _make_simulated_terrain() -> None:
    """Create a clearly labeled synthetic GeoTIFF when real terrain is absent."""
    DATA.mkdir(parents=True, exist_ok=True)
    if TERRAIN_FILE.exists():
        return
    size = GRID_WIDTH // CELL_METRES
    x = np.linspace(-1, 1, size, dtype=np.float32)
    y = np.linspace(-1, 1, size, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    bowl = np.exp(-((xx + 0.28) ** 2 / 0.14 + (yy - 0.12) ** 2 / 0.22))
    terrain = (231.0 + 1.9 * yy + 0.8 * xx - 2.5 * bowl).astype(np.float32)
    # UTM coordinates for the demo-area raster; the elevation values are synthetic.
    center_x, center_y = gpd.GeoSeries.from_xy(
        [GRID_CENTER[1]], [GRID_CENTER[0]], crs="EPSG:4326"
    ).to_crs(CRS).iloc[0].coords[0]
    transform = from_origin(
        center_x - GRID_WIDTH / 2, center_y + GRID_HEIGHT / 2, CELL_METRES, CELL_METRES
    )
    with rasterio.open(
        TERRAIN_FILE,
        "w",
        driver="GTiff",
        height=size,
        width=size,
        count=1,
        dtype="float32",
        crs=CRS,
        transform=transform,
        compress="deflate",
        tags={
            "source": "SIMULATED demo terrain; replace with a georeferenced SRTM GeoTIFF",
            "units": "metres",
        },
    ) as dataset:
        dataset.write(terrain, 1)
        dataset.update_tags(
            source="SIMULATED demo terrain; replace with a georeferenced SRTM GeoTIFF",
            units="metres",
        )


def _build_model():
    """Create 10 m cells, sample terrain, and fit a small synthetic training model."""
    _make_simulated_terrain()
    center = gpd.GeoSeries.from_xy(
        [GRID_CENTER[1]], [GRID_CENTER[0]], crs="EPSG:4326"
    ).to_crs(CRS).iloc[0].coords[0]
    center_x, center_y = center
    min_x = center_x - GRID_WIDTH / 2
    max_y = center_y + GRID_HEIGHT / 2
    columns = np.arange(GRID_WIDTH // CELL_METRES)
    rows = np.arange(GRID_HEIGHT // CELL_METRES)
    xs = min_x + (columns + 0.5) * CELL_METRES
    ys = max_y - (rows + 0.5) * CELL_METRES
    xx, yy = np.meshgrid(xs, ys)
    cells = gpd.GeoDataFrame(
        {"x": xx.ravel(), "y": yy.ravel()},
        geometry=[
            box(
                x - CELL_METRES / 2,
                y - CELL_METRES / 2,
                x + CELL_METRES / 2,
                y + CELL_METRES / 2,
            )
            for y in ys
            for x in xs
        ],
        crs=CRS,
    )

    with rasterio.open(TERRAIN_FILE) as dem:
        if dem.crs is None:
            raise ValueError("The terrain GeoTIFF must have a valid coordinate reference system.")
        if dem.crs.to_string() != CRS:
            sample_x, sample_y = transform_coordinates(
                CRS, dem.crs, cells["x"].tolist(), cells["y"].tolist()
            )
        else:
            sample_x, sample_y = cells["x"].tolist(), cells["y"].tolist()
        sampled = np.ma.vstack(list(dem.sample(zip(sample_x, sample_y), masked=True)))
        elevations = sampled.filled(np.nan)[:, 0].astype(np.float32)
        if not np.isfinite(elevations).all():
            raise ValueError(
                "The terrain GeoTIFF must contain valid elevation data across the full Ranjit Avenue demo grid."
            )
        raster = dem.read(1, masked=True).filled(np.nan)
        pixel_x = abs(dem.transform.a)
        pixel_y = abs(dem.transform.e)
        gradient_y, gradient_x = np.gradient(raster, pixel_y, pixel_x)
        slopes = np.hypot(gradient_x, gradient_y)
        slope_values = np.fromiter(
            (
                slopes[min(max(int((dem.transform.f - y) / pixel_y), 0), slopes.shape[0] - 1),
                        min(max(int((x - dem.transform.c) / pixel_x), 0), slopes.shape[1] - 1)]
                for x, y in zip(sample_x, sample_y)
            ),
            dtype=np.float32,
        )

    low_reference = float(np.percentile(elevations, 20))
    basin_depth = np.maximum(0.0, low_reference - elevations)
    capacity_m3 = (0.015 + basin_depth) * CELL_METRES**2
    cells["elevation_m"] = elevations
    cells["slope"] = slope_values
    cells["basin_capacity_m3"] = capacity_m3

    # Synthetic training labels encode a transparent heuristic, not verified flood events.
    rng = np.random.default_rng(42)
    count = 6000
    training = np.column_stack(
        [
            rng.uniform(228, 235, count),
            rng.uniform(0, 0.2, count),
            rng.uniform(0, 4, count),
            rng.uniform(0, 60, count),
            rng.uniform(0.05, 12, count),
            rng.uniform(0, 1, count),
        ]
    )
    risk_index = (
        0.26 * np.maximum(0, 232.0 - training[:, 0])
        + 0.48 * training[:, 2]
        + 0.055 * training[:, 3]
        + 0.65 / np.maximum(training[:, 4], 0.15)
        + 1.6 * training[:, 5]
        - 0.8 * training[:, 1]
    )
    labels = np.select([risk_index < 1.4, risk_index < 3.2], [0, 1], default=2)
    model = RandomForestClassifier(
        n_estimators=48, max_depth=9, min_samples_leaf=3, random_state=42, n_jobs=1
    )
    model.fit(training, labels)
    return cells, model, {"x": center_x, "y": center_y, "bounds": (min_x, max_y - GRID_HEIGHT, min_x + GRID_WIDTH, max_y)}


@lru_cache(maxsize=1)
def _model_bundle():
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
        result = _simulated_rainfall()
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


def _simulated_rainfall() -> dict:
    start = datetime.now(ZoneInfo("Asia/Kolkata")).replace(minute=0, second=0, microsecond=0)
    hours = [(start + timedelta(hours=hour)).strftime("%H:%M") for hour in range(6)]
    # A reproducible demo shower, explicitly marked synthetic in every response.
    values = [1.2, 3.8, 8.4, 12.0, 7.1, 2.6]
    return {
        "hours": hours,
        "rain_mm": values,
        "source": "SIMULATED sample forecast; live weather source unavailable",
        "simulated": True,
        "current_conditions": {
            "available": False,
            "temperature_c": None,
            "source": "Current temperature unavailable; no temperature is simulated",
        },
    }


def _predict(cells: gpd.GeoDataFrame, model: RandomForestClassifier, rain: dict):
    rain_values = np.asarray(rain["rain_mm"], dtype=float)
    rate = float(np.max(rain_values))
    mean_rate = float(np.mean(rain_values))
    runoff = 0.85
    inflow_m3_hour = mean_rate / 1000 * CELL_METRES**2 * runoff
    time_to_threshold = np.clip(
        cells["basin_capacity_m3"].to_numpy() / max(inflow_m3_hour, 0.02), 0.1, 24
    )
    hotspot_factor = np.zeros(len(cells), dtype=float)
    hot_path = DATA / "waterlogging_spots.csv"
    if hot_path.exists():
        with hot_path.open(newline="", encoding="utf-8-sig") as stream:
            for item in csv.DictReader(stream):
                if item.get("data_status") != "SIMULATED":
                    continue
                lat, lon = float(item["latitude"]), float(item["longitude"])
                gx, gy = transform_coordinates("EPSG:4326", CRS, [lon], [lat])
                distance = np.hypot(cells["x"].to_numpy() - gx[0], cells["y"].to_numpy() - gy[0])
                hotspot_factor = np.maximum(hotspot_factor, np.exp(-distance / 65))

    features = np.column_stack(
        [
            cells["elevation_m"].to_numpy(),
            cells["slope"].to_numpy(),
            cells["basin_capacity_m3"].to_numpy(),
            np.full(len(cells), rate),
            time_to_threshold,
            hotspot_factor,
        ]
    )
    probabilities = model.predict_proba(features)
    # Historical sample hotspots only amplify heavy-rain demo conditions; sample locations are unverified.
    active_hotspots = (hotspot_factor >= 0.7) & (rate >= 8.0)
    # Run 100 perturbed rainfall scenarios to bound risk-class uncertainty.
    rng = np.random.default_rng(104)
    factors = rng.uniform(0.65, 1.45, 100)
    scenarios = np.tile(features, (100, 1))
    scenarios[:, 3] *= np.repeat(factors, len(cells))
    scenarios[:, 4] /= np.repeat(factors, len(cells))
    scenario_predictions = model.predict(scenarios).reshape(100, len(cells))
    scenario_predictions[:, active_hotspots] = 2
    low, high = np.quantile(scenario_predictions, [0.1, 0.9], axis=0)
    predicted = np.argmax(probabilities, axis=1)
    predicted[active_hotspots] = 2
    confidence = probabilities[np.arange(len(cells)), predicted] * 100
    return predicted, confidence, low, high, time_to_threshold, rate


def _class_name(index: int) -> str:
    return RISK_CLASSES[index]


def get_risk_grid(lat: float = GRID_CENTER[0], lon: float = GRID_CENTER[1]) -> dict:
    key = (round(lat, 3), round(lon, 3))
    now = datetime.now(timezone.utc).timestamp()
    cached = _RISK_GRID_CACHE.get(key)
    if cached and now - cached[0] < _FORECAST_TTL:
        return cached[1]
    x, y = transform_coordinates("EPSG:4326", CRS, [lon], [lat])
    center_x, center_y = transform_coordinates(
        "EPSG:4326", CRS, [GRID_CENTER[1]], [GRID_CENTER[0]]
    )
    min_x = center_x[0] - GRID_WIDTH / 2
    max_x = center_x[0] + GRID_WIDTH / 2
    min_y = center_y[0] - GRID_HEIGHT / 2
    max_y = center_y[0] + GRID_HEIGHT / 2
    if not (min_x <= x[0] <= max_x and min_y <= y[0] <= max_y):
        return {
            "type": "FeatureCollection",
            "features": [],
            "data_status": "NO LOCAL TERRAIN COVERAGE",
            "method": "The terrain-backed pilot grid covers Ranjit Avenue, Amritsar only.",
            "forecast_source": "No location-specific risk grid available",
        }
    cells, model, _ = _model_bundle()
    rain = _forecast(lat, lon)
    predicted, confidence, low, high, _, rate = _predict(cells, model, rain)
    cells = cells.copy()
    cells["risk_index"] = predicted
    cells["confidence_pct"] = confidence
    cells["range_low"] = low
    cells["range_high"] = high
    # Display a 50 m summary grid to keep the mobile GeoJSON payload compact.
    cells["gx"] = np.floor((cells["x"] - (cells["x"].min() - 5)) / 50).astype(int)
    cells["gy"] = np.floor((cells["y"].max() + 5 - cells["y"]) / 50).astype(int)
    grouped = cells.dissolve(by=["gx", "gy"], as_index=False, aggfunc={
        "risk_index": lambda values: int(np.rint(np.mean(values))),
        "confidence_pct": "mean",
        "range_low": "mean",
        "range_high": "mean",
    })
    geographic = grouped.to_crs("EPSG:4326")
    features = []
    for row in geographic.itertuples():
        index = int(row.risk_index)
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(gpd.GeoSeries([row.geometry], crs="EPSG:4326").to_json())["features"][0]["geometry"],
                "properties": {
                    "risk": _class_name(index),
                    "risk_index": index,
                    "confidence_pct": round(float(row.confidence_pct), 1),
                    "class_range": [
                        _class_name(max(0, min(2, int(math.floor(row.range_low))))),
                        _class_name(max(0, min(2, int(math.ceil(row.range_high))))),
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
        "method": "10 m internal cells; 50 m summaries for lightweight display",
        "forecast_source": rain["source"],
        "location": {"lat": lat, "lon": lon},
    }
    _RISK_GRID_CACHE[key] = (now, result)
    return result


def _terrain_data_status() -> str:
    if not TERRAIN_FILE.exists():
        return "SIMULATED TERRAIN"
    with rasterio.open(TERRAIN_FILE) as dataset:
        source = dataset.tags().get("source", "")
    if source.upper().startswith("SIMULATED"):
        return "SIMULATED TERRAIN"
    if source:
        return f"Local terrain GeoTIFF · source: {source}"
    return "UNVERIFIED LOCAL TERRAIN · GeoTIFF has no source metadata"


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
    matches = find_matching_localities(query_text=area, city=city, state=state)
    if matches:
        first = matches[0]
        resolved_city = first["city"]
        display_parts = [part for part in (area, resolved_city, first.get("state") or state) if part]
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
    raise ValueError("Choose device location or enter a city and state.")


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
    return {
        "lat": point_lat,
        "lon": point_lon,
        "city": city or _nearest_city_name(point_lat, point_lon),
        "state": state or "",
        "area": area or "",
        "weather_location_note": weather_location_note,
        "label": label,
        "approximate": approximate,
    }


def get_alert(location: dict) -> dict:
    lat, lon = location["lat"], location["lon"]
    unresolved = "not geocoded" in location.get("label", "")
    rain = _simulated_rainfall() if unresolved else {
        **_forecast(lat, lon),
        "imd_observation": _imd_city_observation(location.get("city")),
    }
    if rain.get("current_conditions"):
        rain["current_conditions"]["location_note"] = location.get("weather_location_note")

    historical_context = get_historical_flood_context(location, rain)
    clogging_info = historical_context.get("clogging_assessment", {})
    clog_status = clogging_info.get("status", "CLEAR")

    point_x, point_y = transform_coordinates("EPSG:4326", CRS, [lon], [lat])
    center_x, center_y = transform_coordinates(
        "EPSG:4326", CRS, [GRID_CENTER[1]], [GRID_CENTER[0]]
    )
    inside_pilot = (
        abs(point_x[0] - center_x[0]) <= GRID_WIDTH / 2
        and abs(point_y[0] - center_y[0]) <= GRID_HEIGHT / 2
    )
    if inside_pilot and not unresolved:
        cells, model, _ = _model_bundle()
        predicted, confidence, low, high, time_to_threshold, _ = _predict(cells, model, rain)
        x_list, y_list = transform_coordinates(
            CRS, "EPSG:4326", cells["x"].tolist(), cells["y"].tolist()
        )
        distances = (
            (np.asarray(x_list) - lon) ** 2 * np.cos(np.deg2rad(lat)) ** 2
            + (np.asarray(y_list) - lat) ** 2
        )
        inside = (
            (
                cells["x"].to_numpy()
                >= center_x[0] - GRID_WIDTH / 2
            )
            & (cells["x"].to_numpy() <= center_x[0] + GRID_WIDTH / 2)
            & (cells["y"].to_numpy() >= center_y[0] - GRID_HEIGHT / 2)
            & (cells["y"].to_numpy() <= center_y[0] + GRID_HEIGHT / 2)
        )
        selected = int(np.argmin(np.where(inside, distances, np.inf)))
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
        # Use the new alert_level (RED/YELLOW/GREEN) from the alert engine
        alert_level = historical_context.get("alert_level", "GREEN")
        if alert_level == "RED" or clog_status == "CLOGGED":
            risk = "High"
            threshold = 0.5
            confidence_pct = 94.0
            risk_range = ["Moderate", "High"]
        elif alert_level == "YELLOW" or clog_status in ("CAUTION", "PRONE_TO_CLOGGING", "WATCH"):
            risk = "Moderate"
            threshold = 2.0
            confidence_pct = 88.5
            risk_range = ["Low", "High"]
        else:
            risk = "Low"
            threshold = 6.0
            confidence_pct = 91.0
            risk_range = ["Low", "Moderate"]


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
    frame = pd.read_csv(path)
    return {
        "data_status": "SIMULATED evaluation examples; not measured model performance",
        "metrics": {
            "events": int(len(frame)),
            "accuracy_pct": round(float((frame["predicted_risk"] == frame["observed_risk"]).mean() * 100), 1),
        },
        "events": frame.to_dict(orient="records"),
        "limitations": [
            "All included rainfall, terrain, hotspot and event samples are calibrated demo data, not official or independently validated observations.",
            "Open-Meteo provides numerical weather forecasts, not IMD warnings; an official IMD warning feed is not integrated.",
            "Instantaneous temperature is Open-Meteo model data, not an IMD station observation. IMD's city report supplies today's observed high and low, not a live instant temperature; station observations may be delayed.",
            "The 10 m computational grid is not proof of 10 m terrain accuracy. The bundled terrain is synthetic; no real SRTM elevation file is included.",
            "Drainage capacity, land cover, sewer condition, road closures and municipal response are synthesized from documented disaster records and resident reports.",
            "Nationwide coverage spans all 28 States and 8 Union Territories with historical flood context and chronic drainage chokepoints.",
            "Do not use this prototype for travel, evacuation or emergency decisions. Follow IMD, NDMA and local authorities.",
        ],
    }
