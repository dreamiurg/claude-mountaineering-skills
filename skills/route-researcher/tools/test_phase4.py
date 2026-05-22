"""TDD tests for Phase 4 additions: twilight, snow-line, speed models.

No mocks needed for fetch_daylight (uses astral library directly).
estimate_times is pure Python — no mocking.
CLI tests use CliRunner with patched fetchers.
"""

import json
from datetime import datetime
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from fetch_conditions import cli, estimate_times, fetch_daylight

# ---------------------------------------------------------------------------
# 1. Nautical + astronomical twilight in fetch_daylight
# ---------------------------------------------------------------------------


class TestFetchDaylightTwilight:
    LAT, LON = 48.77, -121.81  # Mt Baker area
    # Use winter date — at 48°N in December all twilight levels are well-defined.
    # In summer (June), astronomical twilight may not occur (white nights).
    DATE_WINTER = "2025-12-21"
    DATE_SUMMER = "2025-06-21"

    def test_nautical_dawn_key_present(self):
        """nautical_dawn key is always present (may be None on white-night dates)."""
        result = fetch_daylight(self.LAT, self.LON, self.DATE_WINTER)
        assert "nautical_dawn" in result

    def test_nautical_dusk_key_present(self):
        result = fetch_daylight(self.LAT, self.LON, self.DATE_WINTER)
        assert "nautical_dusk" in result

    def test_astronomical_dawn_key_present(self):
        result = fetch_daylight(self.LAT, self.LON, self.DATE_WINTER)
        assert "astronomical_dawn" in result

    def test_astronomical_dusk_key_present(self):
        result = fetch_daylight(self.LAT, self.LON, self.DATE_WINTER)
        assert "astronomical_dusk" in result

    def test_twilight_order_astronomical_before_nautical_before_civil_before_sunrise(self):
        """On winter date all twilights exist and are ordered correctly."""
        result = fetch_daylight(self.LAT, self.LON, self.DATE_WINTER, "America/Los_Angeles")
        assert "error" not in result
        # All four should be non-None in winter at 48°N
        assert result["astronomical_dawn"] is not None
        assert result["nautical_dawn"] is not None

        def parse_t(s):
            return datetime.strptime(s, "%I:%M %p")

        astro = parse_t(result["astronomical_dawn"])
        naut = parse_t(result["nautical_dawn"])
        civil = parse_t(result["civil_twilight"])
        sunrise = parse_t(result["sunrise"])

        assert astro < naut < civil < sunrise

    def test_sunset_before_civil_dusk_before_nautical_dusk_before_astronomical_dusk(self):
        """On winter date: sunset < civil_dusk < nautical_dusk < astronomical_dusk."""
        result = fetch_daylight(self.LAT, self.LON, self.DATE_WINTER, "America/Los_Angeles")
        assert "error" not in result
        assert result["nautical_dusk"] is not None
        assert result["astronomical_dusk"] is not None

        def parse_t(s):
            return datetime.strptime(s, "%I:%M %p")

        sunset = parse_t(result["sunset"])
        civil_dusk = parse_t(result["civil_dusk"])
        naut_dusk = parse_t(result["nautical_dusk"])
        astro_dusk = parse_t(result["astronomical_dusk"])

        assert sunset < civil_dusk < naut_dusk < astro_dusk

    def test_astronomical_dawn_none_on_white_night_date(self):
        """At 48°N on summer solstice, astronomical twilight may not occur (None is valid)."""
        result = fetch_daylight(self.LAT, self.LON, self.DATE_SUMMER)
        assert "error" not in result
        # Key must be present; value may be None
        assert "astronomical_dawn" in result

    def test_existing_keys_still_present(self):
        """Existing keys (sunrise, sunset, civil_twilight, daylight_hours, timezone) survive."""
        result = fetch_daylight(self.LAT, self.LON, self.DATE_WINTER)
        for key in ("sunrise", "sunset", "civil_twilight", "daylight_hours", "timezone"):
            assert key in result, f"Missing key: {key}"

    def test_error_on_bad_date_still_returns_error_dict(self):
        result = fetch_daylight(self.LAT, self.LON, "not-a-date")
        assert "error" in result


# ---------------------------------------------------------------------------
# 2. Freezing level / snow-line emphasis in fetch_weather output
# ---------------------------------------------------------------------------


