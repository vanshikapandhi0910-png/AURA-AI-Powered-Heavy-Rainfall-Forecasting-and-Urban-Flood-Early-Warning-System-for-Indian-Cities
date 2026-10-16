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
    # DYNAMIC MULTI-FACTOR SCREENING SCORING & TAILORED NARRATIVE
    # ─────────────────────────────────────────────────────────────────────
    is_raining = rain_indicated or peak_expected_rain >= 2.0
    is_heavy_rain = peak_expected_rain >= 8.0 or (
        isinstance(precipitation, (int, float)) and precipitation >= 6.0
    )
    temperature = current.get("temperature_2m")

    has_exact_locality_records = any(not loc.get("is_state_fallback", False) for loc in india_matches) or bool(matched_csv_reports)
    has_past_records = bool(combined_records) or bool(india_matches)
    has_chronic_risk = (drainage_rating <= 2 or clogged_under_rain) and has_exact_locality_records
    is_state_level = location.get("is_state_level", False) or (not location.get("city") and bool(location.get("state")))

    primary_locality = india_matches[0]["locality"] if india_matches else (location.get("area") or location.get("city") or "Selected area")
    primary_city = india_matches[0]["city"] if india_matches else (location.get("city") or "Urban area")
    primary_state = india_matches[0].get("state") if india_matches else (location.get("state") or "")

    # Calculate dynamic multi-factor screening score (0 to 100)
    drainage_pts_map = {1: 36.0, 2: 25.0, 3: 15.0, 4: 7.0, 5: 2.0}
    drainage_points = drainage_pts_map.get(drainage_rating, 15.0)

    elev_m = float(india_matches[0].get("elevation_m", 60.0)) if india_matches else 60.0
    # Lower elevation basins have higher water accumulation tendency
    elev_points = max(2.0, min(14.0, (150.0 - elev_m) * 0.08))

    t_lower = (terrain_desc or "").lower()
    if any(k in t_lower for k in ("floodplain", "basin", "bowl", "coastal", "tidal", "reclaimed", "marsh")):
        terrain_points = 18.0
    elif any(k in t_lower for k in ("valley", "depression", "alluvial", "low-lying")):
        terrain_points = 12.0
    elif any(k in t_lower for k in ("plateau", "ridge", "sloping", "hilly", "upland")):
        terrain_points = 4.0
    else:
        terrain_points = 8.0

    chokepoints_count = len(all_chokepoints)
    events_count = len(combined_records)
    history_points = min(22.0, (chokepoints_count * 2.8) + (events_count * 3.2) + (4.0 if clogged_under_rain else 0.0))

    curr_rain_val = float(precipitation or 0.0)
    rain_points = min(18.0, (curr_rain_val * 3.0) + (peak_expected_rain * 0.8))

    raw_score = drainage_points + elev_points + terrain_points + history_points + rain_points
    screening_score = round(max(15.0, min(96.0, raw_score)), 1)

    # Determine Alert Level & Status
    if is_raining and (has_chronic_risk or is_heavy_rain):
        alert_level = "RED"
        clogging_status = "CLOGGED"
        clogging_badge = "🔴 RED ALERT — ACTIVE RAIN & CRITICAL CLOGGING HAZARD"
        should_alarm = True
        alarm_reason = f"🔴 RED ALERT: Severe rain & waterlogging hazard detected in {primary_city}!"
        risk_class = "High"
        risk_range = ["Moderate", "High"]
        time_to_threshold = round(max(0.4, 2.0 - (screening_score / 60.0)), 1)
    elif is_raining:
        alert_level = "YELLOW"
        clogging_status = "CAUTION"
        clogging_badge = "🟡 CAUTION — ACTIVE RAINFALL · Slow Drainage Area"
        should_alarm = False
        alarm_reason = ""
        risk_class = "Moderate"
        risk_range = ["Low", "High"]
        time_to_threshold = round(max(1.2, 4.0 - (screening_score / 35.0)), 1)
    elif has_past_records and has_chronic_risk:
        alert_level = "YELLOW"
        clogging_status = "PRONE_TO_CLOGGING"
        clogging_badge = "🟡 CAUTION — CHRONIC WATERLOGGING ZONE · Currently Dry"
        should_alarm = False
        alarm_reason = ""
        risk_class = "High" if screening_score >= 68.0 else "Moderate"
        risk_range = ["Moderate", "High"] if screening_score >= 68.0 else ["Low", "High"]
        time_to_threshold = round(max(1.5, 5.0 - (screening_score / 30.0)), 1)
    elif has_past_records:
        alert_level = "YELLOW"
        clogging_status = "WATCH"
        clogging_badge = "🟡 WATCH — MODERATE RUNOFF PROFILE · Currently Dry"
        should_alarm = False
        alarm_reason = ""
        risk_class = "Moderate" if screening_score >= 42.0 else "Low"
        risk_range = ["Low", "Moderate"]
        time_to_threshold = round(max(2.5, 6.5 - (screening_score / 25.0)), 1)
    else:
        alert_level = "GREEN"
        clogging_status = "CLEAR"
        clogging_badge = "🟢 GREEN — STANDARD RUNOFF PROFILE · DRY"
        should_alarm = is_heavy_rain
        alarm_reason = f"Heavy downpour detected in {primary_city}." if is_heavy_rain else ""
        risk_class = "Low"
        risk_range = ["Low", "Moderate"]
        time_to_threshold = round(max(4.0, 10.0 - (screening_score / 15.0)), 1)

    # ─────────────────────────────────────────────────────────────────────
    # BESPOKE LOCATION-SPECIFIC NARRATIVE SUMMARY (NO REPETITIVE TEMPLATES)
    # ─────────────────────────────────────────────────────────────────────
    def _create_summary() -> str:
        loc_display = f"{primary_locality}, {primary_city}" if primary_locality != primary_city else primary_city
        if is_state_level:
            loc_display = f"{primary_state} State"

        # 1. Weather Sentence
        if is_raining:
            w_str = f"Active rain ({curr_rain_val:.1f} mm/h) is occurring over {loc_display}." if curr_rain_val > 0 else f"Rainfall expected over {loc_display} within the 6-hour forecast window (up to {peak_expected_rain:.1f} mm)."
        else:
            w_str = f"Dry conditions with no active precipitation detected over {loc_display}."

        # 2. Drainage & Terrain Sentence
        d_str = f"Hydrological profile: Set within {terrain_desc}, drainage capacity is rated {drainage_rating}/5 ({drainage_desc})."

        # 3. Chokepoints Sentence
        if all_chokepoints:
            cp_str = f"Known chronic bottlenecks include {', '.join(all_chokepoints[:3])}."
        else:
            cp_str = "No severe chronic structural chokepoints cataloged for this immediate perimeter."

        # 4. Past Events Sentence
        if combined_records:
            latest = combined_records[0]
            evt_yr = latest.get("event_date") or "Recent"
            evt_imp = latest.get("reported_impact") or latest.get("hazard", "")
            h_str = f"Documented historical flood record: During {evt_yr}, {evt_imp}."
        else:
            h_str = "Historical basin record: Standard regional flood management applies."

        # 5. Traveler Guidance
        adv = travel_advisory or ("Follow municipal traffic updates and monitor local stormwater drains during downpours." if alert_level != "GREEN" else "Standard conditions apply; follow IMD forecasts.")
        adv_str = f"Travel Guidance: {adv}"

        return f"{w_str} {d_str} {cp_str} {h_str} {adv_str}"

    clogging_summary = _create_summary()

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
            "locality": primary_locality,
            "city": primary_city,
            "state": primary_state,
            "drainage_system": drainage_desc,
            "drainage_rating": drainage_rating,
            "terrain_type": terrain_desc,
            "clogging_tendency": clogging_tendency,
            "chronic_chokepoints": all_chokepoints,
            "resident_reviews": all_reviews,
            "past_flood_events": [
                {
                    "year": rec.get("event_date", "Past Event"),
                    "impact": rec.get("reported_impact", rec.get("hazard", "")),
                }
                for rec in combined_records[:4]
            ],
            "travel_advisory": travel_advisory,
            "summary": clogging_summary,
            "screening_score": screening_score,
            "risk_class": risk_class,
            "risk_range": risk_range,
            "time_to_threshold_hours": time_to_threshold,
            "has_past_records": has_past_records,
            "is_raining": is_raining,
            "temperature_c": temperature,
            "is_state_level": is_state_level,
        },
        "indofloods_gauges": _indofloods_gauge_context(location),
        "indofloods_coverage_note": (
            "INDOFLOODS gauge-event records cover 2000–2020 river basin stations across India; "
            "open gauge data excludes the Ganga and Brahmaputra."
        ),
        "records": combined_records,
        "nationwide_records": combined_records,
        "warning_text": (
            f"{clogging_badge}: {clogging_summary} {travel_advisory}"
            if should_alarm or alert_level == "RED"
            else None
        ),
    }
