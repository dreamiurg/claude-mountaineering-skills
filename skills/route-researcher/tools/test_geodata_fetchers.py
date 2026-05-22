"""Unit tests for Phase 1 geodata fetchers in fetch_conditions.py.

All HTTP calls are mocked — no real network access required.
"""

import json
from unittest.mock import MagicMock, patch

from fetch_conditions import (
    _OVERPASS_HEADERS,
    fetch_campgrounds,
    fetch_counties,
    fetch_nearest_hospital,
    fetch_ranger_station,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_httpx_post(json_body: dict) -> MagicMock:
    """Return a context-manager mock for httpx.Client that returns json_body on .post()."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = json_body

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = mock_response
    return mock_client


def _mock_httpx_get(json_body: dict) -> MagicMock:
    """Return a context-manager mock for httpx.Client that returns json_body on .get()."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = json_body

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = mock_response
    return mock_client


# ---------------------------------------------------------------------------
# fetch_counties
# ---------------------------------------------------------------------------


class TestFetchCounties:
    FCC_RESPONSE = {
        "results": [
            {
                "county_name": "King County",
                "county_fips": "53033",
                "state_name": "Washington",
                "state_code": "WA",
            }
        ]
    }

    def test_happy_path_summit_only_returns_county(self):
        """With only summit coords, returns the summit county."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_get(self.FCC_RESPONSE)
            result = fetch_counties((48.77, -121.81), None)

        assert "counties" in result
        assert len(result["counties"]) >= 1
        county = result["counties"][0]
        assert county["county_name"] == "King County"
        assert county["county_fips"] == "53033"
        assert county["state_name"] == "Washington"

    def test_happy_path_with_trailhead_samples_line(self):
        """With trailhead + summit, samples multiple points along the line."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_get(self.FCC_RESPONSE)
            result = fetch_counties((47.44, -121.41), (48.77, -121.81))

        assert "counties" in result
        assert result["sampled"] is True
        assert result["sample_points"] == 25

    def test_deduplication_by_fips(self):
        """Duplicate FIPS codes across sampled points are deduplicated."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_get(self.FCC_RESPONSE)
            result = fetch_counties((47.44, -121.41), (48.77, -121.81))

        fips_list = [c["county_fips"] for c in result["counties"]]
        assert len(fips_list) == len(set(fips_list)), "Duplicate FIPS found"

    def test_network_error_returns_error_dict(self):
        """Network failure returns a dict with error key (no exception raised)."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = Exception("Connection refused")
            mock_cls.return_value = mock_client

            result = fetch_counties((48.77, -121.81), None)

        assert "error" in result

    def test_empty_results_handled(self):
        """Empty FCC results list handled without error."""
        empty = {"results": []}
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_get(empty)
            result = fetch_counties((48.77, -121.81), None)

        assert "counties" in result
        assert result["counties"] == []

    def test_scans_all_points_on_success(self):
        """Same-county successes must NOT early-exit — a route can re-enter a new
        county after a long stretch, so every sample point is queried.
        """
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_client = _mock_httpx_get(self.FCC_RESPONSE)
            mock_cls.return_value = mock_client
            fetch_counties((47.44, -121.41), (48.77, -121.81), n_samples=25)

        assert mock_client.get.call_count == 25

    def test_early_exit_after_five_consecutive_errors(self):
        """Five consecutive per-point network errors trigger the stale early-exit.

        A fully-down FCC API must not cause 25 × 30s timeouts.
        """
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = Exception("Connection refused")
            mock_cls.return_value = mock_client

            fetch_counties((47.44, -121.41), (48.77, -121.81), n_samples=25)

        assert mock_client.get.call_count <= 7


# ---------------------------------------------------------------------------
# fetch_nearest_hospital
# ---------------------------------------------------------------------------

OVERPASS_HOSPITAL_RESPONSE = {
    "elements": [
        {
            "type": "node",
            "id": 1,
            "lat": 48.42,
            "lon": -122.33,
            "tags": {
                "name": "PeaceHealth St. Joseph",
                "amenity": "hospital",
                "emergency": "yes",
                "phone": "+1-360-734-5400",
                "website": "https://www.peacehealth.org/st-joseph",
                "addr:housenumber": "2901",
                "addr:street": "Squalicum Pkwy",
                "addr:city": "Bellingham",
                "addr:state": "WA",
            },
        },
        {
            "type": "way",
            "id": 2,
            "center": {"lat": 48.51, "lon": -122.11},
            "tags": {
                "name": "Island Hospital",
                "amenity": "hospital",
            },
        },
    ]
}


class TestFetchNearestHospital:
    def test_happy_path_returns_top_hospitals(self):
        """Returns list of hospitals with required fields."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post(OVERPASS_HOSPITAL_RESPONSE)
            result = fetch_nearest_hospital(48.77, -121.81)

        assert "hospitals" in result
        assert len(result["hospitals"]) >= 1
        h = result["hospitals"][0]
        assert "name" in h
        assert "distance_miles" in h

    def test_prefers_emergency_yes(self):
        """Hospital with emergency=yes is ranked first."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post(OVERPASS_HOSPITAL_RESPONSE)
            result = fetch_nearest_hospital(48.77, -121.81)

        assert result["hospitals"][0]["name"] == "PeaceHealth St. Joseph"

    def test_way_element_uses_center(self):
        """Way elements use the center lat/lon."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post(OVERPASS_HOSPITAL_RESPONSE)
            result = fetch_nearest_hospital(48.77, -121.81)

        names = [h["name"] for h in result["hospitals"]]
        assert "Island Hospital" in names

    def test_phone_included_when_present(self):
        """Phone number is included when available in tags."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post(OVERPASS_HOSPITAL_RESPONSE)
            result = fetch_nearest_hospital(48.77, -121.81)

        peace = next(h for h in result["hospitals"] if h["name"] == "PeaceHealth St. Joseph")
        assert peace.get("phone") == "+1-360-734-5400"

    def test_website_address_and_coords_surfaced(self):
        """website, composed address, and lat/lon are surfaced for linking."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post(OVERPASS_HOSPITAL_RESPONSE)
            result = fetch_nearest_hospital(48.77, -121.81)

        peace = next(h for h in result["hospitals"] if h["name"] == "PeaceHealth St. Joseph")
        assert peace["website"] == "https://www.peacehealth.org/st-joseph"
        assert peace["address"] == "2901 Squalicum Pkwy, Bellingham, WA"
        assert peace["lat"] == 48.42 and peace["lon"] == -122.33

    def test_network_error_returns_error_dict(self):
        """Network failure returns error dict without raising."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = Exception("Timeout")
            mock_cls.return_value = mock_client

            result = fetch_nearest_hospital(48.77, -121.81)

        assert "error" in result

    def test_empty_elements_handled(self):
        """Empty Overpass result handled without error."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post({"elements": []})
            result = fetch_nearest_hospital(48.77, -121.81)

        assert "hospitals" in result
        assert result["hospitals"] == []


class TestOverpassHeaders:
    """_OVERPASS_HEADERS sent on every Overpass POST (prevents 406 from overpass-api.de)."""

    def test_overpass_headers_has_user_agent(self):
        """_OVERPASS_HEADERS must include a User-Agent identifying this project."""
        assert "User-Agent" in _OVERPASS_HEADERS
        assert "claude-mountaineering-skills" in _OVERPASS_HEADERS["User-Agent"]

    def test_overpass_headers_has_accept_json(self):
        """_OVERPASS_HEADERS must include Accept: application/json."""
        assert _OVERPASS_HEADERS.get("Accept") == "application/json"

    def test_hospital_query_sends_overpass_headers(self):
        """fetch_nearest_hospital passes _OVERPASS_HEADERS to httpx.Client constructor."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post({"elements": []})
            fetch_nearest_hospital(48.77, -121.81)

        _, kwargs = mock_cls.call_args
        assert kwargs.get("headers") == _OVERPASS_HEADERS


# ---------------------------------------------------------------------------
# fetch_ranger_station
# ---------------------------------------------------------------------------

OVERPASS_RANGER_RESPONSE = {
    "elements": [
        {
            "type": "node",
            "id": 10,
            "lat": 48.65,
            "lon": -121.95,
            "tags": {
                "name": "Mt Baker Ranger District Office",
                "amenity": "ranger_station",
            },
        }
    ]
}

USFS_DISTRICT_RESPONSE = {
    "features": [
        {
            "attributes": {
                "districtname": "Mt Baker Ranger District",
                "forestname": "Mt Baker-Snoqualmie National Forest",
                "region": "R6",
            }
        }
    ]
}

USFS_EMPTY_RESPONSE: dict[str, list] = {"features": []}


class TestFetchRangerStation:
    def test_happy_path_returns_station_and_district(self):
        """Returns OSM station plus USFS administrative district."""

        def _get_side_effect(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            if "arcx" in url or "fs.usda.gov" in url:
                mock_resp.json.return_value = USFS_DISTRICT_RESPONSE
            else:
                mock_resp.json.return_value = USFS_EMPTY_RESPONSE
            return mock_resp

        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=OVERPASS_RANGER_RESPONSE),
            )
            mock_client.get.side_effect = _get_side_effect
            mock_cls.return_value = mock_client

            result = fetch_ranger_station(48.77, -121.81)

        assert "stations" in result
        assert "admin_district" in result

    def test_usfs_failure_still_returns_osm_data(self):
        """USFS ArcGIS failure is soft — OSM data still returned."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=OVERPASS_RANGER_RESPONSE),
            )
            mock_client.get.side_effect = Exception("USFS down")
            mock_cls.return_value = mock_client

            result = fetch_ranger_station(48.77, -121.81)

        # USFS failure is soft: no error key, OSM stations still present
        assert "error" not in result
        assert "stations" in result

    def test_network_error_returns_error_dict(self):
        """Full network failure returns error dict without raising."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = Exception("Connection refused")
            mock_client.get.side_effect = Exception("Connection refused")
            mock_cls.return_value = mock_client

            result = fetch_ranger_station(48.77, -121.81)

        assert "error" in result

    def test_empty_osm_still_returns_district(self):
        """Empty OSM result still tries USFS district lookup."""

        def _get_side_effect(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = USFS_DISTRICT_RESPONSE
            return mock_resp

        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value={"elements": []}),
            )
            mock_client.get.side_effect = _get_side_effect
            mock_cls.return_value = mock_client

            result = fetch_ranger_station(48.77, -121.81)

        assert "stations" in result
        assert "admin_district" in result


