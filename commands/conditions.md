---
name: conditions
description: Quick weather and conditions check for a mountain peak (weather, air quality, daylight, avalanche)
---

# Quick Conditions Check

Fetch current weather, air quality, daylight, and avalanche conditions for a mountain peak. Much faster than a full route research -- no web scraping or agent dispatch needed.

If the user provided a peak name as an argument (e.g., `/mountaineering:conditions Mt Baker`), use that as the target peak. Otherwise, ask which peak to check.

## Phase 1: Peak Identification

1. **Search PeakBagger** for the peak:

   ```bash
   uvx --from "peakbagger-cli>=1.10.0" peakbagger peak search "{peak_name}" --format json
   ```

2. **Handle results:**

   - **Multiple matches:** Use AskUserQuestion to present options. For each: "[Name] ([Elevation], [Location]) - [PeakBagger URL]". Include "Other" option.
   - **Single match:** Confirm with user: "Found: [Name] ([Elevation], [Location]) - [URL]. Is this correct?"
   - **No matches:** Try variations (Mt/Mount, word order reversal, remove titles). If still nothing, ask user for clarification.

3. **Extract peak_id** from the selected result.

## Phase 2: Peak Details

Fetch peak coordinates and elevation:

```bash
uvx --from "peakbagger-cli>=1.10.0" peakbagger peak show {peak_id} --format json
```

Extract: `latitude`, `longitude`, `elevation_m` (elevation in meters), `peak_name`.

## Phase 3: Fetch Conditions

Run the conditions fetcher script:

```bash
cd ${CLAUDE_PLUGIN_ROOT}/skills/route-researcher/tools && uv run python fetch_conditions.py \
  --coordinates "{latitude},{longitude}" \
  --elevation {elevation_m} \
  --peak-name "{peak_name}" \
  --peak-id {peak_id}
```

This returns JSON with `weather`, `air_quality`, `daylight`, `avalanche`, `peakbagger`, `counties`, `nearest_hospital`, `ranger_station`, `campgrounds`, and (when `--distance-mi`/`--gain-ft` provided) `time_estimates` sections.

**If the script fails:** Note the failure and provide manual check links:

- Weather: `https://www.mountain-forecast.com`
- Avalanche: `https://nwac.us` (Pacific NW) or regional center
- Air quality: `https://www.airnow.gov`

## Phase 4: Present Results

Format the conditions data for the user. Include:

1. **Peak summary:** Name, elevation, coordinates
2. **Weather forecast:** 7-day table with date, conditions, high/low temps, precipitation, wind, freezing level; include **Snow Line** column from `weather.forecast[].snow_line_note` + ⚠️ when `near_summit=true`
3. **Freezing level / snow-line alert:** If any day has `near_summit=true` (freezing level within 2000 ft of summit), call it out prominently
4. **Air quality:** AQI rating. Only highlight if AQI > 50 (anything above "Good")
5. **Daylight:** Full twilight table — astronomical dawn, nautical dawn, civil twilight, sunrise, sunset, civil dusk, nautical dusk, astronomical dusk; show "— (white night)" for null values; include day length
6. **Avalanche:** Region, danger rating if available, link to full forecast
7. **PeakBagger stats:** Recent ascent count and patterns (if available)
8. **Counties traversed:** From `counties.counties[]` — list `county_name`, `state_name`; note if unavailable
9. **Emergency contacts:** Nearest hospital from `nearest_hospital.hospitals[]` (name, distance, phone); nearest ranger station from `ranger_station.stations[]` + `admin_district` if on NF land; note OSM data may be incomplete in remote areas
10. **Campgrounds near trailhead:** From `campgrounds.campgrounds[]` — name, distance, type; note backcountry/high camps not included
11. **Time estimates** (if present): roped (`time_estimates.roped_hr`), unroped (`time_estimates.unroped_hr`), fast/moderate/leisurely — only shown when tool was called with `--distance-mi`/`--gain-ft`

Keep the output concise and scannable. Use tables for the weather forecast and twilight.
