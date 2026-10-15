"""Source-linked historical flood reports, nationwide drainage analysis, and resident reviews."""

from __future__ import annotations

import csv
import math
import re
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from backend.india_dataset import INDIA_FLOOD_DATABASE, find_matching_localities

DATA = Path(__file__).resolve().parents[1] / "data"
REPORTS_FILE = DATA / "historical_flood_reports.csv"
INDOFLOODS_EVENTS_FILE = DATA / "indofloods_events.csv"
INDOFLOODS_GAUGES_FILE = DATA / "indofloods_gauges.csv"
EARTH_RADIUS_KM = 6371.0088
CURRENT_OBSERVATION_MAX_AGE = timedelta(minutes=45)
INDOFLOODS_MATCH_RADIUS_KM = 2.0
INDOFLOODS_START_YEAR = 2000
INDOFLOODS_END_YEAR = 2020
INDOFLOODS_SOURCE = "https://doi.org/10.5281/zenodo.14584655"


def _normalize(value: object) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(value).lower())).strip()


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = lat2_rad - lat1_rad
    delta_lon = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(value))


@lru_cache(maxsize=1)
def _load_indofloods() -> tuple[tuple[dict[str, str], list[dict[str, str]]], ...]:
    if not INDOFLOODS_GAUGES_FILE.exists() or not INDOFLOODS_EVENTS_FILE.exists():
        return ()
    try:
        with INDOFLOODS_GAUGES_FILE.open(newline="", encoding="utf-8-sig") as stream:
            gauges = {
                row["GaugeID"]: row
                for row in csv.DictReader(stream)
                if row.get("Privacy", "").strip().lower() == "open"
            }

        events_by_gauge: dict[str, list[dict[str, str]]] = {}
        with INDOFLOODS_EVENTS_FILE.open(newline="", encoding="utf-8-sig") as stream:
            for event in csv.DictReader(stream):
                event_id = event["EventID"]
                gauge_id = event_id.rsplit("-", 1)[0]
                year_text = event["Start Date"][:4]
                if (
                    gauge_id in gauges
                    and year_text.isdigit()
                    and INDOFLOODS_START_YEAR <= int(year_text) <= INDOFLOODS_END_YEAR
                ):
                    events_by_gauge.setdefault(gauge_id, []).append(event)

        return tuple(
            (gauge, events_by_gauge[gauge_id])
            for gauge_id, gauge in gauges.items()
            if events_by_gauge.get(gauge_id)
        )
    except Exception:
        return ()


def _indofloods_gauge_context(location: dict) -> list[dict]:
    if location.get("lat") is None or location.get("lon") is None:
        return []

    matches = []
    location_state = _normalize(location.get("state", ""))
    for gauge, events in _load_indofloods():
        gauge_state = _normalize(gauge["State"])
        if location_state and gauge_state and location_state != gauge_state:
            continue
        distance = _distance_km(
            float(location["lat"]),
            float(location["lon"]),
            float(gauge["Latitude"]),
            float(gauge["Longitude"]),
        )
        if distance > INDOFLOODS_MATCH_RADIUS_KM:
            continue

        events = sorted(events, key=lambda event: event["Start Date"], reverse=True)
        matches.append(
            {
                "station": gauge["Station"],
                "river": gauge["River Name/ Tributory/ SubTributory"],
                "state": gauge["State"],
                "distance_km": round(distance, 1),
                "event_count": len(events),
                "events": [
                    {
                        "start_date": event["Start Date"],
                        "end_date": event["End Date"],
                        "duration_days": event["Event Duration (days)"],
                        "flood_type": event["Flood Type"],
                    }
                    for event in events[:5]
                ],
                "source_url": INDOFLOODS_SOURCE,
            }
        )
    return sorted(matches, key=lambda gauge: gauge["distance_km"])[:3]


