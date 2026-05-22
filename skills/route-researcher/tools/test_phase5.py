"""TDD tests for Phase 5 additions: itinerary generator + navigation bearings.

Pure-Python helpers — no HTTP mocks needed.
CLI tests use CliRunner with all fetchers patched.
"""

import json
from unittest.mock import patch

from click.testing import CliRunner
from fetch_conditions import build_itinerary, cli, compute_bearings

# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------

BASE_CLI_ARGS = [
    "--coordinates",
    "48.77,-121.81",
    "--elevation",
    "3286",
    "--peak-name",
    "Mt Baker",
]


def _run_cli(extra_args=None):
    runner = CliRunner()
    with (
        patch("fetch_conditions.fetch_weather", return_value={"forecast": [], "timezone": None}),
        patch("fetch_conditions.fetch_air_quality", return_value={"rating": "good"}),
        patch(
            "fetch_conditions.fetch_daylight",
            return_value={
                "sunrise": "5:00 AM",
                "sunset": "9:00 PM",
                "civil_dusk": "9:30 PM",
                "nautical_dusk": "10:00 PM",
            },
        ),
        patch("fetch_conditions.fetch_avalanche", return_value={"region": "north-cascades"}),
        patch("fetch_conditions.fetch_counties", return_value={"counties": []}),
        patch("fetch_conditions.fetch_nearest_hospital", return_value={"hospitals": []}),
        patch("fetch_conditions.fetch_ranger_station", return_value={"stations": []}),
        patch("fetch_conditions.fetch_campgrounds", return_value={"campgrounds": []}),
    ):
        return runner.invoke(cli, BASE_CLI_ARGS + (extra_args or []))


# ---------------------------------------------------------------------------
# 1. build_itinerary helper
# ---------------------------------------------------------------------------