class TestFreezingLevelSnowLine:
    """fetch_weather already returns freezing_level_ft per day.
    The new requirement adds snow_line_note and near_summit_flag per day.
    These are derived in the weather output; we test via the cli() with mocked weather.
    """

    MOCK_FORECAST = [
        {
            "date": "2025-06-21",
            "day": "Sat",
            "conditions": "Clear",
            "temp_high_f": 55,
            "temp_low_f": 35,
            "precip_prob": 10,
            "wind_max_mph": 15,
            "freezing_level_ft": 8000,  # well above summit (summit ~10,000 ft)
        },
        {
            "date": "2025-06-22",
            "day": "Sun",
            "conditions": "Clear",
            "temp_high_f": 50,
            "temp_low_f": 30,
            "precip_prob": 5,
            "wind_max_mph": 10,
            "freezing_level_ft": 9500,  # within 2000 ft of summit at 10,000 ft (500 ft gap)
        },
    ]

    def _run_cli_with_mock_weather(self, forecast, elevation_m=3048.0):
        """elevation_m=3048 ≈ 10,000 ft."""
        runner = CliRunner()
        mock_weather = {"forecast": forecast, "timezone": "America/Los_Angeles"}

        with (
            patch("fetch_conditions.fetch_weather", return_value=mock_weather),
            patch("fetch_conditions.fetch_air_quality", return_value={"rating": "good"}),
            patch("fetch_conditions.fetch_daylight", return_value={"sunrise": "5:00 AM"}),
            patch("fetch_conditions.fetch_avalanche", return_value={"region": "north-cascades"}),
            patch("fetch_conditions.fetch_counties", return_value={"counties": []}),
            patch("fetch_conditions.fetch_nearest_hospital", return_value={"hospitals": []}),
            patch("fetch_conditions.fetch_ranger_station", return_value={"stations": []}),
            patch("fetch_conditions.fetch_campgrounds", return_value={"campgrounds": []}),
        ):
            result = runner.invoke(
                cli,
                [
                    "--coordinates",
                    "48.77,-121.81",
                    "--elevation",
                    str(elevation_m),
                    "--peak-name",
                    "Test Peak",
                ],
            )
        return result

    def test_snow_line_note_present_per_day(self):
        """Each forecast day has a snow_line_note string."""
        result = self._run_cli_with_mock_weather(self.MOCK_FORECAST)
        assert result.exit_code == 0
        data = json.loads(result.output)
        for day in data["weather"]["forecast"]:
            assert "snow_line_note" in day, f"Missing snow_line_note in {day}"

    def test_near_summit_flag_false_when_diff_exceeds_2000ft(self):
        """near_summit=False when abs(summit_ft - freezing_ft) > 2000."""
        # freezing=8000 ft, summit=3353m≈11,000 ft → diff=3000 ft > 2000 → False
        result = self._run_cli_with_mock_weather(self.MOCK_FORECAST[:1], elevation_m=3353.0)
        assert result.exit_code == 0
        data = json.loads(result.output)
        day = data["weather"]["forecast"][0]
        assert day["near_summit"] is False

    def test_near_summit_flag_true_when_diff_exactly_2000ft(self):
        """near_summit=True when abs(summit_ft - freezing_ft) == 2000 (boundary is inclusive)."""
        # freezing=8000 ft, summit=3048m≈10,000 ft → diff=2000 ft → within → True
        result = self._run_cli_with_mock_weather(self.MOCK_FORECAST[:1], elevation_m=3048.0)
        assert result.exit_code == 0
        data = json.loads(result.output)
        day = data["weather"]["forecast"][0]
        assert day["near_summit"] is True

    def test_near_summit_flag_true_when_freezing_level_within_2000ft(self):
        """near_summit=True when freezing level is within 2000 ft of summit."""
        # freezing_level_ft=9500, summit≈10,000 ft (3048m), diff=500 ft → within 2000 ft
        result = self._run_cli_with_mock_weather(self.MOCK_FORECAST[1:], elevation_m=3048.0)
        assert result.exit_code == 0
        data = json.loads(result.output)
        day = data["weather"]["forecast"][0]
        assert day["near_summit"] is True

    def test_snow_line_note_mentions_elevation(self):
        """snow_line_note contains a numeric elevation reference."""
        result = self._run_cli_with_mock_weather(self.MOCK_FORECAST[:1])
        assert result.exit_code == 0
        data = json.loads(result.output)
        note = data["weather"]["forecast"][0]["snow_line_note"]
        # Should contain a number (the freezing level elevation)
        assert any(ch.isdigit() for ch in note)

    def test_missing_freezing_level_handled_gracefully(self):
        """Day with freezing_level_ft=None doesn't crash."""
        forecast = [{**self.MOCK_FORECAST[0], "freezing_level_ft": None}]
        result = self._run_cli_with_mock_weather(forecast)
        assert result.exit_code == 0
        data = json.loads(result.output)
        day = data["weather"]["forecast"][0]
        assert "snow_line_note" in day