def _report_matches(report: dict[str, str], location: dict) -> bool:
    location_state = _normalize(location.get("state", ""))
    report_state = _normalize(report["state"])
    if location_state and report_state and location_state != report_state:
        return False

    fields = [
        _normalize(location.get(field, ""))
        for field in ("area", "city", "label")
        if location.get(field)
    ]
    aliases = [_normalize(value) for value in report["matching_names"].split(";") if value.strip()]
    if any(
        f" {alias} " in f" {field} "
        for alias in aliases
        for field in fields
        if alias
    ):
        return True

    if (
        not report.get("latitude", "").strip()
        or not report.get("longitude", "").strip()
        or location.get("lat") is None
        or location.get("lon") is None
    ):
        return False
    distance = _distance_km(
        float(location["lat"]),
        float(location["lon"]),
        float(report["latitude"]),
        float(report["longitude"]),
    )
    return distance <= float(report.get("match_radius_km", 2.0))


def get_historical_flood_context(location: dict, rainfall: dict) -> dict:
    """Comprehensive India-wide historical events, drainage assessment, and resident reviews."""
    current = rainfall.get("current_conditions") or {}
    precipitation = current.get("precipitation_mm")
    rain_values = rainfall.get("rain_mm") or []
    peak_expected_rain = max(rain_values) if rain_values else 0.0

    observation_time = None
    try:
        observation_time = datetime.fromisoformat(current["time"])
    except (KeyError, TypeError, ValueError):
        observation_time = None
    if observation_time is not None and observation_time.tzinfo is None:
        observation_time = observation_time.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    if observation_time is not None:
        observation_age = datetime.now(timezone.utc) - observation_time.astimezone(timezone.utc)
        observation_is_fresh = timedelta(0) <= observation_age <= CURRENT_OBSERVATION_MAX_AGE
    else:
        observation_is_fresh = False

    rain_indicated = (
        isinstance(precipitation, (int, float))
        and math.isfinite(precipitation)
        and precipitation >= 0.1
    )
    live_rain_available = (
        not rainfall.get("simulated", True)
        and not rainfall.get("offline_cache", False)
        and isinstance(precipitation, (int, float))
        and observation_is_fresh
    )

    if rainfall.get("offline_cache", False):
        rain_status = "Cached offline weather; local historical data active"
    elif rainfall.get("simulated", True):
        rain_status = (
            "Local baseline forecast active; historical flood data will warn only when a live weather model indicates rain."
        )
    elif observation_time is None or not observation_is_fresh:
        rain_status = (
            "No current weather observation within the 45-minute freshness window; "
            "historical flood data will warn only when fresh live rain data is available."
        )
    elif not isinstance(precipitation, (int, float)):
        rain_status = "No usable rain data in the current weather model output."
    elif rain_indicated:
        rain_status = f"Live weather model indicates active rainfall ({precipitation:.1f} mm)."
    else:
        rain_status = f"Live weather model does not indicate rain ({precipitation:.1f} mm)."

    # Match reports from CSV if available
    matched_csv_reports = []
    if REPORTS_FILE.exists():
        with REPORTS_FILE.open(newline="", encoding="utf-8-sig") as stream:
            matched_csv_reports = [
                report
                for report in csv.DictReader(stream)
                if _report_matches(report, location)
            ]

    # Query comprehensive India-wide dataset covering all 28 states and 8 UTs
    india_matches = find_matching_localities(
        query_text=location.get("area") or location.get("label"),
        city=location.get("city"),
        state=location.get("state"),
        lat=location.get("lat"),
        lon=location.get("lon"),
    )

    combined_records = []
    # Add CSV matches first
    for report in matched_csv_reports:
        combined_records.append({
            "place_name": report["place_name"],
            "event_date": report["event_date"],
            "hazard": report["hazard"],
            "reported_impact": report["reported_impact"],
            "location_precision": report.get("location_precision", "Locality"),
            "confidence": report.get("confidence", "Medium"),
            "source_name": report.get("source_name", "Documented source"),
            "source_url": report.get("source_url", "https://ndma.gov.in/"),
        })

    # Add matches from nationwide India flood database
    all_chokepoints = []
    all_reviews = []
    drainage_desc = "Standard urban drainage"
    terrain_desc = "Alluvial plain"
    drainage_rating = 3
    clogging_tendency = "Moderate - Slow Drainage"
    travel_advisory = "Follow local weather and traffic advisories."
    clogged_under_rain = False

    if india_matches:
        primary = india_matches[0]
        drainage_desc = primary.get("drainage_system", drainage_desc)
        terrain_desc = primary.get("terrain_type", terrain_desc)
        drainage_rating = primary.get("drainage_rating", 3)
        clogging_tendency = primary.get("clogging_tendency", clogging_tendency)
        travel_advisory = primary.get("travel_advisory", travel_advisory)
        clogged_under_rain = primary.get("clogged_under_rain", False)

        for match in india_matches:
            for chokepoint in match.get("chronic_chokepoints", []):
                if chokepoint not in all_chokepoints:
                    all_chokepoints.append(chokepoint)
            for review in match.get("resident_reviews", []):
                all_reviews.append({**review, "location": f"{match['locality']}, {match['city']}"})
            for evt in match.get("past_flood_events", []):
                combined_records.append({
                    "place_name": f"{match['locality']}, {match['city']} ({match['state']})",
                    "event_date": evt.get("year", "Historical Event"),
                    "hazard": f"Flood & Waterlogging ({match.get('terrain_type', 'Urban basin')})",
                    "reported_impact": f"{evt.get('event', '')} — {evt.get('impact', '')}",
                    "location_precision": "Locality / Basin match",
                    "confidence": "High (Official disaster & news records)",
                    "source_name": "State Disaster Management / Media Records",
                    "source_url": "https://ndma.gov.in/",
                })

    # ─────────────────────────────────────────────────────────────────────
    # ALERT LEVEL ENGINE
    # RED / YELLOW / GREEN is driven by live temperature + rainfall.
    # Past clogging history raises the urgency tier but never triggers red
    # when the sky is clear and temperature is normal.
    #
    # Tiers:
    #   RED    = active rain (observed/forecast) + past clogging history OR heavy rain
    #   YELLOW = active rain with no clogging history, OR dry but historically clogged area
    #   GREEN  = no rain, no history of clogging
    # ─────────────────────────────────────────────────────────────────────

    is_raining = rain_indicated or peak_expected_rain >= 2.0
    is_heavy_rain = peak_expected_rain >= 8.0 or (
        isinstance(precipitation, (int, float)) and precipitation >= 6.0
    )
    temperature = current.get("temperature_2m")
    temp_is_hot = isinstance(temperature, (int, float)) and temperature >= 30.0

    has_exact_locality_records = any(not loc.get("is_state_fallback", False) for loc in india_matches) or bool(matched_csv_reports)
    has_past_records = bool(combined_records) or bool(india_matches)
    has_chronic_risk = (drainage_rating <= 2 or clogged_under_rain) and has_exact_locality_records

    # ── Determine alert level ────────────────────────────────────────────
    if is_raining and (has_chronic_risk or is_heavy_rain):
        # RED: Rain is active AND area is historically risky OR rain is very heavy
        alert_level = "RED"
        clogging_status = "CLOGGED"
        clogging_badge = "🔴 RED ALERT — ACTIVE RAIN + PAST CLOGGING/FLOOD HISTORY"
        if has_past_records:
            clogging_summary = (
                f"⚠️ Active rainfall detected in an area with documented past flood and clogging history. "
                f"Drainage infrastructure: {drainage_desc}. It once flooded and has high chances of being flooded or clogged right now. "
                f"It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too."
            )
        else:
            clogging_summary = (
                f"Heavy rainfall detected. Poor drainage infrastructure ({drainage_desc}) means "
                f"immediate waterlogging is likely at chokepoints. It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too."
            )
        should_alarm = True
        alarm_reason = f"🔴 RED ALERT: Rain + flood/clogging risk detected in {location.get('city') or 'this area'}!"

    elif is_raining and not has_chronic_risk:
        # YELLOW: Rain is active but no documented clogging history
        alert_level = "YELLOW"
        clogging_status = "CAUTION"
        clogging_badge = "🟡 YELLOW — RAINING · Caution on Low-Lying Roads"
        clogging_summary = (
            f"It is currently raining in this area. While no specific prior local disaster record is cataloged at this exact point, "
            f"it may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too. "
            f"Watch for low-lying roads and underpasses."
        )
        should_alarm = False
        alarm_reason = ""

    elif not is_raining and has_past_records and has_chronic_risk:
        # YELLOW: Dry right now but historically a clogged/flooded zone
        alert_level = "YELLOW"
        clogging_status = "PRONE_TO_CLOGGING"
        clogging_badge = "🟡 YELLOW — DRY NOW · Past Flood / Clogging Recorded"
        clogging_summary = (
            f"Currently dry — no active rainfall. However, this area has a documented history of severe flooding and waterlogging "
            f"due to {drainage_desc}. It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too. "
            f"Monitor weather forecasts and avoid low-lying roads during downpours."
        )
        should_alarm = False
        alarm_reason = ""

    elif not is_raining and has_past_records and not has_chronic_risk and has_exact_locality_records:
        # YELLOW (mild): Dry, has some historical record but better drainage
        alert_level = "YELLOW"
        clogging_status = "WATCH"
        clogging_badge = "🟡 WATCH — Dry · Historical Flooding on Record"
        clogging_summary = (
            f"Currently dry. Past flood events recorded for this area, though drainage is moderate ({drainage_desc}). "
            f"It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too. "
            f"Monitor rainfall forecasts."
        )
        should_alarm = False
        alarm_reason = ""

    else:
        # GREEN: No rain, no specific severe clogging records → safe
        alert_level = "GREEN"
        clogging_status = "CLEAR"
        clogging_badge = "🟢 GREEN — CLEAR · No Rain · No Clogging Records"
        clogging_summary = (
            f"No active rainfall and no documented severe clogging history for this specific point. "
            f"Current conditions appear normal (Drainage: {drainage_desc}, Terrain: {terrain_desc}). "
            f"Note: Low-lying sections may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too."
        )
        should_alarm = is_heavy_rain
        alarm_reason = f"Unexpected heavy downpour in {location.get('city') or 'area'}." if is_heavy_rain else ""

    current_rain_status = (
        "unavailable"
        if rainfall.get("offline_cache", False) or not live_rain_available
        else "rain_indicated"
        if rain_indicated
        else "not_indicated"
    )
    warning = bool(matched_csv_reports) and live_rain_available and rain_indicated

    return {
        "rain_indicated_by_live_model": live_rain_available and rain_indicated,
        "current_rain_status": current_rain_status,
        "rain_status": rain_status,
        "warning": warning,
        "alert_level": alert_level,
        "temperature_c": temperature,
        "has_past_records": has_past_records,
        "travel_alarm": {
            "should_alarm": should_alarm,
            "alarm_reason": alarm_reason,
            "clogging_status": clogging_status,
        },
        "clogging_assessment": {
            "status": clogging_status,
            "alert_level": alert_level,
            "status_badge": clogging_badge,
            "drainage_system": drainage_desc,
            "drainage_rating": drainage_rating,
            "terrain_type": terrain_desc,
            "clogging_tendency": clogging_tendency,
            "chronic_chokepoints": all_chokepoints,
            "resident_reviews": all_reviews,
            "travel_advisory": travel_advisory,
            "summary": clogging_summary,
            "has_past_records": has_past_records,
            "is_raining": is_raining,
            "temperature_c": temperature,
        },
        "indofloods_gauges": _indofloods_gauge_context(location),
        "indofloods_coverage_note": (
            "INDOFLOODS gauge-event records cover 2000–2020 river basin stations across India; "
            "open gauge data excludes the Ganga and Brahmaputra."
        ),
        "records": [
            {
                "place_name": report["place_name"],
                "event_date": report["event_date"],
                "hazard": report["hazard"],
                "reported_impact": report["reported_impact"],
                "location_precision": report.get("location_precision", "Locality"),
                "confidence": report.get("confidence", "Medium"),
                "source_name": report.get("source_name", "Documented source"),
                "source_url": report.get("source_url", "https://ndma.gov.in/"),
            }
            for report in matched_csv_reports
        ] if matched_csv_reports else combined_records,
        "nationwide_records": combined_records,
        "warning_text": (
            f"{clogging_badge}: {clogging_summary} {travel_advisory}"
            if should_alarm or alert_level == "RED"
            else None
        ),
    }