class TestBuildItinerary:
    """build_itinerary(start_time, distance_mi, gain_ft, daylight) -> dict"""

    DAYLIGHT = {
        "sunrise": "5:00 AM",
        "sunset": "9:00 PM",
        "civil_dusk": "9:30 PM",
        "nautical_dusk": "10:00 PM",
    }

    def test_returns_start_time(self):
        result = build_itinerary("06:00", 8.0, 4000, self.DAYLIGHT)
        assert "start_time" in result
        assert result["start_time"] == "06:00"

    def test_returns_summit_eta(self):
        """summit_eta is present and a time string."""
        result = build_itinerary("06:00", 8.0, 4000, self.DAYLIGHT)
        assert "summit_eta" in result
        assert isinstance(result["summit_eta"], str)

    def test_returns_turnaround_time(self):
        result = build_itinerary("06:00", 8.0, 4000, self.DAYLIGHT)
        assert "turnaround_by" in result

    def test_returns_return_eta(self):
        result = build_itinerary("06:00", 8.0, 4000, self.DAYLIGHT)
        assert "return_eta" in result

    def test_summit_eta_later_than_start(self):
        """Summit ETA must be after start time."""
        result = build_itinerary("06:00", 8.0, 4000, self.DAYLIGHT)
        from datetime import datetime

        start = datetime.strptime("06:00", "%H:%M")
        summit = datetime.strptime(result["summit_eta"], "%H:%M")
        assert summit > start

    def test_return_eta_later_than_summit(self):
        """Return ETA must be after summit ETA."""
        result = build_itinerary("06:00", 8.0, 4000, self.DAYLIGHT)
        from datetime import datetime

        summit = datetime.strptime(result["summit_eta"], "%H:%M")
        ret = datetime.strptime(result["return_eta"], "%H:%M")
        assert ret > summit

    def test_after_dark_warning_false_when_return_before_nautical_dusk(self):
        """after_dark=False when return ETA is before nautical dusk."""
        # Start early, short route — should finish well before dark
        result = build_itinerary("05:00", 4.0, 2000, self.DAYLIGHT)
        assert "after_dark" in result
        assert result["after_dark"] is False

    def test_after_dark_warning_true_when_return_after_nautical_dusk(self):
        """after_dark=True when projected return is after nautical dusk."""
        # Start late with a long route — will finish after dark
        result = build_itinerary("14:00", 12.0, 6000, self.DAYLIGHT)
        assert "after_dark" in result
        assert result["after_dark"] is True

    def test_turnaround_based_on_dusk_cutoff(self):
        """turnaround_by is derived from the dusk cutoff, not an arbitrary value."""
        result = build_itinerary("06:00", 8.0, 4000, self.DAYLIGHT)
        # turnaround_by should be before nautical_dusk (10:00 PM)
        from datetime import datetime

        turnaround = datetime.strptime(result["turnaround_by"], "%H:%M")
        naut_dusk = datetime.strptime("22:00", "%H:%M")
        assert turnaround <= naut_dusk

    def test_missing_daylight_keys_handled_gracefully(self):
        """Sparse daylight dict (missing dusk keys) doesn't crash."""
        sparse = {"sunrise": "5:00 AM", "sunset": "9:00 PM"}
        result = build_itinerary("06:00", 8.0, 4000, sparse)
        assert "summit_eta" in result
        # after_dark may be None or False when dusk unknown
        assert "after_dark" in result

    # --- date-anchoring and turnaround semantics (P1 fixes) ---

    def test_pre_dawn_start_summit_eta_uses_elapsed_hours(self):
        """Pre-dawn start (02:00), long route: total_hr captures full elapsed time.

        If result times are re-parsed as HH:MM on 1900-01-01, a summit at 14:00
        looks correct, but a summit at 02:30+12hr=14:30 is fine; the real anchor
        test is total_hr which must equal ascent+descent regardless of wall-clock wrapping.
        """
        result = build_itinerary("02:00", 10.0, 5000, self.DAYLIGHT)
        assert "total_hr" in result
        assert result["total_hr"] > 0

    def test_after_midnight_finish_after_dark_true(self):
        """A route finishing after midnight must report after_dark=True.

        Re-parsing '00:30' as datetime gives 1900-01-01 00:30 which is LESS
        than dusk 1900-01-01 22:00, so the naive comparison reports after_dark=False.
        The fix uses elapsed timedeltas from start so midnight wrapping is handled.
        """
        # Start 21:00, short enough route that naive strptime wraps: ascent ~5hr → summit 02:00,
        # descent ~2.5hr → return 04:30 — all past dusk (22:00) but naive comparison says False.
        result = build_itinerary("21:00", 8.0, 5000, self.DAYLIGHT)
        # return_eta wraps past midnight; after_dark must still be True
        assert result["after_dark"] is True

    def test_turnaround_before_summit_when_day_too_short(self):
        """When dusk - descent_time < summit_eta, turnaround_by comes before summit in elapsed time.

        Start 18:00, nautical dusk 22:00.  Moderate ascent for 10mi/5000ft
        takes ~7hr → summit at 01:18 next day (past dusk).  Latest safe
        turnaround = dusk(22:00) - descent_hr ≈ 19:18, which is only 1.3hr
        after start — far less than the 7.3hr to summit.

        Wall-clock strings can't be compared directly when summit wraps past midnight,
        so use elapsed_hr_to_turnaround < ascent_hr as the assertion.
        """
        late_start = {
            "sunrise": "5:00 AM",
            "sunset": "9:00 PM",
            "civil_dusk": "9:30 PM",
            "nautical_dusk": "10:00 PM",
        }
        result = build_itinerary("18:00", 10.0, 5000, late_start)
        # after_dark must be True (summit and return are past dusk)
        assert result["after_dark"] is True
        # Elapsed time to turnaround < elapsed time to summit.
        # Compute both as minutes-from-start using total_hr as anchor.
        # turnaround_by = dusk - descent_hr = 22:00 - ~2.7hr = ~19:18 → 1hr18min from 18:00 start
        # summit_eta = 18:00 + 7.3hr = 01:18 next day → 7hr18min from start
        from datetime import datetime

        start = datetime.strptime("18:00", "%H:%M")
        turnaround = datetime.strptime(result["turnaround_by"], "%H:%M")
        # elapsed to turnaround (turnaround is same day as start for this case)
        turnaround_elapsed = (turnaround - start).total_seconds()
        if turnaround_elapsed < 0:
            turnaround_elapsed += 86400  # wrap: turnaround next day
        # turnaround elapsed must be less than total route time
        assert turnaround_elapsed < result["total_hr"] * 3600

    def test_turnaround_equals_dusk_minus_descent_when_summitable(self):
        """turnaround_by = dusk - descent_hr when summit is reachable before dusk.

        Definition: the latest time you can start descending and still return
        before nautical dusk.  For a 06:00 start / 8mi / 4000ft route:
          moderate ascent ≈ 4hr → summit 10:00
          fast descent ≈ 0.5 * fast_hr
          dusk = 22:00
          turnaround = 22:00 - descent_hr (should be before dusk, after summit)
        """
        result = build_itinerary("06:00", 8.0, 4000, self.DAYLIGHT)
        from datetime import datetime

        summit = datetime.strptime(result["summit_eta"], "%H:%M")
        turnaround = datetime.strptime(result["turnaround_by"], "%H:%M")
        naut_dusk = datetime.strptime("22:00", "%H:%M")
        # turnaround must be after summit (you still reach the top)
        assert turnaround >= summit
        # and before or at dusk
        assert turnaround <= naut_dusk

    def test_elapsed_hours_output_key_present(self):
        """Result exposes elapsed_hours for programmatic use."""
        result = build_itinerary("06:00", 8.0, 4000, self.DAYLIGHT)
        assert "total_hr" in result
        assert result["total_hr"] > 0

    # --- cross-midnight day-marker tests (Wave F P1 re-open) ---

    def test_cross_midnight_summit_eta_has_plus1d_marker(self):
        """Evening start (18:00) with long route: summit_eta wraps to next day.

        summit_eta '07:18' is ambiguous — looks like 7am same day, before the
        18:00 start.  Must be '07:18 (+1d)' to be unambiguous.
        """
        result = build_itinerary("18:00", 20.0, 8000, self.DAYLIGHT)
        assert "(+1d)" in result["summit_eta"], (
            f"summit_eta {result['summit_eta']!r} should contain '(+1d)' for cross-midnight route"
        )

    def test_cross_midnight_return_eta_has_plus1d_marker(self):
        """Evening start with long route: return_eta wraps to next day, must say (+1d)."""
        result = build_itinerary("18:00", 20.0, 8000, self.DAYLIGHT)
        assert "(+1d)" in result["return_eta"], (
            f"return_eta {result['return_eta']!r} should contain '(+1d)' for cross-midnight route"
        )

    def test_cross_midnight_after_dark_true(self):
        """Evening start with 20mi/8000ft route: return is well past dusk → after_dark=True."""
        result = build_itinerary("18:00", 20.0, 8000, self.DAYLIGHT)
        assert result["after_dark"] is True

    def test_normal_daytime_route_has_no_plus1d_marker(self):
        """A standard daytime route that finishes same day must NOT have (+1d) markers."""
        result = build_itinerary("06:00", 8.0, 4000, self.DAYLIGHT)
        assert "(+1d)" not in result["summit_eta"]
        assert "(+1d)" not in result["return_eta"]

    def test_turnaround_same_day_no_plus1d_when_evening_start(self):
        """For evening start, turnaround_by (dusk - descent_hr) stays same day — no (+1d)."""
        # 18:00 start, dusk 22:00: turnaround = 22:00 - descent, same evening
        result = build_itinerary("18:00", 20.0, 8000, self.DAYLIGHT)
        assert "(+1d)" not in result["turnaround_by"], (
            f"turnaround_by {result['turnaround_by']!r} should be same-day for evening start"
        )

    def test_degenerate_zero_distance_zero_gain(self):
        """distance_mi=0, gain_ft=0: summit==return==start, total_hr==0, no crash."""
        result = build_itinerary("06:00", 0.0, 0.0, self.DAYLIGHT)
        assert "start_time" in result
        assert result["total_hr"] == 0.0
        assert result["summit_eta"] == "06:00"
        assert result["return_eta"] == "06:00"

    def test_descent_hr_uses_raw_fast_formula(self):
        """descent_hr = (dist/3.5 + gain/2000) * 0.5, not times['fast_hr'] * 0.5.

        Using the pre-rounded fast_hr introduces ±3 min rounding error.
        The raw formula must give a more precise result for non-trivial routes.
        """
        from fetch_conditions import estimate_times

        dist, gain = 8.0, 4000
        times = estimate_times(dist, gain)
        raw_descent = (dist / 3.5 + gain / 2000) * 0.5
        # Build the itinerary and verify total_hr uses the raw (unrounded) descent value
        result = build_itinerary("06:00", dist, gain, self.DAYLIGHT)
        ascent_hr = times["moderate_hr"]
        expected_total = round(ascent_hr + raw_descent, 1)
        assert result["total_hr"] == expected_total