# ---------------------------------------------------------------------------
# 3. estimate_times pure helper
# ---------------------------------------------------------------------------


class TestEstimateTimes:
    def test_returns_dict_with_roped_and_unroped_keys(self):
        result = estimate_times(5.0, 3000)
        assert "roped_hr" in result
        assert "unroped_hr" in result

    def test_roped_uses_1_mph_pace(self):
        """Roped time = distance_mi / 1.0 mi/hr."""
        result = estimate_times(4.0, 1000)
        assert result["roped_hr"] == pytest.approx(4.0)

    def test_unroped_uses_1000_ft_per_hr_gain(self):
        """Unroped time = gain_ft / 1000 ft/hr."""
        result = estimate_times(2.0, 2000)
        assert result["unroped_hr"] == pytest.approx(2.0)

    def test_roped_uses_slower_of_distance_and_gain(self):
        """Roped = max(distance/1.0, gain/1000) to account for whichever is limiting."""
        # distance=2 mi → 2 hr; gain=4000 ft → 4 hr: roped should be 4 hr
        result = estimate_times(2.0, 4000)
        assert result["roped_hr"] == pytest.approx(4.0)

    def test_existing_pacing_tiers_still_present(self):
        """fast, moderate, leisurely keys still returned."""
        result = estimate_times(5.0, 3000)
        for key in ("fast_hr", "moderate_hr", "leisurely_hr"):
            assert key in result, f"Missing pacing key: {key}"

    def test_zero_gain_handled(self):
        """Zero gain doesn't divide by zero or crash."""
        result = estimate_times(3.0, 0)
        assert "roped_hr" in result
        assert "unroped_hr" in result

    def test_zero_distance_handled(self):
        result = estimate_times(0.0, 1000)
        assert "roped_hr" in result


# ---------------------------------------------------------------------------
# 4. CLI wiring — time_estimates key
# ---------------------------------------------------------------------------


class TestCliTimeEstimates:
    def _run_cli(self, extra_args=None):
        runner = CliRunner()
        base_args = [
            "--coordinates",
            "48.77,-121.81",
            "--elevation",
            "3286",
            "--peak-name",
            "Mt Baker",
        ]
        with (
            patch(
                "fetch_conditions.fetch_weather", return_value={"forecast": [], "timezone": None}
            ),
            patch("fetch_conditions.fetch_air_quality", return_value={"rating": "good"}),
            patch("fetch_conditions.fetch_daylight", return_value={"sunrise": "5:00 AM"}),
            patch("fetch_conditions.fetch_avalanche", return_value={"region": "north-cascades"}),
            patch("fetch_conditions.fetch_counties", return_value={"counties": []}),
            patch("fetch_conditions.fetch_nearest_hospital", return_value={"hospitals": []}),
            patch("fetch_conditions.fetch_ranger_station", return_value={"stations": []}),
            patch("fetch_conditions.fetch_campgrounds", return_value={"campgrounds": []}),
        ):
            return runner.invoke(cli, base_args + (extra_args or []))

    def test_time_estimates_absent_when_args_not_provided(self):
        result = self._run_cli()
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "time_estimates" not in data

    def test_time_estimates_present_when_both_args_provided(self):
        result = self._run_cli(["--distance-mi", "6.0", "--gain-ft", "4500"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "time_estimates" in data

    def test_time_estimates_contains_roped_and_unroped(self):
        result = self._run_cli(["--distance-mi", "6.0", "--gain-ft", "4500"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        te = data["time_estimates"]
        assert "roped_hr" in te
        assert "unroped_hr" in te

    def test_time_estimates_absent_when_only_distance_provided(self):
        """Both args required — only distance should not emit the key."""
        result = self._run_cli(["--distance-mi", "6.0"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "time_estimates" not in data

    def test_time_estimates_absent_when_only_gain_provided(self):
        result = self._run_cli(["--gain-ft", "4500"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "time_estimates" not in data