# ---------------------------------------------------------------------------
# fetch_campgrounds
# ---------------------------------------------------------------------------

OVERPASS_CAMPGROUND_RESPONSE = {
    "elements": [
        {
            "type": "node",
            "id": 20,
            "lat": 48.70,
            "lon": -121.85,
            "tags": {
                "name": "Douglas Fir Campground",
                "tourism": "camp_site",
                "camp_type": "established",
            },
        },
        {
            "type": "way",
            "id": 21,
            "center": {"lat": 48.68, "lon": -121.80},
            "tags": {
                "name": "Horseshoe Cove Campground",
                "tourism": "camp_site",
            },
        },
    ]
}


class TestFetchCampgrounds:
    def test_happy_path_returns_campgrounds(self):
        """Returns list of campgrounds with name, coords, distance."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post(OVERPASS_CAMPGROUND_RESPONSE)
            result = fetch_campgrounds(48.77, -121.81)

        assert "campgrounds" in result
        assert len(result["campgrounds"]) >= 1
        c = result["campgrounds"][0]
        assert "name" in c
        assert "distance_miles" in c

    def test_backcountry_gap_noted(self):
        """Result includes a note that backcountry camps are not covered."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post(OVERPASS_CAMPGROUND_RESPONSE)
            result = fetch_campgrounds(48.77, -121.81)

        note = result.get("note", "") + json.dumps(result)
        assert "backcountry" in note.lower() or "trip report" in note.lower()

    def test_way_element_uses_center(self):
        """Way elements use the center lat/lon."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post(OVERPASS_CAMPGROUND_RESPONSE)
            result = fetch_campgrounds(48.77, -121.81)

        names = [c["name"] for c in result["campgrounds"]]
        assert "Horseshoe Cove Campground" in names

    def test_network_error_returns_error_dict(self):
        """Network failure returns error dict without raising."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = Exception("Timeout")
            mock_cls.return_value = mock_client

            result = fetch_campgrounds(48.77, -121.81)

        assert "error" in result

    def test_empty_elements_handled(self):
        """Empty Overpass result handled without error."""
        with patch("fetch_conditions.httpx.Client") as mock_cls:
            mock_cls.return_value = _mock_httpx_post({"elements": []})
            result = fetch_campgrounds(48.77, -121.81)

        assert "campgrounds" in result
        assert result["campgrounds"] == []


