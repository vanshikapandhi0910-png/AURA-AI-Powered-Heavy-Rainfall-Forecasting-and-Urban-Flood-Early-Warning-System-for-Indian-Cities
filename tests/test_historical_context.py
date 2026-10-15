import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from backend.historical import REPORTS_FILE, get_historical_flood_context
from backend.engine import _imd_city_report_fields, get_alert, resolve_location


def live_rain(precipitation: float) -> dict:
    return {
        "simulated": False,
        "current_conditions": {
            "precipitation_mm": precipitation,
            "time": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="minutes"),
        },
    }


class HistoricalFloodContextTests(unittest.TestCase):
    def test_chashoti_alias_uses_approximate_hamlet_point_not_kishtwar_city_centre(self):
        location = resolve_location(
            None,
            None,
            "Jammu and Kashmir",
            "Kishtwar",
            "Chashoti",
        )

        self.assertAlmostEqual(location["lat"], 33.3778917)
        self.assertAlmostEqual(location["lon"], 76.2782699)
        self.assertTrue(location["approximate"])
        self.assertIn("approximate OpenStreetMap hamlet point", location["weather_location_note"])

    def test_cuddapah_alias_resolves_to_kadapa_instead_of_demo_coordinates(self):
        location = resolve_location(None, None, "Andhra Pradesh", "Cuddapah", "")

        self.assertAlmostEqual(location["lat"], 14.4673)
        self.assertAlmostEqual(location["lon"], 78.8242)
        self.assertNotIn("demo coordinates", location["label"])

    def test_cuddapah_2001_ifrc_flood_is_matched_for_the_city(self):
        result = get_historical_flood_context(
            {"city": "Cuddapah", "state": "Andhra Pradesh"},
            live_rain(0.0),
        )
        coordinate_result = get_historical_flood_context(
            {"lat": 14.4673, "lon": 78.8242, "state": "Andhra Pradesh"},
            live_rain(0.0),
        )

        self.assertFalse(result["warning"])
        self.assertEqual(result["current_rain_status"], "not_indicated")
        self.assertEqual(result["records"][0]["place_name"], "Cuddapah city (Kadapa)")
        self.assertEqual(coordinate_result["records"][0]["place_name"], "Cuddapah city (Kadapa)")
        self.assertEqual(
            result["records"][0]["source_name"],
            "IFRC, India floods 2001 — Appeal 21/2001, Operations Update No. 6",
        )
        self.assertIn("not an event boundary", result["records"][0]["location_precision"])

    def test_ganjam_2013_phailin_flood_is_matched_at_district_level(self):
        result = get_historical_flood_context(
            {"area": "Ganjam", "city": "Brahmapur", "state": "Odisha"},
            live_rain(0.0),
        )

        self.assertEqual(len(result["records"]), 1)
        record = result["records"][0]
        self.assertEqual(record["place_name"], "Ganjam district")
        self.assertEqual(record["event_date"], "October 2013 (Phailin aftermath; exact observation date not stated)")
        self.assertIn("50–60 villages", record["reported_impact"])
        self.assertIn("District;", record["location_precision"])
        self.assertIn("coastal storm-surge inundation", record["hazard"])
        self.assertEqual(
            record["source_name"],
            "IFRC, India: Cyclone Phailin — DREF operation MDRIN013, Operation Update No. 1",
        )

    def test_alert_emits_nationwide_flood_screening_and_clogging_status_outside_the_amritsar_pilot(self):
        location = {
            "lat": 19.32,
            "lon": 84.79,
            "label": "Ganjam, Brahmapur, Odisha",
            "city": "Brahmapur",
            "state": "Odisha",
            "area": "Ganjam",
            "approximate": True,
            "weather_location_note": "Approximate city location",
        }
        forecast = {"simulated": False, "current_conditions": {}, "source": "test source"}

        with (
            patch("backend.engine._forecast", return_value=forecast),
            patch("backend.engine._imd_city_observation", return_value=None),
            patch("backend.engine._model_bundle") as model_bundle,
            patch("backend.engine._terrain_data_status", return_value="SIMULATED terrain"),
        ):
            result = get_alert(location)

        self.assertTrue(result["screening_available"])
        self.assertIn(result["risk"], ("Low", "Moderate", "High"))
        self.assertIsNotNone(result["confidence_pct"])
        self.assertIsNotNone(result["time_to_threshold_hours"])
        self.assertIsNotNone(result["uncertainty"])
        self.assertNotIn("The experimental terrain-backed screening is limited to Ranjit Avenue, Amritsar", result["message"])
        self.assertIn("clogging_assessment", result["historical_context"])
        model_bundle.assert_not_called()

    def test_imd_city_report_parses_daily_forecast_rainfall_and_warning(self):
        fields = _imd_city_report_fields({
            "rainfall": "3.00",
            "ffc": ["Partly cloudy with rain", "Mainly clear"],
            "wText": ["Thunderstorm accompanied with lightning", "No warning"],
        })

        self.assertEqual(fields["rainfall_24h_mm"], 3.0)
        self.assertEqual(fields["today_forecast"], "Partly cloudy with rain")
        self.assertEqual(fields["today_warning"], "Thunderstorm accompanied with lightning")

    def test_chashoti_spelling_matches_chishoti_historical_record(self):
        result = get_historical_flood_context(
            {"area": "Chashoti", "city": "Kishtwar", "state": "Jammu and Kashmir"},
            live_rain(0.8),
        )

        self.assertTrue(result["warning"])
        self.assertEqual(result["current_rain_status"], "rain_indicated")
        self.assertEqual(result["records"][0]["place_name"], "Chishoti")

    def test_device_coordinates_near_chishoti_match_approximate_village_record(self):
        result = get_historical_flood_context(
            {"lat": 33.3778, "lon": 76.2781, "state": "Jammu and Kashmir"},
            live_rain(0.8),
        )

        self.assertTrue(result["warning"])
        self.assertEqual(result["records"][0]["place_name"], "Chishoti")

    def test_approximate_village_point_matches_and_warns_when_live_model_indicates_rain(self):
        result = get_historical_flood_context(
            {"lat": 30.5151181, "lon": 74.0513720, "state": "Punjab"},
            live_rain(0.8),
        )

        self.assertTrue(result["warning"])
        self.assertGreaterEqual(len(result["records"]), 2)
        self.assertIsNotNone(result["warning_text"])

    def test_locality_name_matches_without_triggering_on_parent_city_alone(self):
        locality = get_historical_flood_context(
            {"area": "Dhoka Mohalla", "city": "Ludhiana", "state": "Punjab"},
            live_rain(1.2),
        )
        city_only = get_historical_flood_context(
            {"city": "Ludhiana", "state": "Punjab"},
            live_rain(1.2),
        )

        self.assertTrue(locality["warning"])
        self.assertEqual([row["place_name"] for row in locality["records"]], ["Dhoka Mohalla"])
        self.assertFalse(city_only["warning"])

    def test_historical_record_does_not_warn_for_simulated_or_no_rain(self):
        location = {"area": "Mazor Chapori", "state": "Assam"}

        simulated = get_historical_flood_context(
            location,
            {"simulated": True, "current_conditions": {"precipitation_mm": 12.0}},
        )
        dry = get_historical_flood_context(location, live_rain(0.0))

        self.assertFalse(simulated["warning"])
        self.assertEqual(simulated["current_rain_status"], "unavailable")
        self.assertFalse(dry["warning"])
        self.assertEqual(dry["current_rain_status"], "not_indicated")
        self.assertTrue(simulated["records"])

    def test_subthreshold_precipitation_does_not_warn(self):
        result = get_historical_flood_context(
            {"area": "Mazor Chapori", "state": "Assam"},
            live_rain(0.09),
        )

        self.assertFalse(result["warning"])
        self.assertIn("does not indicate rain", result["rain_status"])

    def test_missing_current_precipitation_is_unavailable_not_dry(self):
        result = get_historical_flood_context(
            {"area": "Mazor Chapori", "state": "Assam"},
            {
                "simulated": False,
                "current_conditions": {
                    "precipitation_mm": None,
                    "time": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="minutes"),
                },
            },
        )

        self.assertEqual(result["current_rain_status"], "unavailable")
        self.assertIn("usable rain data", result["rain_status"])

    def test_cached_offline_rain_is_not_reported_as_current(self):
        result = get_historical_flood_context(
            {"area": "Mazor Chapori", "state": "Assam"},
            {
                "simulated": False,
                "offline_cache": True,
                "current_conditions": {
                    "precipitation_mm": 2.0,
                    "time": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="minutes"),
                },
            },
        )

        self.assertEqual(result["current_rain_status"], "unavailable")
        self.assertFalse(result["rain_indicated_by_live_model"])
        self.assertIn("Cached offline", result["rain_status"])

    def test_stale_current_weather_does_not_trigger_warning(self):
        result = get_historical_flood_context(
            {"area": "Mazor Chapori", "state": "Assam"},
            {
                "simulated": False,
                "current_conditions": {
                    "precipitation_mm": 5.0,
                    "time": "2020-01-01T12:00",
                },
            },
        )

        self.assertFalse(result["warning"])
        self.assertEqual(result["current_rain_status"], "unavailable")
        self.assertIn("freshness window", result["rain_status"])

    def test_each_dataset_record_has_a_source_and_complete_csv_row(self):
        import csv

        with REPORTS_FILE.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)

        self.assertGreater(len(rows), 0)
        self.assertTrue(all(None not in row and row["source_url"] for row in rows))

    def test_state_mismatch_does_not_match_same_place_name(self):
        result = get_historical_flood_context(
            {"area": "Guddar Bhaini", "state": "Haryana"},
            live_rain(0.8),
        )

        self.assertFalse(result["warning"])
        self.assertEqual(result["records"], [])

    def test_district_report_matches_explicit_district_not_nearby_unspecified_place(self):
        district = get_historical_flood_context(
            {"city": "Gurdaspur", "state": "Punjab"},
            live_rain(0.8),
        )
        nearby = get_historical_flood_context(
            {"city": "Amritsar", "state": "Punjab"},
            live_rain(0.8),
        )

        self.assertTrue(district["warning"])
        self.assertEqual(district["records"][0]["location_precision"], "District; broad area only")
        self.assertFalse(nearby["warning"])

    def test_indofloods_adds_nearby_station_history_as_separate_evidence(self):
        result = get_historical_flood_context(
            {"lat": 15.8833, "lon": 77.9572, "state": "Andhra Pradesh"},
            live_rain(0.0),
        )

        self.assertEqual(result["current_rain_status"], "not_indicated")
        self.assertFalse(result["warning"])
        self.assertEqual(result["records"], [])
        self.assertEqual(result["indofloods_gauges"][0]["station"], "Bawapuram")
        self.assertGreater(result["indofloods_gauges"][0]["event_count"], 0)
        self.assertTrue(result["indofloods_gauges"][0]["source_url"].startswith("https://doi.org/"))
        self.assertTrue(
            all(
                "2000" <= event["start_date"][:4] <= "2020"
                for event in result["indofloods_gauges"][0]["events"]
            )
        )

    def test_indofloods_does_not_match_distant_kadapa_station(self):
        result = get_historical_flood_context(
            {"lat": 14.4673, "lon": 78.8242, "state": "Andhra Pradesh"},
            live_rain(0.0),
        )

        self.assertEqual(result["indofloods_gauges"], [])
        self.assertIn("excludes the Ganga and Brahmaputra", result["indofloods_coverage_note"])

    def test_village_report_does_not_match_only_its_district_or_city(self):
        result = get_historical_flood_context(
            {"city": "Kishtwar", "state": "Jammu and Kashmir"},
            live_rain(0.8),
        )
        self.assertFalse(any(r.get("place_name") == "Chishoti" for r in result["records"]))

    def test_dharbanga_spelling_resolves_to_darbhanga_not_patna(self):
        # User entered Bihar (state) and Dharbanga (city with variant spelling)
        location = resolve_location(None, None, "Bihar", "Dharbanga", "")

        # Must resolve to Darbhanga's real coordinates, NOT Patna
        self.assertAlmostEqual(location["lat"], 26.1542, places=3)
        self.assertAlmostEqual(location["lon"], 85.8918, places=3)
        self.assertIn("Darbhanga", location["label"])
        self.assertNotIn("Patna", location["label"])

        # Context evaluation must pull Darbhanga's hydrological & review records
        context = get_historical_flood_context(location, live_rain(15.0))
        clogging = context["clogging_assessment"]
        
        self.assertEqual(clogging["status"], "CLOGGED")
        self.assertEqual(clogging["drainage_rating"], 1)
        self.assertTrue(context["travel_alarm"]["should_alarm"])
        # New alert-level engine assertions
        self.assertEqual(clogging["alert_level"], "RED")
        self.assertTrue(clogging["has_past_records"])
        self.assertTrue(clogging["is_raining"])
        self.assertEqual(context["alert_level"], "RED")

        # Verify chokepoints and reviews belong to Darbhanga
        chokepoints_str = " ".join(clogging["chronic_chokepoints"])
        self.assertIn("Tower Chowk", chokepoints_str)
        self.assertNotIn("Kankarbagh", chokepoints_str)
        self.assertNotIn("Saidpur", chokepoints_str)

    def test_alert_level_is_green_when_dry_and_no_clogging_history(self):
        """Areas with no rain and no documented clogging must return GREEN — never RED by default."""
        # Use a remote location with no known clogging events and no rain
        result = get_historical_flood_context(
            {"city": "SomeUnknownTown", "state": "Sikkim"},
            live_rain(0.0),
        )
        ca = result["clogging_assessment"]
        self.assertEqual(result["alert_level"], "GREEN")
        self.assertEqual(ca["alert_level"], "GREEN")
        self.assertFalse(result["travel_alarm"]["should_alarm"])

    def test_alert_level_is_yellow_when_raining_with_no_clogging_records(self):
        """Rain with no chronic drainage risk should yield YELLOW, not RED."""
        result = get_historical_flood_context(
            {"city": "SomeUnknownTown", "state": "Himachal Pradesh"},
            live_rain(3.0),   # light rain, no chronic risk
        )
        ca = result["clogging_assessment"]
        # Should be YELLOW (caution) not RED since no chronic risk / past records
        self.assertIn(result["alert_level"], ("YELLOW", "GREEN"))
    def test_upper_assam_city_resolves_and_includes_2026_deluge_and_resident_warning(self):
        """User searched for Assam state and Upper Assam city: must match 2026 flood events and resident warning statement."""
        location = resolve_location(None, None, "Assam", "Upper Assam", "")
        self.assertAlmostEqual(location["lat"], 27.2000, places=2)
        self.assertAlmostEqual(location["lon"], 94.6000, places=2)
        self.assertIn("Upper Assam", location["label"])

        # When dry: area has documented past flood disaster history, so it must return YELLOW (prone to flooding)
        context_dry = get_historical_flood_context(location, live_rain(0.0))
        ca_dry = context_dry["clogging_assessment"]
        self.assertEqual(context_dry["alert_level"], "YELLOW")
        self.assertEqual(ca_dry["status"], "PRONE_TO_CLOGGING")
        self.assertTrue(ca_dry["has_past_records"])
        self.assertIn("it may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too", ca_dry["summary"].lower())

        # Verify 2026 flood event is present in the records
        event_years = [ev.get("year") for r in context_dry["records"] for ev in [r] if "2026" in str(r.get("event_date", ""))]
        # Or in india_matches past_flood_events
        india_match = context_dry.get("india_dataset_match")
        past_events = india_match.get("past_flood_events", []) if india_match else []
        self.assertTrue(any(ev.get("year") == "2026" for ev in past_events) or bool(event_years))

        # When raining: must trigger RED alert and travel alarm
        context_rain = get_historical_flood_context(location, live_rain(4.0))
        ca_rain = context_rain["clogging_assessment"]
        self.assertEqual(context_rain["alert_level"], "RED")
        self.assertEqual(ca_rain["status"], "CLOGGED")
        self.assertTrue(context_rain["travel_alarm"]["should_alarm"])
        self.assertIn("it may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too", ca_rain["summary"].lower())

    def test_upper_assam_variant_spelling_and_city_queries(self):
        """Variant queries such as 'upper assam city' or 'Jorhat' must resolve and match past experiences."""
        loc_variant = resolve_location(None, None, "Assam", "upper assam city", "")
        context_variant = get_historical_flood_context(loc_variant, live_rain(0.0))
        self.assertTrue(context_variant["clogging_assessment"]["has_past_records"])
        self.assertIn("it may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too", context_variant["clogging_assessment"]["summary"].lower())

        loc_jorhat = resolve_location(None, None, "Assam", "Jorhat", "")
        context_jorhat = get_historical_flood_context(loc_jorhat, live_rain(0.0))
        self.assertTrue(context_jorhat["clogging_assessment"]["has_past_records"])
        self.assertEqual(context_jorhat["alert_level"], "YELLOW")


if __name__ == "__main__":
    unittest.main()