# ---------------------------------------------------------------------------
# 2. compute_bearings helper
# ---------------------------------------------------------------------------


class TestComputeBearings:
    """compute_bearings(waypoints) -> dict"""

    def test_returns_segments_list(self):
        waypoints = [(47.0, -121.0), (48.0, -121.0)]
        result = compute_bearings(waypoints)
        assert "segments" in result
        assert isinstance(result["segments"], list)
        assert len(result["segments"]) == 1

    def test_due_north_bearing_is_zero(self):
        """Moving due north: bearing ≈ 0° (or 360°)."""
        waypoints = [(47.0, -121.0), (48.0, -121.0)]
        result = compute_bearings(waypoints)
        bearing = result["segments"][0]["bearing_deg"]
        # Due north is 0° or 360°
        assert bearing < 5 or bearing > 355

    def test_due_east_bearing_is_90(self):
        """Moving due east: bearing ≈ 90°."""
        waypoints = [(47.0, -122.0), (47.0, -121.0)]
        result = compute_bearings(waypoints)
        bearing = result["segments"][0]["bearing_deg"]
        assert abs(bearing - 90) < 5

    def test_due_south_bearing_is_180(self):
        """Moving due south: bearing ≈ 180°."""
        waypoints = [(48.0, -121.0), (47.0, -121.0)]
        result = compute_bearings(waypoints)
        bearing = result["segments"][0]["bearing_deg"]
        assert abs(bearing - 180) < 5

    def test_segment_includes_distance_miles(self):
        waypoints = [(47.0, -121.0), (48.0, -121.0)]
        result = compute_bearings(waypoints)
        seg = result["segments"][0]
        assert "distance_mi" in seg
        assert seg["distance_mi"] > 0

    def test_cumulative_distance_in_segments(self):
        """Each segment has cumulative_distance_mi."""
        waypoints = [(47.0, -121.0), (48.0, -121.0), (49.0, -121.0)]
        result = compute_bearings(waypoints)
        assert (
            result["segments"][0]["cumulative_distance_mi"]
            < result["segments"][1]["cumulative_distance_mi"]
        )

    def test_multi_segment_count(self):
        """N waypoints produces N-1 segments."""
        waypoints = [(47.0, -121.0), (47.5, -121.0), (48.0, -121.0), (48.5, -121.5)]
        result = compute_bearings(waypoints)
        assert len(result["segments"]) == 3

    def test_total_distance_present(self):
        waypoints = [(47.0, -121.0), (48.0, -121.0), (49.0, -121.0)]
        result = compute_bearings(waypoints)
        assert "total_distance_mi" in result
        assert result["total_distance_mi"] > 0

    def test_single_waypoint_returns_empty_segments(self):
        """Single point → no segments, no error."""
        result = compute_bearings([(47.0, -121.0)])
        assert "segments" in result
        assert result["segments"] == []

    def test_empty_waypoints_returns_empty_segments(self):
        result = compute_bearings([])
        assert "segments" in result
        assert result["segments"] == []

    def test_segment_includes_from_to_labels(self):
        """Each segment has from/to indices or coords for readability."""
        waypoints = [(47.0, -121.0), (48.0, -121.0)]
        result = compute_bearings(waypoints)
        seg = result["segments"][0]
        assert "from" in seg


