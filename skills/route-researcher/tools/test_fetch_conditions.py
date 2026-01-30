"""Tests for fetch_conditions.py

These are integration tests that make live API calls.
Skip by default unless RUN_INTEGRATION_TESTS=1 is set.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

# Get absolute path to the tools directory and script
TOOLS_DIR = Path(__file__).parent
SCRIPT = TOOLS_DIR / "fetch_conditions.py"

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Requires live network access to external APIs. Set RUN_INTEGRATION_TESTS=1 to run.",
)


def test_fetch_conditions_returns_valid_json():
    """Test that fetch_conditions returns valid JSON with expected structure."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            str(SCRIPT),
            "--coordinates",
            "47.4502,-121.4135",
            "--elevation",
            "1353",
            "--peak-name",
            "Mount Si",
        ],
        capture_output=True,
        text=True,
        cwd=str(TOOLS_DIR),
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"

    data = json.loads(result.stdout)

    # Check required keys exist
    assert "weather" in data
    assert "air_quality" in data
    assert "daylight" in data
    assert "avalanche" in data
    assert "gaps" in data

    # Check weather structure
    assert "forecast" in data["weather"]
    assert isinstance(data["weather"]["forecast"], list)


def test_fetch_conditions_weather_forecast_structure():
    """Test that weather forecast has expected fields."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            str(SCRIPT),
            "--coordinates",
            "47.4502,-121.4135",
            "--elevation",
            "1353",
            "--peak-name",
            "Mount Si",
        ],
        capture_output=True,
        text=True,
        cwd=str(TOOLS_DIR),
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)

    if data["weather"]["forecast"]:  # If we got forecast data
        day = data["weather"]["forecast"][0]
        assert "date" in day
        assert "day" in day
        assert "conditions" in day
        assert "temp_high_f" in day or "error" in data["weather"]


def test_fetch_conditions_handles_invalid_coords_gracefully():
    """Test graceful handling of edge case coordinates."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            str(SCRIPT),
            "--coordinates",
            "0,0",
            "--elevation",
            "0",
            "--peak-name",
            "Invalid Peak",
        ],
        capture_output=True,
        text=True,
        cwd=str(TOOLS_DIR),
    )

    # Should still return valid JSON (graceful degradation)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "gaps" in data


def test_fetch_conditions_with_peak_id():
    """Test that peakbagger data is fetched when peak_id provided."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            str(SCRIPT),
            "--coordinates",
            "47.4502,-121.4135",
            "--elevation",
            "1353",
            "--peak-name",
            "Mount Si",
            "--peak-id",
            "2630",
        ],
        capture_output=True,
        text=True,
        cwd=str(TOOLS_DIR),
        timeout=120,  # peakbagger-cli can be slow
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "peakbagger" in data
