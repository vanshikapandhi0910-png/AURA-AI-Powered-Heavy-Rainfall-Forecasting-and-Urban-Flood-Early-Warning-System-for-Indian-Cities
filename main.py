"""FastAPI application and lightweight static-file server for AURA-Flood."""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.community import add_experience, get_experiences
from backend.india_dataset import get_all_locations_directory
from backend.engine import (
    get_alert,
    get_evaluation,
    get_hotspots,
    get_rainfall,
    get_risk_grid,
    resolve_location,
)

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"

app = FastAPI(title="AURA-Flood", version="0.2.0")


class ExperienceSubmission(BaseModel):
    location_label: str = Field(min_length=2, max_length=180)
    city: str = Field(default="", max_length=100)
    state: str = Field(default="", max_length=100)
    category: Literal["Waterlogging observed", "Road/access blocked", "Drainage/chokepoint concern"]
    experience: str = Field(min_length=8, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


@app.get("/api/risk-grid")
def risk_grid(lat: float = 31.6446, lon: float = 74.8725):
    return get_risk_grid(lat, lon)


@app.get("/api/rainfall")
def rainfall(lat: float = 31.6446, lon: float = 74.8725, city: str | None = None):
    return get_rainfall(lat, lon, city)


@app.get("/api/hotspots")
def hotspots():
    return get_hotspots()


@app.get("/api/experiences")
def experiences():
    return {
        "reports": get_experiences(),
        "data_status": "Community submitted · unverified reports",
    }


@app.post("/api/experiences", status_code=201)
def submit_experience(report: ExperienceSubmission):
    return add_experience(report.model_dump())


@app.get("/api/alerts")
def alerts(
    lat: float | None = None,
    lon: float | None = None,
    state: str | None = None,
    city: str | None = None,
    area: str | None = None,
):
    try:
        location = resolve_location(lat, lon, state, city, area)
        return get_alert(location)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/evaluation")
def evaluation():
    return get_evaluation()


@app.get("/api/locations")
def locations():
    return {
        "locations": get_all_locations_directory(),
        "total": len(get_all_locations_directory()),
        "scope": "All 28 States and 8 Union Territories of India",
    }


@app.get("/manifest.json")
def manifest():
    return FileResponse(FRONTEND / "manifest.json", media_type="application/manifest+json")


app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
