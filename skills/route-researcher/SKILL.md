---
name: route-researcher
description: Research North American mountain peaks and generate comprehensive route beta reports
---

# Route Researcher

Research mountain peaks across North America and generate comprehensive route beta reports combining data from multiple sources including PeakBagger, SummitPost, WTA, AllTrails, weather forecasts, avalanche conditions, and trip reports.

**Data Sources:** This skill aggregates information from specialized mountaineering websites (PeakBagger, SummitPost, Washington Trails Association, AllTrails, The Mountaineers, and regional avalanche centers). The quality of the generated report depends on the availability of information on these sources. If your target peak lacks coverage on these websites, the report may contain limited details. The skill works best for well-documented peaks in North America.

## When to Use This Skill

Use this skill when the user requests:

- Research on a specific mountain peak
- Route beta or climbing information
- Trip planning information for peaks
- Current conditions for mountaineering objectives

Examples:

- "Research Mt Baker"
- "I'm planning to climb Sahale Peak next month, can you research the route?"
- "Generate route beta for Forbidden Peak"

## Progress Checklist

Research Progress:

- [ ] Phase 1: Peak Identification (peak validated, ID obtained)
- [ ] Phase 2: Peak Information Retrieval (coordinates and details obtained)
- [ ] Phase 3: Data Gathering (parallel execution)
  - [ ] Phase 3a: Python conditions fetch (weather, air quality, daylight, avalanche, peakbagger stats/ascents)
  - [ ] Phase 3b: Researcher agents (3 in parallel - web sources + trip reports)
  - [ ] Phase 3c: Results aggregated
  - [ ] Phase 3d: Access/permits (inline WebSearch)
- [ ] Phase 4: Route Analysis (synthesize route, crux, hazards)
- [ ] Phase 5: Report Generation (Report Writer agent)
- [ ] Phase 6: Report Review & Validation (Report Reviewer agent)
- [ ] Phase 7: Completion (user notified, next steps provided)

## Orchestration Workflow

### Phase 1: Peak Identification

**Goal:** Identify and validate the specific peak to research.

1. **Extract Peak Name** from user message
   - Look for peak names, mountain names, or climbing objectives
   - Common patterns: "Mt Baker", "Mount Rainier", "Sahale Peak", etc.

2. **Search PeakBagger** using peakbagger-cli:

   ```bash
   uvx --from "git+https://github.com/dreamiurg/peakbagger-cli.git@v1.10.0" peakbagger peak search "{peak_name}" --format json
   ```

   - Parse JSON output to extract peak matches
   - Each result includes: peak_id, name, elevation (feet/meters), location, url

3. **Handle Multiple Matches:**
   - If **multiple peaks** found: Use AskUserQuestion to present options
     - For each option, show: peak name, elevation, location, AND PeakBagger URL
     - Format each option description as: "[Peak Name] ([Elevation], [Location]) - [PeakBagger URL]"
     - This allows user to click through and verify the correct peak
     - Let user select the correct peak
     - Provide "Other" option if none match

   - If **single match** found: Confirm with user
     - Present confirmation message with peak details and PeakBagger link
     - Show: "Found: [Peak Name] ([Elevation], [Location])"
     - Include PeakBagger URL in the message so user can verify: "[PeakBagger URL]"
     - Use AskUserQuestion: "Is this the correct peak? You can verify at [PeakBagger URL]"

   - If **no matches** found:
     - Try peak name variations systematically (see "Peak Name Variations" section):
       - **Word order reversal:** "Mountain Pratt" → "Pratt Mountain"
       - **Title variations:** Mt/Mount, St/Saint
       - **Add location:** Include state or range name
       - **Remove titles:** Try just the core name
     - Run multiple searches in parallel with different variations
     - Combine results and present best matches to user
     - If still no results, use AskUserQuestion to ask for:
       - A different peak name variation
       - Direct PeakBagger peak ID or URL
       - General PeakBagger search

4. **Extract Peak ID:**
   - From search results JSON, extract the `peak_id` field
   - Store for use in subsequent peakbagger-cli commands
   - Also store the PeakBagger URL for reference links

### Phase 2: Peak Information Retrieval

**Goal:** Get detailed peak information and coordinates needed for location-based data gathering.

This phase must complete before Phase 3, as coordinates are required for weather, daylight, and avalanche data.

Retrieve detailed peak information using the peak ID from Phase 1:

```bash
uvx --from "git+https://github.com/dreamiurg/peakbagger-cli.git@v1.10.0" peakbagger peak show {peak_id} --format json
```

This returns structured JSON with:

- Peak name and alternate names
- Elevation (feet and meters)
- Prominence (feet and meters)
- Isolation (miles and kilometers)
- Coordinates (latitude, longitude in decimal degrees)
- Location (county, state, country)
- Routes (if available): trailhead, distance, vertical gain
- Peak list memberships and rankings
- Standard route description (if available in routes data)

**Error Handling:**

- If peakbagger-cli fails: Fall back to WebSearch/WebFetch and note in "Information Gaps"
- If specific fields missing in JSON: Mark as "Not available" in gaps section
- Rate limiting: Built into peakbagger-cli (default 2 second delay)

**Once coordinates are obtained from this step, immediately proceed to Phase 3.**

### Phase 3: Data Gathering

**Goal:** Gather comprehensive route information from all available sources.

**Execution Strategy:** Run Python script for deterministic API data + dispatch specialized agents in parallel for web research. This hybrid approach minimizes token usage while maximizing parallelism.

