# Route Researcher Architecture

## Overview

The route-researcher skill uses a hybrid architecture combining:

- **Python scripts** for deterministic API calls (weather, air quality, daylight, geodata, itinerary, bearings)
- **LLM agents** for tasks requiring judgment (web scraping, content extraction, report writing, validation)

This approach minimizes token usage while maximizing parallelism and reliability.

## Components

### Python Scripts (`tools/`)

| Script | Purpose | Output |
| :----- | :------ | :----- |
| `fetch_conditions.py` | Unified conditions fetcher | JSON with weather, air quality, daylight, avalanche, peakbagger, geodata, time estimates, itinerary, bearings |
| `cloudscrape.py` | Fallback web fetcher for blocked sites | HTML content |

### Agent Types (3 total)

| Agent | Role | Model | Count | When |
| :---- | :--- | :---- | :---- | :--- |
| **Researcher** | Gather data from web sources, fetch trip reports | Sonnet | 3 parallel | Phase 3 |
| **Report Writer** | Generate markdown report from data package | Sonnet | 1 | Phase 5 |
| **Report Reviewer** | Validate report quality, fix issues | Opus | 1 | Phase 6 |

### Orchestrator (SKILL.md)

The orchestrator handles:

- Peak identification (Phases 1-2)
- Coordinating parallel data gathering (Phase 3)
- Data synthesis and analysis (Phase 4)
- Agent dispatch and result aggregation (Phases 3, 5, 6)
- User presentation (Phase 7)

## Execution Flow

```text
User Request
    │
    ▼
Phase 1-2: Peak Identification
    │ (peakbagger-cli search/info)
    ▼
Phase 3: Data Gathering (PARALLEL)
    ┌─────────────────────────────────────────────────────────────────────────┐
    │  Python: fetch_conditions.py                                            │
    │  (weather, air quality, daylight, avalanche, peakbagger stats,          │
    │   counties, hospital, ranger station, campgrounds,                      │
    │   time_estimates, itinerary, bearings)                                  │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  Agent 1: PeakBagger + SummitPost                                       │
    │  Agent 2: WTA + Mountaineers + NWHikers + HikeOfTheWeek +               │
    │           OregonHikers + CascadeClimbers + MountainProject              │
    │  Agent 3: AllTrails                                                     │
    │  (each fetches route info + trip reports incl. hazard/terrain fields)  │
    └─────────────────────────────────────────────────────────────────────────┘
    │
    ▼
Phase 4: Analysis (orchestrator inline)
    │ (route type, crux, hazards, terrain detail, time estimates,
    │  geodata surfacing, gap identification)
    ▼
Phase 5: Report Writer Agent
    │ (generates markdown from data package)
    ▼
Phase 6: Report Reviewer Agent
    │ (validates and fixes issues)
    ▼
Phase 7: Present to User + offer itinerary/bearings/trip-report template
```

## Data Contracts

All agents return JSON matching explicit schemas defined in SKILL.md.

### fetch_conditions.py Output Keys

All keys are top-level in the returned JSON object. Optional keys are emitted only when the corresponding CLI args are provided.

| Key | Present when | Shape summary |
| :-- | :----------- | :------------ |
| `weather` | always | `forecast[]` with per-day `snow_line_note`, `near_summit` bool, `freezing_level_ft` |
| `air_quality` | always | US AQI values |
| `daylight` | always | 8 twilight keys (null = white night) + `daylight_hours`, `timezone` |
| `avalanche` | always | NWAC region + URL |
| `peakbagger` | when `--peak-id` provided | ascent stats + recent ascents |
| `counties` | always | `counties[]` with `county_name`, `county_fips`, `state_name`, `state_code` |
| `nearest_hospital` | always | `hospitals[]` — name, distance_miles, emergency, phone; sorted emergency-first |
| `ranger_station` | always | `stations[]` + optional `admin_district` (district_name, forest_name, region) on NF land |
| `campgrounds` | always | `campgrounds[]` within ~12 mi (20 km) — name, distance_miles, camp_type, backcountry, operator |
| `time_estimates` | `--distance-mi` + `--gain-ft` | roped_hr, unroped_hr, fast_hr, moderate_hr, leisurely_hr, note |
| `itinerary` | `--start-time` + `--distance-mi` + `--gain-ft` | start_time, summit_eta, turnaround_by, return_eta, total_hr, after_dark bool, dusk_cutoff, note |
| `bearings` | 2+ `--waypoint` args | segments[] (bearing_deg, distance_mi, cumulative_distance_mi) + total_distance_mi, note |
| `gaps` | always | string array of API/fetch failures |

**Daylight key names (8 total):**

```
astronomical_dawn  nautical_dawn  civil_twilight (dawn)  sunrise
sunset             civil_dusk     nautical_dusk           astronomical_dusk
```

Values are `null` when the sun does not reach the threshold (high-latitude white nights).

**Itinerary safety signal:** `after_dark: true` means the projected return exceeds the nautical dusk cutoff. The report writer must surface this prominently.

**Bearings bearing_deg convention:** spherical azimuth, 0–360 (0 = N, 90 = E, 180 = S, 270 = W). Apply local declination before compass use.

### Researcher Agent Output

Trip report fields include hazard and terrain-detail extractions:

