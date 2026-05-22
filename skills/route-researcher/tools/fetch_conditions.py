#!/usr/bin/env python3
"""Unified conditions fetcher - weather, air quality, daylight, avalanche.

Fetches all environmental/conditions data for a mountain peak from various APIs.
Returns unified JSON matching the data contract for the route-researcher skill.
"""

import json
import math
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Any

import click
import httpx

OPEN_METEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

WEATHER_CODES = {
    0: ("Clear", "☀️"),
    1: ("Partly cloudy", "⛅"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Fog", "🌫️"),
    51: ("Light drizzle", "🌧️"),
    53: ("Drizzle", "🌧️"),
    55: ("Heavy drizzle", "🌧️"),
    61: ("Light rain", "🌧️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    71: ("Light snow", "❄️"),
    73: ("Snow", "❄️"),
    75: ("Heavy snow", "❄️"),
    80: ("Light showers", "🌧️"),
    81: ("Showers", "🌧️"),
    82: ("Heavy showers", "🌧️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Thunderstorm with hail", "⛈️"),
}

PEAKBAGGER_CMD = [
    "uvx",
    "--from",
    "git+https://github.com/dreamiurg/peakbagger-cli.git@v1.10.0",
    "peakbagger",
]


def fetch_weather(lat: float, lon: float, elevation_m: float, days: int = 7) -> dict[str, Any]:
    """Fetch weather forecast from Open-Meteo API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "elevation": elevation_m,
        "daily": (
            "temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,wind_speed_10m_max,weather_code"
        ),
        "hourly": "freezing_level_height",
        "timezone": "auto",
        "forecast_days": days,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(OPEN_METEO_WEATHER_URL, params=params)
            response.raise_for_status()
            data = response.json()

            forecast = []
            daily = data.get("daily", {})
            dates = daily.get("time", [])

            for i, date_str in enumerate(dates):
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                weather_code = daily.get("weather_code", [None])[i]
                conditions, icon = WEATHER_CODES.get(weather_code, ("Unknown", "❓"))

                # Get freezing level (average of hourly values for that day)
                hourly = data.get("hourly", {})
                freezing_levels = hourly.get("freezing_level_height", [])
                day_start = i * 24
                day_end = day_start + 24
                day_freezing = freezing_levels[day_start:day_end] if freezing_levels else []
                # Filter out None values
                day_freezing = [f for f in day_freezing if f is not None]
                avg_freezing_m = sum(day_freezing) / len(day_freezing) if day_freezing else None
                avg_freezing_ft = (
                    round(avg_freezing_m * 3.28084) if avg_freezing_m is not None else None
                )

                # Get temperature values safely
                temp_max_c = daily.get("temperature_2m_max", [None])[i]
                temp_min_c = daily.get("temperature_2m_min", [None])[i]
                wind_max_kmh = daily.get("wind_speed_10m_max", [None])[i]

                forecast.append(
                    {
                        "date": date_str,
                        "day": date_obj.strftime("%a"),
                        "conditions": f"{icon} {conditions}",
                        "temp_high_f": round(temp_max_c * 9 / 5 + 32)
                        if temp_max_c is not None
                        else None,
                        "temp_low_f": round(temp_min_c * 9 / 5 + 32)
                        if temp_min_c is not None
                        else None,
                        "precip_prob": daily.get("precipitation_probability_max", [None])[i],
                        "wind_max_mph": round(wind_max_kmh * 0.621371)
                        if wind_max_kmh is not None
                        else None,
                        "freezing_level_ft": avg_freezing_ft,
                    }
                )

            return {
                "forecast": forecast,
                "timezone": data.get("timezone"),
                "source_url": f"https://open-meteo.com/en/docs#latitude={lat}&longitude={lon}",
            }
    except Exception as e:
        return {"forecast": [], "error": str(e)}


def fetch_air_quality(lat: float, lon: float, days: int = 7) -> dict[str, Any]:
    """Fetch air quality from Open-Meteo API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "us_aqi,pm2_5,pm10",
        "timezone": "auto",
        "forecast_days": days,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(OPEN_METEO_AQ_URL, params=params)
            response.raise_for_status()
            data = response.json()

            hourly = data.get("hourly", {})
            aqi_values = [v for v in hourly.get("us_aqi", []) if v is not None]

            if aqi_values:
                max_aqi = max(aqi_values)
                avg_aqi = sum(aqi_values) / len(aqi_values)

                if avg_aqi <= 50:
                    rating = "good"
                elif avg_aqi <= 100:
                    rating = "moderate"
                elif avg_aqi <= 150:
                    rating = "unhealthy for sensitive groups"
                elif avg_aqi <= 200:
                    rating = "unhealthy"
                else:
                    rating = "very unhealthy"

                concerns = []
                if max_aqi > 100:
                    concerns.append(
                        f"AQI peaks at {int(max_aqi)} - may affect sensitive individuals"
                    )

                return {
                    "aqi_avg": round(avg_aqi),
                    "aqi_max": round(max_aqi),
                    "rating": rating,
                    "concerns": concerns,
                    "source_url": f"https://open-meteo.com/en/docs/air-quality-api#latitude={lat}&longitude={lon}",
                }
            else:
                return {"rating": "unknown", "error": "No AQI data available"}
    except Exception as e:
        return {"rating": "unknown", "error": str(e)}


def fetch_daylight(
    lat: float, lon: float, date_str: str, tz_name: str | None = None
) -> dict[str, Any]:
    """Calculate daylight using astral library.

    Args:
        lat: Latitude
        lon: Longitude
        date_str: Date as YYYY-MM-DD
        tz_name: IANA timezone name (e.g., "America/Los_Angeles"). Defaults to UTC if not provided.
    """
    try:
        import zoneinfo

        from astral import LocationInfo
        from astral.sun import dawn as astral_dawn
        from astral.sun import dusk as astral_dusk
        from astral.sun import sun

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        location = LocationInfo(latitude=lat, longitude=lon)

        # Use provided timezone or fall back to UTC
        try:
            tz = zoneinfo.ZoneInfo(tz_name) if tz_name else zoneinfo.ZoneInfo("UTC")
        except Exception:
            tz = zoneinfo.ZoneInfo("UTC")

        s = sun(location.observer, date=date_obj, tzinfo=tz)

        sunrise = s["sunrise"]
        sunset = s["sunset"]
        civil_dawn = s["dawn"]  # −6° depression
        civil_dusk = s["dusk"]  # −6° depression

        fmt = "%-I:%M %p"

        def _try_twilight(fn, depression):
            """Return formatted time or None if sun never reaches that depression."""
            try:
                t = fn(location.observer, date=date_obj, depression=depression, tzinfo=tz)
                return t.strftime(fmt)
            except Exception:
                return None

        nautical_dawn = _try_twilight(astral_dawn, 12)
        nautical_dusk = _try_twilight(astral_dusk, 12)
        astronomical_dawn = _try_twilight(astral_dawn, 18)
        astronomical_dusk = _try_twilight(astral_dusk, 18)

        daylight = sunset - sunrise
        daylight_hours = daylight.total_seconds() / 3600

        tz_label = tz_name if tz_name else "UTC"
        return {
            "astronomical_dawn": astronomical_dawn,
            "nautical_dawn": nautical_dawn,
            "civil_twilight": civil_dawn.strftime(fmt),
            "sunrise": sunrise.strftime(fmt),
            "sunset": sunset.strftime(fmt),
            "civil_dusk": civil_dusk.strftime(fmt),
            "nautical_dusk": nautical_dusk,
            "astronomical_dusk": astronomical_dusk,
            "daylight_hours": round(daylight_hours, 1),
            "timezone": tz_label,
        }
    except Exception as e:
        return {"error": str(e)}


def _enrich_forecast_snow_line(forecast: list[dict], summit_elevation_ft: float) -> None:
    """Add snow_line_note and near_summit fields to each forecast day (in-place)."""
    for day in forecast:
        fl = day.get("freezing_level_ft")
        if fl is not None:
            note = f"Snow line ~{fl:,} ft (freezing level)"
            diff = abs(summit_elevation_ft - fl)
            near = diff <= 2000
            if near:
                note += f" — within {int(diff):,} ft of summit"
        else:
            note = "Freezing level data unavailable"
            near = False
        day["snow_line_note"] = note
        day["near_summit"] = near


def fetch_avalanche(lat: float, lon: float) -> dict[str, Any]:
    """Get avalanche forecast info (returns URL for manual check).

    NWAC regions are roughly determined by coordinates.
    """
    if 48.0 <= lat <= 48.9 and lon > -122.0:
        region = "mt-baker"
    elif lat > 48.5:
        region = "north-cascades"
    elif lat > 47.0 and lon < -123.0:
        region = "olympics"
    elif lat > 47.5:
        region = "stevens-pass"
    elif lat > 47.0:
        region = "snoqualmie-pass"
    else:
        region = "south-cascades"

    return {
        "region": region,
        "url": f"https://nwac.us/avalanche-forecast/#{region}",
        "note": "Check NWAC for current avalanche danger ratings before entering avalanche terrain",
    }


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in miles between two lat/lon points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _sample_line(
    start: tuple[float, float], end: tuple[float, float], n: int
) -> list[tuple[float, float]]:
    """Return n evenly-spaced points along the line from start to end (inclusive)."""
    if n <= 1:
        return [start]
    points = []
    for i in range(n):
        t = i / (n - 1)
        lat = start[0] + t * (end[0] - start[0])
        lon = start[1] + t * (end[1] - start[1])
        points.append((lat, lon))
    return points


FCC_AREA_URL = "https://geo.fcc.gov/api/census/area"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USFS_DISTRICTS_URL = (
    "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_RangerDistricts_01/MapServer/0/query"
)


def fetch_counties(
    summit: tuple[float, float],
    trailhead: tuple[float, float] | None,
    n_samples: int = 25,
) -> dict[str, Any]:
    """Return counties traversed from trailhead to summit via FCC Area API.

    If trailhead is None, only the summit point is queried and a note is added.
    Deduplicates by county_fips.
    """
    try:
        points = _sample_line(trailhead, summit, n_samples) if trailhead else [summit]
        seen: dict[str, dict] = {}
        errors = 0  # consecutive failed requests (API likely down)
        with httpx.Client(timeout=30.0) as client:
            for lat, lon in points:
                try:
                    resp = client.get(
                        FCC_AREA_URL,
                        params={"lat": float(lat), "lon": float(lon), "format": "json"},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    for r in data.get("results", []):
                        fips = r.get("county_fips")
                        if fips and fips not in seen:
                            seen[fips] = {
                                "county_name": r.get("county_name"),
                                "county_fips": fips,
                                "state_name": r.get("state_name"),
                                "state_code": r.get("state_code"),
                            }
                    errors = 0  # a successful request resets the failure counter
                except Exception:
                    errors += 1
                    if errors >= 5:
                        break  # API appears down; stop hammering it
                    continue  # single-point failure is non-fatal
                # Keep sampling every point on success — a route can re-enter a
                # new county after a long stretch in one, so never early-exit on
                # "no new county" (would miss later boundary crossings).

        if not seen and points:
            return {
                "error": "FCC Area API returned no data for any sampled point.",
                "note": "County lookup failed; check https://geo.fcc.gov/api/census/area",
                "counties": [],
            }

        result: dict[str, Any] = {"counties": list(seen.values())}
        if trailhead:
            result["sampled"] = True
            result["sample_points"] = len(points)
        else:
            result["note"] = (
                "Only summit county returned — provide --trailhead to sample the full route."
            )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "note": "County lookup failed; check FCC Area API.",
            "counties": [],
        }


def _osm_coords(el: dict) -> tuple[float | None, float | None]:
    """Extract lat/lon from a node element or a way/relation with a center."""
    elat = el["lat"] if "lat" in el else (el.get("center") or {}).get("lat")
    elon = el["lon"] if "lon" in el else (el.get("center") or {}).get("lon")
    return elat, elon


def _osm_website(tags: dict) -> str | None:
    """Best website URL from common OSM tags, if any."""
    return tags.get("website") or tags.get("contact:website") or tags.get("url")


def _osm_address(tags: dict) -> str | None:
    """Compose a human address from OSM addr:* tags, if present."""
    if tags.get("addr:full"):
        return tags["addr:full"]
    street = " ".join(p for p in (tags.get("addr:housenumber"), tags.get("addr:street")) if p)
    locality = ", ".join(p for p in (tags.get("addr:city"), tags.get("addr:state")) if p)
    return ", ".join(p for p in (street, locality) if p) or None


_OVERPASS_HEADERS = {
    "User-Agent": (
        "claude-mountaineering-skills/route-researcher "
        "(https://github.com/dreamiurg/claude-mountaineering-skills)"
    ),
    "Accept": "application/json",
}


def _overpass_query(query: str) -> list[dict]:
    """POST query to Overpass API and return elements list.

    Raises on network or HTTP error — callers must catch for graceful degradation.
    """
    with httpx.Client(timeout=35.0, headers=_OVERPASS_HEADERS) as client:
        resp = client.post(OVERPASS_URL, data={"data": query})
        resp.raise_for_status()
        return resp.json().get("elements", [])


def fetch_nearest_hospital(lat: float, lon: float) -> dict[str, Any]:
    """Return nearest hospitals via OSM Overpass, sorted by distance.

    Prefers emergency=yes (sorted first); does not require it.
    Returns top 3 results.
    """
    query = f"""
[out:json][timeout:25];
nwr[amenity=hospital](around:50000,{float(lat)},{float(lon)});
out center tags;
"""
    try:
        elements = _overpass_query(query)
        hospitals = []
        for el in elements:
            tags = el.get("tags", {})
            elat, elon = _osm_coords(el)
            if elat is None or elon is None:
                continue
            entry: dict[str, Any] = {
                "name": tags.get("name", "Unknown hospital"),
                "lat": elat,
                "lon": elon,
                "distance_miles": round(_haversine_miles(lat, lon, elat, elon), 1),
                "emergency": tags.get("emergency"),
            }
            if "phone" in tags:
                entry["phone"] = tags["phone"]
            if _osm_website(tags):
                entry["website"] = _osm_website(tags)
            if _osm_address(tags):
                entry["address"] = _osm_address(tags)
            hospitals.append(entry)

        # Sort: emergency=yes first, then by distance
        hospitals.sort(key=lambda h: (h.get("emergency") != "yes", h["distance_miles"]))
        return {"hospitals": hospitals[:3]}
    except Exception as e:
        return {"error": str(e), "note": "Hospital lookup failed; check OSM Overpass."}


def fetch_ranger_station(lat: float, lon: float) -> dict[str, Any]:
    """Return nearest ranger stations (OSM) plus USFS administrative district name.

    OSM query unions amenity=ranger_station with tourism=information+information=visitor_centre.
    USFS ArcGIS EDW provides the administrative district/forest name (no key required).
    USFS failure is soft — OSM data still returned.
    """
    overpass_query = f"""
[out:json][timeout:25];
(
  nwr[amenity=ranger_station](around:50000,{float(lat)},{float(lon)});
  nwr[tourism=information][information=visitor_centre](around:50000,{float(lat)},{float(lon)});
);
out center tags;
"""
    try:
        elements = _overpass_query(overpass_query)
        stations = []
        for el in elements:
            tags = el.get("tags", {})
            elat, elon = _osm_coords(el)
            if elat is None or elon is None:
                continue
            s_entry: dict[str, Any] = {
                "name": tags.get("name", "Unknown station"),
                "lat": elat,
                "lon": elon,
                "distance_miles": round(_haversine_miles(lat, lon, elat, elon), 1),
            }
            if tags.get("phone"):
                s_entry["phone"] = tags["phone"]
            if _osm_website(tags):
                s_entry["website"] = _osm_website(tags)
            if _osm_address(tags):
                s_entry["address"] = _osm_address(tags)
            stations.append(s_entry)
        stations.sort(key=lambda s: s["distance_miles"])

        result: dict[str, Any] = {"stations": stations[:3]}

        # USFS administrative district (soft — failure just omits district)
        try:
            with httpx.Client(timeout=20.0) as client:
                usfs_resp = client.get(
                    USFS_DISTRICTS_URL,
                    params={
                        "geometry": f"{float(lon)},{float(lat)}",
                        "geometryType": "esriGeometryPoint",
                        "inSR": "4326",
                        "spatialRel": "esriSpatialRelIntersects",
                        "outFields": "districtname,forestname,region",
                        "f": "json",
                        "returnGeometry": "false",
                    },
                )
                usfs_resp.raise_for_status()
                features = usfs_resp.json().get("features", [])
                if features:
                    attrs = features[0].get("attributes", {})
                    result["admin_district"] = {
                        "district_name": attrs.get("districtname"),
                        "forest_name": attrs.get("forestname"),
                        "region": attrs.get("region"),
                    }
        except Exception:
            pass  # USFS failure is non-fatal

        return result
    except Exception as e:
        return {"error": str(e), "note": "Ranger station lookup failed; check OSM Overpass."}


def fetch_campgrounds(lat: float, lon: float) -> dict[str, Any]:
    """Return established campgrounds within ~12 mi (~20 km) via OSM Overpass.

    Note: backcountry/high camps are NOT in any database — they come from
    trip reports and route beta, not this fetcher.
    """
    query = f"""
[out:json][timeout:25];
nwr[tourism=camp_site](around:20000,{float(lat)},{float(lon)});
out center tags;
"""
    try:
        elements = _overpass_query(query)
        campgrounds = []
        for el in elements:
            tags = el.get("tags", {})
            elat, elon = _osm_coords(el)
            if elat is None or elon is None:
                continue
            c_entry: dict[str, Any] = {
                "name": tags.get("name", "Unnamed campground"),
                "lat": elat,
                "lon": elon,
                "distance_miles": round(_haversine_miles(lat, lon, elat, elon), 1),
                "camp_type": tags.get("camp_type"),
                "backcountry": tags.get("backcountry"),
                "operator": tags.get("operator"),
            }
            if _osm_website(tags):
                c_entry["website"] = _osm_website(tags)
            campgrounds.append(c_entry)
        campgrounds.sort(key=lambda c: c["distance_miles"])

        return {
            "campgrounds": campgrounds,
            "note": (
                "Established campgrounds only (OSM data). "
                "Backcountry and high camps are not in any database — "
                "extract from trip reports and route beta."
            ),
        }
    except Exception as e:
        return {"error": str(e), "note": "Campground lookup failed; check OSM Overpass."}


def estimate_times(distance_mi: float, gain_ft: float) -> dict[str, Any]:
    """Estimate travel times using roped/unroped and standard pacing models.

    Roped (glacier): slower of distance/1.0 mph or gain/1000 ft/hr.
    Unroped: gain / 1000 ft/hr.
    Standard tiers use Naismith's rule variants.
    """
    roped_by_distance = distance_mi if distance_mi else 0.0  # 1 mph glacier pace
    roped_by_gain = gain_ft / 1000.0 if gain_ft else 0.0
    roped_hr = max(roped_by_distance, roped_by_gain)
    unroped_hr = gain_ft / 1000.0 if gain_ft else 0.0

    # Standard pacing tiers (distance / pace + gain adjustment)
    fast_hr = round(distance_mi / 3.5 + gain_ft / 2000, 1)
    moderate_hr = round(distance_mi / 2.5 + gain_ft / 1500, 1)
    leisurely_hr = round(distance_mi / 2.0 + gain_ft / 1000, 1)

    return {
        "roped_hr": round(roped_hr, 1),
        "unroped_hr": round(unroped_hr, 1),
        "fast_hr": fast_hr,
        "moderate_hr": moderate_hr,
        "leisurely_hr": leisurely_hr,
        "note": (
            "Roped: ~1 mi/hr on glacier (slower of distance or gain limit). "
            "Unroped: ~1,000 ft/hr gain. "
            "Standard tiers use Naismith-variant pacing."
        ),
    }


def build_itinerary(
    start_time: str,
    distance_mi: float,
    gain_ft: float,
    daylight: dict[str, Any],
) -> dict[str, Any]:
    """Generate a climb timeline from start time, route stats, and daylight.

    Turnaround definition: latest time to begin descent and return before nautical dusk
    (dusk - descent_hr).  If that time is before the summit ETA the route cannot be
    completed before dark, and after_dark=True.

    All arithmetic uses timedelta from start_dt so pre-dawn starts and after-midnight
    finishes are handled correctly without re-parsing wall-clock strings.
    Dusk is anchored to the start date (or day+1 when the dusk time-of-day is earlier
    than start time-of-day, e.g. a 23:00 start with 22:00 dusk).
    """
    fmt_in = "%H:%M"

    def _fmt(dt: datetime, ref: datetime) -> str:
        """Format dt as HH:MM, appending ' (+1d)' when it falls on the next calendar day."""
        s = dt.strftime("%H:%M")
        if dt.date() > ref.date():
            s += " (+1d)"
        return s

    try:
        start_dt = datetime.strptime(start_time, fmt_in)
    except ValueError:
        return {"error": f"Invalid start_time format: {start_time!r}. Use HH:MM."}

    times = estimate_times(distance_mi, gain_ft)

    # Ascent: moderate pace; descent: half of raw fast pace (downhill, unrounded)
    ascent_hr = times["moderate_hr"]
    descent_hr = (distance_mi / 3.5 + gain_ft / 2000) * 0.5  # raw formula avoids rounding error
    total_hr = round(ascent_hr + descent_hr, 1)

    summit_dt = start_dt + timedelta(hours=ascent_hr)
    return_dt = summit_dt + timedelta(hours=descent_hr)

    # Dusk cutoff: prefer nautical_dusk → civil_dusk → sunset → None
    dusk_str = daylight.get("nautical_dusk") or daylight.get("civil_dusk") or daylight.get("sunset")
    dusk_dt = None
    if dusk_str:
        for fmt in ("%I:%M %p", "%H:%M"):
            try:
                dusk_dt = datetime.strptime(dusk_str, fmt)
                break
            except ValueError:
                continue

    if dusk_dt:
        # Anchor dusk to the same calendar date as start.  When the dusk time-of-day
        # is earlier than start (e.g. 23:00 start, 22:00 dusk) it must be day+1.
        if dusk_dt.time() < start_dt.time():
            dusk_dt += timedelta(days=1)

        # Turnaround = latest moment to begin descent and reach the trailhead before dusk.
        turnaround_dt = dusk_dt - timedelta(hours=descent_hr)
        # Clamp: turnaround cannot be before start (edge case: tiny window)
        if turnaround_dt < start_dt:
            turnaround_dt = start_dt
        after_dark = return_dt > dusk_dt
    else:
        turnaround_dt = summit_dt  # no dusk info — use summit as turnaround
        after_dark = False

    return {
        "start_time": start_time,
        "summit_eta": _fmt(summit_dt, start_dt),
        "turnaround_by": _fmt(turnaround_dt, start_dt),
        "return_eta": _fmt(return_dt, start_dt),
        "after_dark": after_dark,
        "dusk_cutoff": dusk_str,
        "total_hr": total_hr,
        "note": (
            "Ascent at moderate pace; descent at fast pace. "
            "Adjust for terrain, conditions, and party speed."
        ),
    }


def compute_bearings(waypoints: list[tuple[float, float]]) -> dict[str, Any]:
    """Return per-segment compass bearings and distances for an ordered list of waypoints.

    Each segment: bearing_deg (0–360), distance_mi, cumulative_distance_mi, from/to indices.
    """
    if len(waypoints) < 2:
        return {"segments": [], "total_distance_mi": 0.0}

    segments = []
    cumulative = 0.0

    for i in range(len(waypoints) - 1):
        lat1, lon1 = float(waypoints[i][0]), float(waypoints[i][1])
        lat2, lon2 = float(waypoints[i + 1][0]), float(waypoints[i + 1][1])

        # Forward azimuth (bearing) using spherical formula
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dl = math.radians(lon2 - lon1)
        x = math.sin(dl) * math.cos(phi2)
        y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dl)
        bearing = (math.degrees(math.atan2(x, y)) + 360) % 360

        dist = _haversine_miles(lat1, lon1, lat2, lon2)
        cumulative += dist

        segments.append(
            {
                "from": i,
                "to": i + 1,
                "bearing_deg": round(bearing, 1),
                "distance_mi": round(dist, 2),
                "cumulative_distance_mi": round(cumulative, 2),
            }
        )

    return {
        "segments": segments,
        "total_distance_mi": round(cumulative, 2),
    }


def run_peakbagger_stats(peak_id: int) -> dict[str, Any]:
    """Run peakbagger-cli to get ascent statistics."""
    try:
        result = subprocess.run(
            [*PEAKBAGGER_CMD, "peak", "stats", str(peak_id), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr.strip() or "Command failed"}
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response: {e}"}
    except Exception as e:
        return {"error": str(e)}


def run_peakbagger_ascents(peak_id: int, within: str = "1y") -> dict[str, Any]:
    """Run peakbagger-cli to get recent ascents."""
    try:
        result = subprocess.run(
            [
                *PEAKBAGGER_CMD,
                "peak",
                "ascents",
                str(peak_id),
                "--format",
                "json",
                "--within",
                within,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr.strip() or "Command failed"}
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response: {e}"}
    except Exception as e:
        return {"error": str(e)}


@click.command()
@click.option("--coordinates", required=True, help="Summit coordinates as lat,lon")
@click.option("--elevation", required=True, type=float, help="Elevation in meters")
@click.option("--peak-name", required=True, help="Peak name")
@click.option("--peak-id", type=int, default=None, help="PeakBagger peak ID (optional)")
@click.option("--date", default=None, help="Date as YYYY-MM-DD (default: today)")
@click.option("--trailhead", default=None, help="Trailhead coordinates as lat,lon (optional)")
@click.option(
    "--distance-mi",
    type=float,
    default=None,
    help="Round-trip distance in miles (for time estimates and itinerary)",
)
@click.option(
    "--gain-ft", type=float, default=None, help="Total elevation gain in feet (for time estimates)"
)
@click.option("--start-time", default=None, help="Planned start time as HH:MM (for itinerary)")
@click.option(
    "--waypoint",
    "waypoints",
    multiple=True,
    help="Waypoint as lat,lon (repeat for multiple; enables navigation bearings)",
)
def cli(
    coordinates: str,
    elevation: float,
    peak_name: str,
    peak_id: int,
    date: str,
    trailhead: str,
    distance_mi: float,
    gain_ft: float,
    start_time: str,
    waypoints: tuple,
):
    """Fetch all conditions data for a peak.

    Returns unified JSON with weather, air quality, daylight, avalanche,
    geodata (counties, hospital, ranger station, campgrounds), and PeakBagger data.
    """
    try:
        lat, lon = map(float, coordinates.split(","))
    except ValueError:
        click.echo(json.dumps({"error": "Invalid coordinates format. Use lat,lon"}), err=True)
        sys.exit(1)

    trailhead_coords: tuple[float, float] | None = None
    if trailhead:
        try:
            th_lat, th_lon = map(float, trailhead.split(","))
            trailhead_coords = (th_lat, th_lon)
        except ValueError:
            click.echo(json.dumps({"error": "Invalid --trailhead format. Use lat,lon"}), err=True)
            sys.exit(1)

    date_str = date or datetime.now().strftime("%Y-%m-%d")
    gaps = []

    summit_elevation_ft = round(elevation * 3.28084)

    # Existing fetchers
    weather = fetch_weather(lat, lon, elevation)
    if "error" in weather:
        gaps.append({"source": "Open-Meteo Weather", "reason": weather["error"]})
    else:
        _enrich_forecast_snow_line(weather.get("forecast", []), summit_elevation_ft)

    air_quality = fetch_air_quality(lat, lon)
    if "error" in air_quality:
        gaps.append({"source": "Open-Meteo Air Quality", "reason": air_quality["error"]})

    tz_name = weather.get("timezone")
    daylight = fetch_daylight(lat, lon, date_str, tz_name)
    if "error" in daylight:
        gaps.append({"source": "Daylight calculation", "reason": daylight["error"]})

    avalanche = fetch_avalanche(lat, lon)

    # Phase 1 geodata fetchers
    counties = fetch_counties((lat, lon), trailhead_coords)
    if "error" in counties:
        gaps.append({"source": "FCC Counties", "reason": counties["error"]})

    nearest_hospital = fetch_nearest_hospital(lat, lon)
    if "error" in nearest_hospital:
        gaps.append({"source": "OSM Nearest Hospital", "reason": nearest_hospital["error"]})

    ranger_station = fetch_ranger_station(lat, lon)
    if "error" in ranger_station:
        gaps.append({"source": "OSM/USFS Ranger Station", "reason": ranger_station["error"]})

    campgrounds = fetch_campgrounds(lat, lon)
    if "error" in campgrounds:
        gaps.append({"source": "OSM Campgrounds", "reason": campgrounds["error"]})

    # PeakBagger data (if peak_id provided)
    peakbagger = {}
    if peak_id:
        stats = run_peakbagger_stats(peak_id)
        if "error" in stats:
            gaps.append({"source": "PeakBagger stats", "reason": stats["error"]})
        else:
            peakbagger["stats"] = stats

        ascents = run_peakbagger_ascents(peak_id)
        if "error" in ascents:
            gaps.append({"source": "PeakBagger ascents", "reason": ascents["error"]})
        else:
            peakbagger["ascents"] = ascents

    output: dict[str, Any] = {
        "weather": weather,
        "air_quality": air_quality,
        "daylight": daylight,
        "avalanche": avalanche,
        "counties": counties,
        "nearest_hospital": nearest_hospital,
        "ranger_station": ranger_station,
        "campgrounds": campgrounds,
        "peakbagger": peakbagger,
        "gaps": gaps,
    }

    if distance_mi is not None and gain_ft is not None:
        output["time_estimates"] = estimate_times(distance_mi, gain_ft)

    # Itinerary: needs start_time + distance + gain + daylight
    if start_time and distance_mi is not None and gain_ft is not None:
        output["itinerary"] = build_itinerary(start_time, distance_mi, gain_ft, daylight)

    # Navigation bearings: needs 2+ waypoints
    if waypoints and len(waypoints) >= 2:
        try:
            parsed = [
                (float(parts[0]), float(parts[1]))
                for w in waypoints
                if (parts := w.split(",")) and len(parts) >= 2
            ]
            if len(parsed) < 2:
                gaps.append(
                    {
                        "source": "Navigation bearings",
                        "reason": "Need at least 2 valid waypoints in lat,lon format.",
                    }
                )
            else:
                output["bearings"] = compute_bearings(parsed)
        except Exception as e:
            gaps.append({"source": "Navigation bearings", "reason": str(e)})

    click.echo(json.dumps(output, indent=2))


if __name__ == "__main__":
    cli()