#### Step 3A: Fetch Conditions Data (Python Script)

Run the conditions fetcher script to gather all API-based data:

```bash
cd "{repo_root}/skills/route-researcher/tools"
uv run python fetch_conditions.py \
  --coordinates "{latitude},{longitude}" \
  --elevation {elevation_m} \
  --peak-name "{peak_name}" \
  --peak-id {peak_id} \
  --trailhead "{trailhead_lat},{trailhead_lon}" \
  --distance-mi {round_trip_distance_mi} \
  --gain-ft {total_gain_ft} \
  --start-time "{HH:MM}" \
  --waypoint "{lat1},{lon1}" --waypoint "{lat2},{lon2}"
```

Optional args: `--trailhead` enables multi-county path sampling (trailhead→summit); hospital/ranger lookups always run from the summit regardless; `--distance-mi`/`--gain-ft` enable `time_estimates`; `--start-time` (with distance + gain) enables `itinerary`; `--waypoint` (2+) enables `bearings`.

This returns JSON with:

- **weather**: 7-day forecast with temperatures, precipitation, freezing levels; each day includes `snow_line_note` (human-readable framing of freezing level as snow line) and `near_summit` (bool: true when freezing level within 2000 ft of summit)
- **air_quality**: AQI ratings and any concerns
- **daylight**: Full twilight table — `astronomical_dawn`, `nautical_dawn`, `civil_twilight` (dawn), `sunrise`, `sunset`, `civil_dusk`, `nautical_dusk`, `astronomical_dusk`; values are `null` at high latitudes when sun doesn't reach threshold (white nights); `daylight_hours`, `timezone`
- **time_estimates**: Roped/unroped + 3-tier pacing (`roped_hr`, `unroped_hr`, `fast_hr`, `moderate_hr`, `leisurely_hr`) — only present when `--distance-mi` and `--gain-ft` CLI args are provided
- **itinerary**: Trip schedule with safety signals (`start_time`, `summit_eta`, `turnaround_by`, `return_eta`, `total_hr`, `after_dark` bool, `dusk_cutoff`, `note`) — only present when `--start-time`, `--distance-mi`, AND `--gain-ft` are all provided; `after_dark: true` is a safety warning that must be prominently surfaced; `total_hr` is the full round-trip duration in hours
- **bearings**: Navigation bearings between waypoints (`segments[]` with `bearing_deg`, `distance_mi`, `cumulative_distance_mi`; `total_distance_mi`) — only present when 2 or more `--waypoint "lat,lon"` args are provided
- **avalanche**: NWAC region and URL for manual check
- **peakbagger**: Ascent statistics and recent ascents (if peak_id provided)
- **counties**: Counties traversed trailhead→summit (`counties[]` with `county_name`, `county_fips`, `state_name`, `state_code`); `sampled` bool and `sample_points` int indicate whether path sampling ran (requires `--trailhead`); without `--trailhead` only the summit county is returned
- **nearest_hospital**: Nearest hospitals/ERs (`hospitals[]` with `name`, `lat`, `lon`, `distance_miles`, `emergency`, and `phone`/`website`/`address` when OSM has them); sorted emergency-first then by distance; max 3
- **ranger_station**: Nearest ranger stations (`stations[]` with `name`, `lat`, `lon`, `distance_miles`, and `phone`/`website`/`address` when present) + optional `admin_district` (`district_name`, `forest_name`, `region`) when the summit coordinates intersect a USFS ranger district
- **campgrounds**: Established campgrounds within ~12 mi (20 km) (`campgrounds[]` with `name`, `lat`, `lon`, `distance_miles`, `camp_type`, `backcountry`, `operator`, and `website` when present); backcountry/high camps are NOT included — extract those from trip reports
- **gaps**: Any API failures noted for report

**Run this in parallel with Step 3B** — include both the Bash command for fetch_conditions.py and all 3 Task calls in the same response turn to maximize parallelism.

#### Step 3B: Dispatch Researcher Agents (Parallel)

Dispatch 3 Researcher agents in a single message (all Task calls together). Each agent researches assigned sources and fetches trip report content directly.

**Agent 1: PeakBagger + SummitPost**

```
Task(
  subagent_type="general-purpose",
  model="sonnet",
  prompt="""You are a route researcher gathering mountaineering data for {peak_name}.

## Your Assignment
Research from these sources: PeakBagger, SummitPost

## PeakBagger Research
1. Search: "{peak_name} site:peakbagger.com"
2. Extract route descriptions from peak page
3. List recent ascents with trip reports:
   ```bash
   uvx --from "git+https://github.com/dreamiurg/peakbagger-cli.git@v1.10.0" peakbagger peak ascents {peak_id} --format json --with-tr --limit 20
   ```

4. Identify trip reports with content (word_count > 0)
5. Fetch content for up to 5 recent trip reports using:

   ```bash
   uvx --from "git+https://github.com/dreamiurg/peakbagger-cli.git@v1.10.0" peakbagger ascent show {ascent_id} --format json
   ```

## SummitPost Research

1. Search: "{peak_name} site:summitpost.org"
2. Use WebFetch to extract: route name, difficulty, approach, description, hazards
3. If WebFetch fails, use the fetching ladder:

   ```bash
   # Fast path (httpx with browser-like headers, no browser)
   uv run python {repo_root}/skills/route-researcher/tools/cloudscrape.py "{url}"

   # If the above returns {"error": ...} or content is blocked/JS-rendered:
   uv run python {repo_root}/skills/route-researcher/tools/cloudscrape.py --render "{url}"
   ```

## Trip Report Extraction

For each report fetched, extract:
- date, author, route conditions, gear mentioned
- **Hazards (extract explicitly and separately):**
  - Rockfall zones: location on route, conditions, timing guidance mentioned
  - Icefall/serac hazard: location, stability, pre-dawn/timing advice
  - Cornice hazard: location, buildup direction, avoidance notes
- **Terrain detail (extract if mentioned):**
  - Downclimb sections: location, difficulty, rappel anchors if any
  - River/stream crossings: location, flow conditions, ford difficulty
  - Water sources: named locations, seasonal availability
  - Named camps or bivy sites: name/location, exposure notes

## Output Format (return EXACTLY this JSON)

```json
{
  "sources": ["PeakBagger", "SummitPost"],
  "route_info": [
    {"source": "...", "name": "...", "difficulty": "...", "description": "...", "hazards": [...]}
  ],
  "trip_reports": [
    {"source": "...", "date": "...", "author": "...", "url": "...", "summary": "...", "conditions": "...", "has_gpx": false,
     "rockfall": "...", "icefall": "...", "cornices": "...",
     "downclimbs": "...", "crossings": "...", "water_sources": "...", "camps": "..."}
  ],
  "gaps": ["what couldn't be fetched and why"]
}
```"""
)
```