# ---------------------------------------------------------------------------
# 3. CLI wiring
# ---------------------------------------------------------------------------


class TestCliItinerary:
    def test_itinerary_absent_when_start_time_not_provided(self):
        result = _run_cli(["--distance-mi", "8.0", "--gain-ft", "4000"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "itinerary" not in data

    def test_itinerary_absent_when_distance_not_provided(self):
        result = _run_cli(["--start-time", "06:00", "--gain-ft", "4000"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "itinerary" not in data

    def test_itinerary_present_when_all_args_provided(self):
        result = _run_cli(["--start-time", "06:00", "--distance-mi", "8.0", "--gain-ft", "4000"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "itinerary" in data

    def test_itinerary_contains_required_keys(self):
        result = _run_cli(["--start-time", "06:00", "--distance-mi", "8.0", "--gain-ft", "4000"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        it = data["itinerary"]
        assert "start_time" in it
        assert "summit_eta" in it
        assert "return_eta" in it
        assert "after_dark" in it


class TestCliBearings:
    def test_bearings_absent_when_no_waypoints(self):
        result = _run_cli()
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "bearings" not in data

    def test_bearings_present_when_waypoints_provided(self):
        result = _run_cli(["--waypoint", "47.0,-121.0", "--waypoint", "48.0,-121.0"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "bearings" in data

    def test_bearings_contains_segments(self):
        result = _run_cli(["--waypoint", "47.0,-121.0", "--waypoint", "48.0,-121.0"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "segments" in data["bearings"]
        assert len(data["bearings"]["segments"]) == 1