```json
{
  "sources": ["PeakBagger", "SummitPost"],
  "route_info": [
    {"source": "...", "name": "...", "difficulty": "...", "description": "...", "hazards": [...]}
  ],
  "trip_reports": [
    {
      "source": "...", "date": "...", "author": "...", "url": "...",
      "summary": "...", "conditions": "...", "has_gpx": false,
      "rockfall": "...", "icefall": "...", "cornices": "...",
      "downclimbs": "...", "crossings": "...", "water_sources": "...", "camps": "..."
    }
  ],
  "gaps": ["what couldn't be fetched and why"]
}
```

### Report Writer Output

```json
{
  "status": "SUCCESS",
  "file_path": "/path/to/report.md",
  "filename": "YYYY-MM-DD-peak-name.md",
  "sections_generated": N
}
```

### Report Reviewer Output

```json
{
  "status": "PASS | PASS_WITH_FIXES | FAIL",
  "issues_found": N,
  "fixes_applied": ["description of fixes"],
  "remaining_issues": [],
  "report_path": "/path/to/report.md"
}
```

## Fetching Strategy (Three-Tier Ladder)

For any web page, escalate through tiers until content is returned:

1. **WebFetch** — fastest; works for most static sites
2. **`cloudscrape.py "{url}"`** — httpx with TLS spoofing; no browser; works for many lightly-protected sites
3. **`cloudscrape.py --render "{url}"`** — Patchright stealth headless Chromium; required for Cloudflare-challenged and JS-rendered pages

`cloudscrape.py` always exits 0 (graceful degradation). First `--render` use installs Chromium lazily via `patchright install chromium`; subsequent calls reuse the install.

**Known `--render` requirements:** hikeoftheweek.com.

## Error Handling

| Layer | Failure | Response |
| :---- | :------ | :------- |
| Python API call | Timeout/down | Return partial data + gaps array |
| Researcher agent | Entire agent fails | Proceed with other agents' data |
| Researcher agent | Single source fails | Return partial data + gaps |
| Report Writer | Can't generate | Fail loudly (critical) |
| Report Reviewer | Unfixable issues | Return FAIL status, ask user |

**Minimum viable report:** Peak metadata + at least one route source + conditions data.

## Source Coverage

### Agent 1: PeakBagger + SummitPost

peakbagger-cli (v1.10.0+) for structured peak/ascent data. SummitPost via WebFetch / cloudscrape.py ladder.

### Agent 2: WTA + Mountaineers + Regional Sources

- **WTA** — AJAX trip report endpoint (`{wta_url}/@@related_tripreport_listing`)
- **Mountaineers.org** — route beta, technical requirements
- **NWHikers** (northwesthikers.net / nwhikers.net) — first-person trip reports
- **HikeOfTheWeek** (hikeoftheweek.com) — MUST use `--render` (Cloudflare-protected)
- **Oregon Hikers Field Guide** (oregonhikers.org) — static MediaWiki, WebFetch-friendly
- **Cascade Climbers** (cascadeclimbers.com) — technical beta, forum reports
- **Mountain Project** — rock/ridge sections, grades, gear

### Agent 3: AllTrails

WebFetch / cloudscrape.py ladder. Route stats, reviews, seasonal info.

## Geodata Fetchers

All geodata is fetched deterministically in `fetch_conditions.py` and fails soft (error → `gaps[]`):

| Fetcher | Source | Notes |
| :------ | :----- | :---- |
| `fetch_counties` | FCC Area API | Samples up to 25 points trailhead→summit; dedupes by FIPS |
| `fetch_nearest_hospital` | OSM Overpass | Up to 3 results; `emergency=yes` preferred; haversine sort |
| `fetch_ranger_station` | OSM Overpass + USFS ArcGIS EDW | `admin_district` added when trailhead is on NF land |
| `fetch_campgrounds` | OSM Overpass | ~12 mi (20 km) radius; backcountry camps NOT included |

## Design Decisions

### Why Python for API calls?

- Deterministic: No LLM judgment needed for structured API responses
- Reliable: No prompt variability
- Fast: Direct HTTP calls, no agent overhead
- Cheap: Zero tokens for weather/daylight/air quality/geodata/itinerary/bearings

### Why inline agent prompts?

- Reliable: No "read instructions from file" failure mode
- Self-contained: Agent has everything it needs in the prompt
- Explicit contracts: JSON output format clearly specified
- Testable: Can verify prompt produces expected results

### Why 3 researcher agents (not 5)?

- Balance: Enough parallelism without coordination overhead
- Source grouping: Related sources assigned together
- Trip report batching: Each agent fetches its own reports (no separate fetch step)

### Why Patchright over Playwright?

Patchright is a drop-in Playwright fork with stealth patches (TLS fingerprint, bot-detection bypass). Required for Cloudflare-challenged sites. Lazy Chromium install keeps the base environment light; only installed on first `--render` use.

## Maintenance

To modify agent behavior:

1. Edit the inline prompt in SKILL.md (Phases 3, 5, or 6)
2. Update the JSON output contract if needed
3. Test with a real peak to verify changes work

To add new data sources:

1. Decide if it's API-based (add to fetch_conditions.py) or web-based (add to a Researcher agent)
2. Update the relevant component
3. Update data aggregation in Phase 3C
4. Update Report Writer prompt if new sections needed

To add new fetch_conditions.py output keys:

1. Implement in `fetch_conditions.py` + tests
2. Document the key in SKILL.md Step 3A bullet list
3. Add to Phase 5A data package JSON shape
4. Add template section in `assets/report-template.md`
5. Update this architecture doc