**Agent 2: WTA + Mountaineers + Regional Sources**

```
Task(
  subagent_type="general-purpose",
  model="sonnet",
  prompt="""You are a route researcher gathering mountaineering data for {peak_name}.

## Your Assignment
Research from these sources: WTA, Mountaineers.org, northwesthikers.net, hikeoftheweek.com, Oregon Hikers Field Guide (oregonhikers.org), Cascade Climbers (cascadeclimbers.com), Mountain Project

## WTA Research
1. Search: "{peak_name} site:wta.org"
2. Find the hike page and extract: trail name, difficulty, distance, elevation gain, hazards
3. Get trip reports from AJAX endpoint: {wta_url}/@@related_tripreport_listing
4. Fetch content for up to 5 recent trip reports using the fetching ladder:
   ```bash
   # Fast path first
   uv run python {repo_root}/skills/route-researcher/tools/cloudscrape.py "{trip_report_url}"

   # If output contains {"error": ...} or content is blocked/JS-rendered:
   uv run python {repo_root}/skills/route-researcher/tools/cloudscrape.py --render "{trip_report_url}"
   ```

## Mountaineers Research

1. Search: "{peak_name} site:mountaineers.org route"
2. Extract route beta, technical requirements, hazards

## NWHikers Research (northwesthikers.net / nwhikers.net)

1. Search: "{peak_name} site:nwhikers.net OR site:northwesthikers.net"
2. Use WebFetch to extract first-person trip reports, GPS track notes, conditions
3. If WebFetch fails, use `cloudscrape.py "{url}"` (fast path usually sufficient)

## Hike of the Week (hikeoftheweek.com — REQUIRES --render)

1. Search: "{peak_name} site:hikeoftheweek.com"
2. **MUST use `--render` flag** — site is Cloudflare-protected and blocks WebFetch:

   ```bash
   uv run python {repo_root}/skills/route-researcher/tools/cloudscrape.py --render "{url}"
   ```

3. Extract: logistics, route narrative, access notes, trailhead directions

## Oregon Hikers Field Guide (oregonhikers.org — Oregon objectives only)

1. Search: "{peak_name} site:oregonhikers.org"
2. Use WebFetch — site is static MediaWiki HTML, WebFetch-friendly
3. Extract: route description, access, permits, conditions notes

## Cascade Climbers (cascadeclimbers.com)

1. Search: "{peak_name} site:cascadeclimbers.com"
2. Use WebFetch; if blocked use `cloudscrape.py "{url}"`
3. Extract: technical route beta, gear lists, trip reports, conditions

## Mountain Project (for technical/rock sections)

1. Search: "{peak_name} site:mountainproject.com"
2. Use WebFetch to extract: route name, grade, gear, description, rock quality
3. If WebFetch fails, use `cloudscrape.py "{url}"`

## Fallback

If WebFetch fails for any page, use the fetching ladder: `cloudscrape.py "{url}"` (fast) → `cloudscrape.py --render "{url}"` for JS-rendered or Cloudflare-protected pages.

## Trip Report Extraction

For each report fetched, extract:
- date, author, route conditions, gear mentioned
- **Hazards (extract explicitly and separately):**
  - Rockfall zones: location on route, conditions, timing guidance mentioned
  - Icefall/serac hazard: location, stability, pre-dawn/timing advice
  - Cornice hazard: location, buildup direction, avoidance notes
- **Terrain detail (extract if mentioned):**
  - Downclimb sections: location, difficulty, rappel anchors if any
  - River/stream crossings: location, flow conditions, ford difficulty
  - Water sources: named locations, seasonal availability
  - Named camps or bivy sites: name/location, exposure notes

## Output Format (return EXACTLY this JSON)

```json
{
  "sources": ["WTA", "Mountaineers", "NWHikers", "HikeOfTheWeek", "OregonHikers", "CascadeClimbers", "MountainProject"],
  "route_info": [
    {"source": "...", "name": "...", "difficulty": "...", "description": "...", "hazards": [...]}
  ],
  "trip_reports": [
    {"source": "...", "date": "...", "author": "...", "url": "...", "summary": "...", "conditions": "...", "has_gpx": false,
     "rockfall": "...", "icefall": "...", "cornices": "...",
     "downclimbs": "...", "crossings": "...", "water_sources": "...", "camps": "..."}
  ],
  "gaps": ["what couldn't be fetched and why"]
}
```"""
)
```