# ---------------------------------------------------------------------------
# CLI integration — new output keys wired into cli()
# ---------------------------------------------------------------------------


class TestCliOutputKeys:
    """Verify the new keys appear in cli() output dict."""

    def test_output_contains_new_geodata_keys(self):
        """cli() output dict includes counties, nearest_hospital, ranger_station, campgrounds."""
        from click.testing import CliRunner
        from fetch_conditions import cli

        runner = CliRunner()

        # Patch all 4 new fetchers to return minimal valid dicts
        with (
            patch("fetch_conditions.fetch_counties", return_value={"counties": []}),
            patch("fetch_conditions.fetch_nearest_hospital", return_value={"hospitals": []}),
            patch("fetch_conditions.fetch_ranger_station", return_value={"stations": []}),
            patch("fetch_conditions.fetch_campgrounds", return_value={"campgrounds": []}),
            patch("fetch_conditions.fetch_weather", return_value={"forecast": []}),
            patch("fetch_conditions.fetch_air_quality", return_value={"rating": "good"}),
            patch("fetch_conditions.fetch_daylight", return_value={"sunrise": "6:00 AM"}),
            patch("fetch_conditions.fetch_avalanche", return_value={"region": "north-cascades"}),
        ):
            result = runner.invoke(
                cli,
                [
                    "--coordinates",
                    "48.77,-121.81",
                    "--elevation",
                    "3286",
                    "--peak-name",
                    "Mt Baker",
                ],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "counties" in data
        assert "nearest_hospital" in data
        assert "ranger_station" in data
        assert "campgrounds" in data
        assert "gaps" in data

    def test_trailhead_option_accepted(self):
        """--trailhead option is accepted by cli()."""
        from click.testing import CliRunner
        from fetch_conditions import cli

        runner = CliRunner()

        with (
            patch("fetch_conditions.fetch_counties", return_value={"counties": []}),
            patch("fetch_conditions.fetch_nearest_hospital", return_value={"hospitals": []}),
            patch("fetch_conditions.fetch_ranger_station", return_value={"stations": []}),
            patch("fetch_conditions.fetch_campgrounds", return_value={"campgrounds": []}),
            patch("fetch_conditions.fetch_weather", return_value={"forecast": []}),
            patch("fetch_conditions.fetch_air_quality", return_value={"rating": "good"}),
            patch("fetch_conditions.fetch_daylight", return_value={"sunrise": "6:00 AM"}),
            patch("fetch_conditions.fetch_avalanche", return_value={"region": "north-cascades"}),
        ):
            result = runner.invoke(
                cli,
                [
                    "--coordinates",
                    "48.77,-121.81",
                    "--elevation",
                    "3286",
                    "--peak-name",
                    "Mt Baker",
                    "--trailhead",
                    "48.60,-121.70",
                ],
            )

        assert result.exit_code == 0

    def test_fetcher_error_appended_to_gaps(self):
        """When a fetcher returns an error, it is appended to gaps."""
        from click.testing import CliRunner
        from fetch_conditions import cli

        runner = CliRunner()

        with (
            patch("fetch_conditions.fetch_counties", return_value={"error": "API down"}),
            patch("fetch_conditions.fetch_nearest_hospital", return_value={"hospitals": []}),
            patch("fetch_conditions.fetch_ranger_station", return_value={"stations": []}),
            patch("fetch_conditions.fetch_campgrounds", return_value={"campgrounds": []}),
            patch("fetch_conditions.fetch_weather", return_value={"forecast": []}),
            patch("fetch_conditions.fetch_air_quality", return_value={"rating": "good"}),
            patch("fetch_conditions.fetch_daylight", return_value={"sunrise": "6:00 AM"}),
            patch("fetch_conditions.fetch_avalanche", return_value={"region": "north-cascades"}),
        ):
            result = runner.invoke(
                cli,
                [
                    "--coordinates",
                    "48.77,-121.81",
                    "--elevation",
                    "3286",
                    "--peak-name",
                    "Mt Baker",
                ],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        gap_sources = [g.get("source", "") for g in data["gaps"]]
        assert any("count" in s.lower() or "FCC" in s or "Counties" in s for s in gap_sources)