**Agent 3: AllTrails**

```
Task(
  subagent_type="general-purpose",
  model="sonnet",
  prompt="""You are a route researcher gathering mountaineering data for {peak_name}.

## Your Assignment
Research from AllTrails

## AllTrails Research
1. Search: "{peak_name} site:alltrails.com"
2. Use WebFetch to extract: trail name, difficulty, distance, elevation gain, route type, best season, hazards
3. If WebFetch fails, use:
   ```bash
   uv run python {repo_root}/skills/route-researcher/tools/cloudscrape.py "{url}"
   ```

4. From route description and any visible reviews/comments, extract if present:
   - Rockfall zones, icefall/serac hazard, cornice hazard
   - Downclimb sections, river/stream crossings, water sources, named camps

## Output Format (return EXACTLY this JSON)

```json
{
  "sources": ["AllTrails"],
  "route_info": [
    {"source": "...", "name": "...", "difficulty": "...", "distance_miles": N, "elevation_gain_ft": N, "description": "...", "hazards": [...],
     "rockfall": "...", "icefall": "...", "cornices": "...",
     "downclimbs": "...", "crossings": "...", "water_sources": "...", "camps": "..."}
  ],
  "trip_reports": [],
  "gaps": ["what couldn't be fetched and why"]
}
```"""
)
```

**Execute all 3 agents in parallel by including all Task calls in a single response.**

#### Step 3C: Aggregate Results

After Python script and all agents return, aggregate into unified data structure:

```json
{
  "conditions": { /* from fetch_conditions.py */ },
  "route_data": {
    "sources": [ /* merged from all 3 agents */ ],
    "trip_reports": [ /* merged from all agents */ ]
  },
  "gaps": [ /* merged gaps from all sources */ ]
}
```

**Partial Failure Handling:**

- If any agent fails entirely, proceed with data from successful agents
- Note failed sources in the gaps array
- Minimum viable: conditions data + at least one route source

#### Step 3D: Access, Permits, and Road/Gate Status (Inline)

Determine permits AND the **current road/gate status** to the trailhead — do not just tell the user to go check. Actively research and report the actual status with a source and date.

**Permits:**

```
WebSearch: "{peak_name} trailhead access" ; "{peak_name} permit requirements"
```

**Road / gate status workflow** (identify the access highway + forest road + managing agency first, then check sources in order; capture each source URL for the report):

1. **State DOT pass report** (WA → WSDOT): fetch the relevant pass page, e.g. `https://wsdot.com/travel/real-time/mountainpasses/mt.-baker` (SR-542) or `.../north-cascades` (SR-20). Read `RoadCondition` / `TravelAdvisoryActive` / restrictions. Other states: `WebSearch "{state} DOT mountain pass report {highway}"`.
2. **USFS forest alerts/conditions**: fetch `https://www.fs.usda.gov/{region}/{forest-shortname}/alerts` (e.g. `r06/mbs/alerts`) and `/conditions`; search the page for the road number / trailhead name → closure milepost, reason, seasonal gate. Also `WebSearch "{forest name} {road or trailhead} road open {year}"` for seasonal-opening press releases.
3. **NPS road conditions** (if in/through a national park): fetch `https://www.nps.gov/{park-code}/planyourvisit/road-conditions.htm` (e.g. `noca`, `mora`, `olym`) → per-road OPEN/CLOSED + milepost.
4. **WTA ground truth** (PNW): `WebSearch "site:wta.org {trail} gate road open closed {year}"` or fetch the hike page; scan the 3-5 most recent trip reports for "gate"/"road open/closed"/"drove to" (use `cloudscrape.py --render` if WTA 403s).
5. **InciWeb fire closures** (Jul-Oct): `WebSearch "inciweb {area} closure {trailhead} {year}"`; if an active incident is near the trailhead, read its closure page.

**Synthesize** into a dated status statement for the report's Road Conditions section:
> "Gate/road status (as of {date}): {road} is {OPEN/CLOSED/SEASONAL GATE/UNKNOWN} per [source](url). {If closed: gate at {milepost}, adds ~{N} mi each way.}"

If no source confirms it, say so explicitly and include the managing ranger station phone as the fallback. Add trailhead names, permits, the status statement, and all source URLs to route_data.

### Phase 4: Route Analysis

**Goal:** Analyze gathered data to determine route characteristics and synthesize information.

#### Step 4A: Determine Route Type

Based on route descriptions, elevation, and gear mentions, classify as:

- **Glacier:** Crevasses mentioned, glacier travel, typically >8000ft
- **Rock:** Technical climbing, YDS ratings (5.x), protection mentioned
- **Scramble:** Class 2-4, exposed but non-technical
- **Hike:** Class 1-2, trail-based, minimal exposure

#### Step 4B: Synthesize Route Information from Multiple Sources

**Goal:** Combine trip reports and route descriptions from Step 3B researcher agents, plus conditions data from Step 3A, into comprehensive route beta.

**Source Priority:**

1. Trip reports (Step 3B agents) - first-hand experiences
2. Route descriptions (Step 3B agents) - published beta baseline
3. PeakBagger/ascent data (Step 3A Python script) - basic info, patterns

**Synthesis Pattern for Route, Crux, and Hazards:**

1. **Start with baseline** from route descriptions (standard route name, published difficulty)
2. **Enrich with trip report details** (landmarks, specific conditions, actual experiences)
3. **Note conflicts** when trip reports disagree with published info
4. **Highlight consensus** ("Multiple reports mention...")
5. **Include specifics** (elevations, locations, quotes)
6. **Link every specific-report attribution to its source.** Whenever a detail is drawn from a *particular* trip/climb report (a date, a quote, "one party found…", "a recent report noted…"), the attribution MUST be a Markdown hyperlink to that report's URL — never plain text. Carry each trip report's `url` (and date/author) through synthesis so it can be linked; use the date/author as the link text. For consensus phrasing ("multiple reports mention…"), link 2-3 of the contributing reports inline. Only general/published beta with no specific source stays unlinked.

**Example (Route Description):**
> "The standard route follows the East Ridge (Class 3). A [Sep 2025 party](https://www.peakbagger.com/climber/ascent.aspx?aid=12345) found a well-cairned use trail branching right at 4,800 ft—the correct turn—through talus they called 'tedious' and 'ankle-rolling'. An [Oct 2025 report](https://www.wta.org/go-hiking/trip-reports/trip_report.123) noted the section was snow-covered, requiring microspikes."

**Apply this pattern to:**

- **Route:** Use baseline structure, add landmarks/navigation from trip reports, include actual times
- **Crux:** Describe location/difficulty, add trip report assessments, note conditions-dependent variations
- **Hazards:** Extract ALL hazards from trip reports. Organize by type with explicit, SEPARATE sub-sections — do NOT bury rockfall or icefall under generic "exposure":
  - **Rockfall:** tag location, trigger (other parties / freeze-thaw / sun hitting the face), timing mitigation (pre-dawn passage, move quickly through zone)
  - **Icefall/Serac:** tag location, stability assessment, timing mitigation (avoid afternoon, pre-dawn passage)
  - **Cornice:** tag location, avoidance line, conditions (buildup direction, season)
  - Other hazards (crevasses, exposure, route-finding, seasonal) as separate bullets
  - Be comprehensive — safety-critical; include specific locations and mitigation strategies
- **Terrain detail:** Surface the following in the report when found in trip reports/beta:
  - Downclimbs: location, difficulty, whether rappel anchors exist
  - River/stream crossings: location, seasonal flow, ford difficulty
  - Water sources: named locations and per-day availability by season
  - Named camps/bivy sites: name, location, exposure; note these come from trip reports, not the campground database

**Extract Key Information:**

From all synthesized data, identify:

- **Difficulty Rating:** YDS class, scramble grade, or general difficulty (validated by trip reports)
- **Crux:** Hardest/most technical section of route (synthesized above)
- **Hazards:** All identified hazards (synthesized above)
- **Notable Gear:** Any unusual or important gear mentioned in trip reports or beta (to be included in relevant sections, not as standalone section)
- **Trailhead:** Name and approximate location
- **Distance/Gain:** Round-trip distance and elevation gain (compare published vs actual trip report data)
- **Time Estimates:** Use `conditions.time_estimates` (keys: `fast_hr`, `moderate_hr`, `leisurely_hr`, `roped_hr`, `unroped_hr`) from fetch_conditions.py output — present only when it was called with `--distance-mi` and `--gain-ft`. If `time_estimates` is absent from the conditions data, note it in Information Gaps. **To populate it:** re-invoke fetch_conditions.py with `--distance-mi {distance}` and `--gain-ft {gain}` once route distance/gain are known from Step 3B research. At the same time, add `--start-time HH:MM` to get `itinerary` and `--waypoint` args to get `bearings` — these optional outputs only activate when the args are supplied.
- **Freezing Level Analysis:** Compare peak elevation with forecasted freezing levels:
  - **Include Freezing Level Alert if:** Any day in forecast has freezing level within 2000 ft of peak elevation
  - **Omit if:** Freezing level stays >2000 ft above peak throughout forecast (typical summer conditions)
  - Example: 5,469 ft peak with 5,000-8,000 ft freezing levels → Include alert (marginal conditions)
  - Example: 4,000 ft peak with 10,000+ ft freezing levels → Omit alert (well above summit)

#### Step 4C: Surface Geodata in Report

Include these geodata fields when available. **Every place named in the report must be a link** — see the link patterns below.

**Place / map link patterns** (build from a place's `lat`/`lon` and `name`):

- Google Maps **place** (named entity): `https://www.google.com/maps/search/?api=1&query={URL-encoded name + address}` — use this (not bare coordinates) for hospitals, ranger stations, campgrounds, and any named place, so the link resolves to the actual entity. When only coordinates are meaningful, `query={lat},{lon}`.
- Gaia GPS: `https://www.gaiagps.com/map/?loc=14/{lon}/{lat}` (zoom/lon/lat).
- CalTopo: `https://caltopo.com/map.html#ll={lat},{lon}&z=14&b=mbt`.

Surfacing rules:

- **Counties:** list `county_name + state_name` from `conditions.counties.counties[]` in the Overview. Empty/`error` → Information Gaps.
- **Emergency contacts:** build the table from `conditions.nearest_hospital.hospitals[]` and `conditions.ranger_station` (stations + admin_district). **Link each name** to its `website` if present, else a Google Maps place search by `name + address`. **Always include phone AND address columns** — each entry now carries `phone`/`website`/`address`/`lat`/`lon` when OSM has them; if `phone` or `address` is missing, make a best effort to find the entity's real phone/address (its official site or Google Maps listing) before writing "—". Missing/`error` → note in Information Gaps.
- **Campgrounds:** build the Camping table from `conditions.campgrounds.campgrounds[]`; link the name (website or Google Maps place) and add Google Maps + Gaia map links from each entry's `lat`/`lon`.
- **Any named location report-wide** (campsite, bivy, high camp, named feature, trailhead): accompany with at least Google Maps + Gaia links, per the patterns above. For trip-report-named camps without coordinates, use a Google Maps place search by name and do your best to locate it; if it cannot be located, say so explicitly. Backcountry/high camps come from trip reports, not the campground DB.

#### Step 4D: Identify Information Gaps

Explicitly document what data was **not found or unreliable:**

- Missing trip reports
- No GPS tracks available
- Script failures (weather, avalanche, daylight)
- Conflicting information between sources
- Limited seasonal data

### Phase 5: Report Generation

**Goal:** Create comprehensive Markdown document by dispatching Report Writer agent.

#### Step 5A: Prepare Data Package

Organize all gathered and analyzed data into structured JSON:

```json
{
  "peak": {
    "name": "{peak_name}",
    "id": {peak_id},
    "elevation_ft": {elevation},
    "coordinates": [{latitude}, {longitude}],
    "location": "{location}",
    "peakbagger_url": "{url}"
  },
  "conditions": {
    // From fetch_conditions.py output
    "weather": {"forecast": [{"date": "...", "snow_line_note": "...", "near_summit": bool, "freezing_level_ft": N, ...}], ...},
    "air_quality": {...},
    "daylight": {"astronomical_dawn": "...", "nautical_dawn": "...", "civil_twilight": "...", "sunrise": "...", "sunset": "...", "civil_dusk": "...", "nautical_dusk": "...", "astronomical_dusk": "...", "daylight_hours": N},
    "avalanche": {...},
    "peakbagger": {...},
    "counties": {"counties": [{"county_name": "...", "county_fips": "...", "state_name": "...", "state_code": "..."}], "sampled": bool, "sample_points": N},  // sampled + sample_points only present when --trailhead was given
    "nearest_hospital": {"hospitals": [{"name": "...", "lat": N, "lon": N, "distance_miles": N, "emergency": "yes|null", "phone": "...", "website": "...", "address": "..." /* phone/website/address optional */}]},
    "ranger_station": {"stations": [{"name": "...", "lat": N, "lon": N, "distance_miles": N, "phone": "...", "website": "...", "address": "..." /* optional */}], "admin_district": {"district_name": "...", "forest_name": "...", "region": "..."}},
    "campgrounds": {"campgrounds": [{"name": "...", "lat": N, "lon": N, "distance_miles": N, "camp_type": "...", "operator": "...", "website": "..." /* optional */}], "note": "..."},
    "time_estimates": {"roped_hr": N, "unroped_hr": N, "fast_hr": N, "moderate_hr": N, "leisurely_hr": N, "note": "..."},
    "itinerary": {"start_time": "HH:MM", "summit_eta": "HH:MM", "turnaround_by": "HH:MM", "return_eta": "HH:MM", "total_hr": N, "after_dark": false, "dusk_cutoff": "9:15 PM" /* 12-hr AM/PM format, unlike other time fields */, "note": "..."},
    "bearings": {"segments": [{"from": 0, "to": 1, "bearing_deg": N, "distance_mi": N, "cumulative_distance_mi": N}], "total_distance_mi": N}
  },
  "route_data": {
    // Merged from all Researcher agents
    "sources": [...],
    "trip_reports": [...]
  },
  "analysis": {
    // From Phase 4
    "route_type": "{hike|scramble|technical|glacier}",
    "difficulty": "{rating}",
    "crux": "{description}",
    "hazards": [...],
    "access": {...}
  },
  "gaps": [...]
}
```

#### Step 5B: Dispatch Report Writer Agent

```
Task(
  subagent_type="general-purpose",
  model="sonnet",
  prompt="""You are a Report Writer generating a mountaineering route report.

## Instructions

1. **Read the report template:**
   Use the Read tool to read: {repo_root}/skills/route-researcher/assets/report-template.md

2. **Generate report following template structure exactly:**
   - Header with peak name, elevation, location, date
   - AI disclaimer (prominent safety warning)
   - Overview: route type, difficulty, distance/gain, time estimates
   - Route Description: synthesized from sources, include landmarks
   - Crux: describe hardest section with specifics
   - Known Hazards: comprehensive list
   - Current Conditions: weather forecast, freezing levels, air quality, daylight
   - Trip Reports: links organized by source with dates
   - Information Gaps: explicitly list missing data
   - Data Sources: links to all sources used

3. **Markdown Formatting Rules:**
   - ALWAYS add blank line before lists
   - ALWAYS add blank line after section headers
   - Use `-` for bullets (not `*` or `+`)
   - Use `**text**` for bold emphasis
   - Break paragraphs >4 sentences
   - **Link specific-report attributions.** Any statement attributed to a particular trip/climb report (a date, a quote, "one party…", "a recent report…") MUST be a Markdown link `[date/author](report_url)` to that report's source URL — never plain-text attribution. Pull the URL from the matching `trip_reports[].url` in the data package. Leave only generic/published beta (no specific source) unlinked.

4. **Save the report:**
   Use the Write tool to save to the user's current working directory: {date}-{peak-name-slug}.md

## Data Package

{data_package_json}

## Output Format (return EXACTLY this JSON)
```json
{
  "status": "SUCCESS",
  "file_path": "/absolute/path/to/report.md",
  "filename": "YYYY-MM-DD-peak-name.md",
  "sections_generated": N
}
```"""
)
```

#### Step 5C: Capture Report File Path

Extract `file_path` from agent's JSON response for use in Phase 6.

### Phase 6: Report Review & Validation

**Goal:** Validate report quality by dispatching Report Reviewer agent.

#### Step 6A: Dispatch Report Reviewer Agent

```
Task(
  subagent_type="general-purpose",
  model="opus",
  prompt="""You are a Report Reviewer validating a mountaineering route report.

## Instructions

1. **Read the report:**
   Use the Read tool to read: {report_file_path}

2. **Perform systematic quality checks:**

   **Factual Consistency:**
   - Dates match their stated day-of-week (e.g., "Thu Nov 6, 2025" is actually Thursday)
   - Coordinates, elevations, distances consistent across all mentions
   - Weather forecasts align logically (freezing levels match precipitation types)

   **Mathematical Accuracy:**
   - Elevation gains add up correctly
   - Time estimates reasonable given distance and elevation gain
   - Unit conversions correct (feet to meters, etc.)

   **Internal Logic:**
   - Hazard warnings align with route descriptions
   - Recommendations match current conditions
   - Crux descriptions match overall difficulty rating

   **Completeness:**
   - No placeholder texts like {{peak_name}} or {{YYYY-MM-DD}}
   - All referenced links actually provided
   - Mandatory sections present: Overview, Route, Current Conditions, Trip Reports, Information Gaps, Data Sources

   **Formatting:**
   - Markdown headers properly structured
   - Lists have blank lines before them
   - Tables properly formatted

   **Safety & Responsibility:**
   - AI disclaimer present and prominent
   - Critical hazards properly emphasized
   - Users directed to verify information from primary sources

   **Emergency contacts & location links (verify INDEPENDENTLY):**
   - Each emergency contact (hospital, ranger station) has a working name link (website or a Google Maps place link to the actual entity — NOT bare coordinates), a phone, and an address. Independently confirm the phone/address look right for that named entity (e.g. via its official site / Google Maps); fix or flag mismatches and fill blanks you can confirm.
   - Road/gate status is a dated statement with a cited source, not a "go check it yourself" punt.
   - Every named place in the report (campsite, bivy, high camp, trailhead, named feature) carries map links (Google Maps + Gaia GPS). Flag any named location missing links.
   - Specific trip-report attributions are hyperlinks to their source, not plain text.

3. **Fix issues:**
   - **Critical** (safety errors, factual errors, missing disclaimers): MUST fix using Edit tool
   - **Important** (completeness, consistency): SHOULD fix
   - **Minor** (formatting, polish): FIX if quick

## Output Format (return EXACTLY this JSON)
```json
{
  "status": "PASS" | "PASS_WITH_FIXES" | "FAIL",
  "issues_found": N,
  "fixes_applied": ["description of fix 1", "description of fix 2"],
  "remaining_issues": ["issues that couldn't be fixed"],
  "report_path": "/absolute/path/to/report.md"
}
```"""
)
```

#### Step 6B: Process Validation Results

Handle the reviewer agent's response:

- **PASS or PASS_WITH_FIXES:** Proceed to Phase 7 with the `report_path`
- **FAIL:** Present `remaining_issues` to user and ask for guidance

The Report Reviewer automatically fixes issues and returns the corrected file path.

### Phase 7: Completion

**Goal:** Inform user of completion and next steps.

Report to user:

1. **Success message:** "Route research complete for {Peak Name}"
2. **File location:** Full absolute path to generated report
3. **Summary:** Brief 2-3 sentence overview:
   - Route type and difficulty
   - Key hazards or considerations
   - Any significant information gaps
4. **Next steps:** Encourage user to:
   - Review the report
   - Verify critical information from primary sources
   - Check current conditions before attempting route
   - **Itinerary and navigation**: If the user wants a start-time schedule and/or compass bearings, re-run `fetch_conditions.py` with `--start-time HH:MM` (adds `itinerary` key) and/or `--waypoint lat,lon` flags (2+ waypoints add `bearings` key). Surface `after_dark: true` as a prominent safety warning.
   - **Post-climb trip report**: After the climb, offer the trip-report template at `skills/route-researcher/assets/trip-report-template.md` as a starting point for filing a trip report.

**Example completion message:**

```
Route research complete for Mount Baker!

Report saved to: 2025-10-20-mount-baker.md

Summary: Mount Baker via Coleman-Deming route is a moderate glacier climb (Class 3) with significant crevasse hazards. The route involves 5,000+ ft elevation gain and typically requires an alpine start. Weather and avalanche forecasts are included.

Next steps: Review the report and verify current conditions before your climb. Remember that mountain conditions change rapidly - check recent trip reports and weather forecasts immediately before your trip.
```

## Error Handling Principles

Throughout execution, follow these error handling guidelines:

### Script Failures

- **Don't block:** If a Python script fails, note in "Information Gaps" and continue
- **Provide alternatives:** Include manual check links (Mountain-Forecast.com, NWAC.us)
- **One retry:** Retry once on network timeouts, then continue

### Missing Data

- **Be explicit:** Always document what wasn't found
- **Be helpful:** Provide links for manual checking
- **Don't guess:** Never fabricate data to fill gaps

### Search Failures

- **Try variations:** If peak not found, try alternate names (Mt vs Mount)
- **Ask user:** If still not found, ask user for clarification or direct URL
- **Provide guidance:** Suggest how to search PeakBagger manually

### WebFetch/WebSearch Issues

- **Fetching ladder:** WebFetch first → `cloudscrape.py "{url}"` (fast httpx, no browser) → `cloudscrape.py --render "{url}"` (Patchright stealth browser, for JS-rendered or Cloudflare-protected pages)
- **When to use `--render`:** hikeoftheweek.com and any site where the default path returns `{"error": ...}` on stdout or where content is blocked/JS-rendered
- **Graceful degradation:** Missing one source shouldn't stop entire research; cloudscrape.py exits 0 on failure
- **Document gaps:** Note which sources were unavailable (WebFetch AND both cloudscrape.py paths failed)
- **Prioritize safety:** If critical safety info (avalanche, hazards) unavailable, emphasize in gaps section

## Execution Timeouts

- **Individual Python scripts:** 30s for API calls; up to 120s when --peak-id is provided (peakbagger-cli)
- **WebFetch operations:** Use default timeout
- **WebSearch operations:** Use default timeout
- **Total skill execution:** Target 3-5 minutes, acceptable up to 10 minutes for comprehensive research

## Quality Principles

Every generated report must:

1. ✅ **Include safety disclaimer** prominently at top
2. ✅ **Document all information gaps** explicitly
3. ✅ **Cite sources** with links
4. ✅ **Use current date** in filename and metadata
5. ✅ **Follow template structure** exactly
6. ✅ **Provide actionable information** (distances, times, gear)
7. ✅ **Emphasize verification** - this is research, not gospel

## Implementation Notes

See `skills/route-researcher/docs/architecture.md` for detailed execution flow, component overview, data contracts, and design decisions.

### peakbagger-cli Command Reference (v1.10.0, git source)

All commands use `--format json` for structured output. Run via:

```bash
uvx --from "git+https://github.com/dreamiurg/peakbagger-cli.git@v1.10.0" peakbagger <command> --format json
```

**Available Commands:**

- `peak search <query>` - Search for peaks by name
- `peak show <peak_id>` - Get detailed peak information (coordinates, elevation, routes)
- `peak stats <peak_id>` - Get ascent statistics and temporal patterns
  - `--within <period>` - Filter by period (e.g., '1y', '5y')
  - `--after <YYYY-MM-DD>` / `--before <YYYY-MM-DD>` - Date filters
- `peak ascents <peak_id>` - List individual ascents with trip report links
  - `--within <period>` - Filter by period (e.g., '1y', '5y')
  - `--with-gpx` - Only ascents with GPS tracks
  - `--with-tr` - Only ascents with trip reports
  - `--limit <n>` - Max ascents to return (default: 100)
- `ascent show <ascent_id>` - Get detailed ascent information

**Note:** For comprehensive command options, run `peakbagger --help` or `peakbagger <command> --help`

### Peak Name Variations

Common variations to try if initial search fails:

- **Word order reversal:** "Mountain Pratt" → "Pratt Mountain", "Peak Sahale" → "Sahale Peak"
- **Title expansion:** "Mt" → "Mount", "St" → "Saint"
- **Add location:** "Baker, WA" or "Baker, North Cascades"
- **Remove title:** "Baker" instead of "Mt Baker"
- **Combine variations:** Try reversed order with title expansion (e.g., "Mountain Pratt" → "Pratt Mount" + "Pratt Mountain")

### Navigation Map Links

#### Summit Coordinates Links

Build these centered on the summit (decimal degrees) for the report Overview line.

**Google Maps:**

```
https://www.google.com/maps/search/?api=1&query={latitude},{longitude}
```

**CalTopo** (MapBuilder Topo base, zoom 14):

```
https://caltopo.com/map.html#ll={latitude},{longitude}&z=14&b=mbt
```

**Gaia GPS** (order is zoom/longitude/latitude):

```
https://www.gaiagps.com/map/?loc=14/{longitude}/{latitude}
```

**PeakVisor hiking map** (zoom/latitude/longitude; slashes URL-encoded as `%2F` in the query):

```
https://peakvisor.com/hiking-map?custom=14%2F{latitude}%2F{longitude}#14/{latitude}/{longitude}
```

Example (Mt Baker, 48.7768, -121.8144):

- Google Maps: `https://www.google.com/maps/search/?api=1&query=48.7768,-121.8144`
- CalTopo: `https://caltopo.com/map.html#ll=48.7768,-121.8144&z=14&b=mbt`
- Gaia GPS: `https://www.gaiagps.com/map/?loc=14/-121.8144/48.7768`
- PeakVisor: `https://peakvisor.com/hiking-map?custom=14%2F48.7768%2F-121.8144#14/48.7768/-121.8144`

**Note:** Use decimal degrees. Gaia GPS expects zoom/longitude/latitude order; CalTopo and PeakVisor use latitude then longitude.

#### Trailhead Google Maps Links

**If coordinates available** (e.g., from Mountaineers.org place information):

```
https://www.google.com/maps/search/?api=1&query={latitude},{longitude}
```

Example: `https://www.google.com/maps/search/?api=1&query=48.5123,-121.0456`

**If only trailhead name available:**

```
https://www.google.com/maps/search/?api=1&query={trailhead_name}+{state}
```

Example: `https://www.google.com/maps/search/?api=1&query=Cascade+Pass+Trailhead+WA`

**Note:** Prefer coordinates when available for more precise location.

---

**Skill Version:** 5.1.0 | **Last Updated:** 2026-05-22
