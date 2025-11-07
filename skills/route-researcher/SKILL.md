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
- [ ] Phase 3: Data Gathering (route descriptions, trip reports, weather, conditions collected)
  - [ ] Phase 3 Stage 1: Parallel data gathering (Steps 3A-3H)
  - [ ] Phase 3 Stage 2: Fetch trip report content (Step 3I - 10-15 reports for representative sample)
- [ ] Phase 4: Route Analysis (synthesize route, crux, hazards from all sources including trip reports)
- [ ] Phase 5: Report Generation (markdown file created)
- [ ] Phase 6: Report Review & Validation (check for inconsistencies and errors)
- [ ] Phase 7: Completion (user notified, next steps provided)

## Orchestration Workflow

### Phase 1: Peak Identification

**Goal:** Identify and validate the specific peak to research.

1. **Extract Peak Name** from user message
   - Look for peak names, mountain names, or climbing objectives
   - Common patterns: "Mt Baker", "Mount Rainier", "Sahale Peak", etc.

2. **Search PeakBagger** using peakbagger-cli:
   ```bash
   uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger peak search "{peak_name}" --format json
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
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger peak show {peak_id} --format json
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

**Execution Strategy:** Execute ALL steps in parallel to minimize total execution time.

All Phase 3 steps run simultaneously. Do not wait for any step to complete before starting others.

#### Step 3A: Route Description Research (WebSearch + WebFetch)

**Step 1:** Search for route descriptions:
```
WebSearch queries (run in parallel):
1. "{peak_name} route description climbing"
2. "{peak_name} summit post route"
3. "{peak_name} mountain project"
4. "{peak_name} site:mountaineers.org route"
5. "{peak_name} site:alltrails.com"
6. "{peak_name} standard route"
```

**Step 2:** Fetch top relevant pages:

**Universal Fetching Strategy:**

For ANY website, use this two-tier approach:

1. **Try WebFetch first** with appropriate extraction prompt
2. **If WebFetch fails or returns incomplete data,** use cloudscrape.py as fallback:
   ```bash
   cd skills/route-researcher/tools
   uv run python cloudscrape.py "{url}"
   ```
   Then parse the returned HTML to extract needed information.

**Common sites and their extraction prompts:**

**AllTrails (try WebFetch, fallback to cloudscrape.py):**
```
WebFetch Prompt: "Extract route information including:
- Trail name
- Route description and key features
- Difficulty rating
- Distance and elevation gain
- Estimated time
- Route type (loop, out & back, point to point)
- Best season
- Known hazards or warnings
- Current conditions if mentioned in recent reviews"
```

**Save AllTrails URL for Phase 4:**
- Overview sources section (primary route information sources)
- Trip reports "Browse All" section (for reviews)

**SummitPost, Mountaineers.org, PeakBagger (try WebFetch, fallback to cloudscrape.py):**
```
WebFetch Prompt: "Extract route information including:
- Route name and difficulty rating
- Approach details and trailhead
- Route description and key sections
- Technical difficulty (YDS class, scramble grade, etc.)
- Crux description
- Distance and elevation gain
- Estimated time
- Known hazards and conditions"
```

**Mountain Project, WTA (try WebFetch, fallback to cloudscrape.py):**
```
WebFetch Prompt: "Extract route information including:
- Approach details
- Route description and key sections
- Technical difficulty (YDS class, scramble grade, etc.)
- Crux description
- Distance and elevation gain
- Estimated time
- Known hazards"
```

**Error Handling:**
- If WebFetch fails or returns incomplete data: Automatically retry with cloudscrape.py
- If cloudscrape.py also fails: Note in "Information Gaps" section with URL for manual checking
- If no route descriptions found from any source: Note in gaps and provide general guidance
- If conflicting information between sources: Note discrepancies in report

#### Step 3B: Peak Ascent Statistics (peakbagger-cli)

Retrieve ascent data and patterns using the peak ID:

**Step 1: Get overall ascent statistics**
```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger peak stats {peak_id} --format json
```

This returns:
- Total ascent count (all-time)
- Seasonal distribution (by month)
- Count of ascents with GPX tracks
- Count of ascents with trip reports

**Step 2: Get detailed ascent list based on activity level**

Based on the total count from Step 1, adaptively retrieve ascents:

**For popular peaks (>50 ascents total):**
```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger peak ascents {peak_id} --format json --within 1y
```
Recent data (1 year) is sufficient for active peaks.

**For moderate peaks (10-50 ascents total):**
```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger peak ascents {peak_id} --format json --within 5y
```
Expand to 5 years to get meaningful sample size.

**For rarely-climbed peaks (<10 ascents total):**
```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger peak ascents {peak_id} --format json
```
Get all available ascent data regardless of age.

**Additional filters (apply as needed):**
- `--with-gpx`: Focus on ascents with GPS tracks (useful for route finding)
- `--with-tr`: Focus on ascents with trip reports (useful for conditions)

**Extract and save for Phase 4 (Report Generation):**
- Total ascent statistics (total count, temporal breakdown, monthly distribution)
- **All ascents from JSON with the following data:**
  - Date (`date` field)
  - Climber name (`climber.name` field)
  - Trip report word count (`trip_report.word_count` field)
  - GPX availability (`has_gpx` field)
  - Ascent URL (`url` field)
- Seasonal patterns (monthly distribution data)
- Timeframe used for the query (1y, 5y, or all)

**Error Handling:**
- If peakbagger-cli fails: Fall back to WebSearch for trip reports
- If no ascents found: Note in report and continue with other sources

#### Step 3C: Trip Report Sources Discovery (WebSearch)

Systematically search for trip report pages across major platforms:

```
WebSearch queries (run in parallel):
1. "{peak_name} site:wta.org" - WTA hike page with trip reports
2. "{peak_name} site:alltrails.com" - AllTrails page with reviews
3. "{peak_name} site:summitpost.org" - SummitPost route page
4. "{peak_name} site:mountaineers.org" - Mountaineers route information
5. "{peak_name} trip report site:cascadeclimbers.com" - Forum discussions
```

**Extract and save URLs for Phase 4 (Report Generation):**
- WTA trip reports URL (if found)
- AllTrails trail page URL (if found)
- SummitPost route/trip reports URL (if found)
- Mountaineers.org route page URL (if found)
- CascadeClimbers forum search URL or relevant thread URLs (if found)

**Optional WebFetch for conditions data:**
- If specific high-value trip reports identified, fetch 1-2 for detailed conditions
- Extract recent dates and conditions mentioned for "Recent Conditions" section

#### Step 3D: Weather Forecast (Open-Meteo API + NOAA)

**Requires coordinates from Phase 2 (latitude, longitude, elevation):**

Gather weather data from multiple sources in parallel:

**Source 1: Open-Meteo Weather API (Primary)**

Use WebFetch to get detailed mountain weather forecast:
```
URL: https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&elevation={peak_elevation_m}&hourly=temperature_2m,precipitation,freezing_level_height,snow_depth,wind_speed_10m,wind_gusts_10m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max&timezone=auto&forecast_days=7

Prompt: "Parse the JSON response and extract:
- Daily weather summary for 6-7 days (date, conditions based on weather_code, temps, precip probability)
- Freezing level height in feet for each day (convert from meters)
- Snow depth if applicable
- Wind speeds and gusts
- Organize by calendar date with day-of-week
- **IMPORTANT:** The timezone parameter is set to 'auto', so dates are in local time. Calculate day-of-week from the actual date strings in the JSON response (YYYY-MM-DD format). Today's date in local time is {current_date}.
- Map weather_code to descriptive conditions (0=clear, 1-3=partly cloudy, 45-48=fog, 51-67=rain, 71-77=snow, 80-82=showers, 95-99=thunderstorms)"
```

**Weather Code to Icon/Description mapping:**
- 0: ☀️ Clear
- 1-3: ⛅ Partly cloudy
- 45-48: 🌫️ Fog
- 51-67: 🌧️ Rain
- 71-77: ❄️ Snow
- 80-82: 🌧️ Showers
- 95-99: ⛈️ Thunderstorms

**Source 2: Open-Meteo Air Quality API**

Use WebFetch to get air quality forecast:
```
URL: https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&hourly=pm2_5,pm10,us_aqi&timezone=auto&forecast_days=7

Prompt: "Parse the JSON and determine air quality for the forecast period:
- Check US AQI values: 0-50 (good), 51-100 (moderate), 101-150 (unhealthy for sensitive), 151-200 (unhealthy), 201-300 (very unhealthy), 301+ (hazardous)
- Check PM2.5 and PM10 levels
- Identify any days with AQI >100 (concerning for outdoor activities)
- Return overall assessment and any days to be cautious"
```

**Source 3: NOAA/NWS Point Forecast (Supplemental)**

Use WebFetch for detailed text forecast and warnings:
```
URL: https://forecast.weather.gov/MapClick.php?textField1={lat}&textField2={lon}
Prompt: "Extract:
- Detailed text forecasts for context
- Any weather warnings or alerts
- Hazardous weather outlook"
```

**Source 4: NWAC Mountain Weather (if applicable)**

If in avalanche season (roughly Nov-Apr), check NWAC mountain weather:
```
WebFetch: https://nwac.us/mountain-weather-forecast/
Prompt: "Extract general mountain weather patterns for the Cascades region including synoptic pattern and multi-day trend"
```

**Data to extract and save for Phase 4:**
- 6-7 day forecast with conditions, temps, precipitation, wind
- **Freezing level height for each day** (from Open-Meteo)
- Snow depth changes (from Open-Meteo)
- **Air quality assessment** (good/moderate/poor, note any concerning days)
- Weather warnings or alerts (from NOAA)
- Mountain-Forecast.com URL for manual checking (find via WebSearch, don't scrape)
- **Open-Meteo Weather Link:** Construct from coordinates and elevation:
  `https://open-meteo.com/en/docs#latitude={lat}&longitude={lon}&elevation={peak_elevation_m}&hourly=&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto`
- **Open-Meteo Air Quality Link:** Construct from coordinates:
  `https://open-meteo.com/en/docs/air-quality-api#latitude={lat}&longitude={lon}&hourly=&daily=&timezone=auto`

**Error Handling:**
- If Open-Meteo API fails: Fall back to NOAA only, note reduced data quality in gaps
- If Air Quality API fails: Note in gaps, continue without AQ data
- If NOAA WebFetch fails: Continue with Open-Meteo data only
- If NWAC not in season or fails: Skip this source
- **Always provide manual check links** for Mountain-Forecast.com and NOAA even when API data retrieved

#### Step 3E: Avalanche Forecast (Python Script)

**Requires coordinates from Phase 2. Only for peaks with glaciers or avalanche terrain (elevation >6000ft in winter months):**

```bash
cd skills/route-researcher/tools
uv run python fetch_avalanche.py --region "North Cascades" --coordinates "{lat},{lon}"
```

**Expected Output:** JSON with NWAC avalanche forecast

**Error Handling:**
- Script not yet implemented: Note "Avalanche script pending - check NWAC.us manually"
- Script fails: Note in gaps with link to NWAC
- Not applicable (low elevation, summer): Skip this step

#### Step 3F: Daylight Calculations (Sunrise-Sunset.org API)

**Requires coordinates from Phase 2 (latitude, longitude):**

Use WebFetch to get sunrise/sunset data from Sunrise-Sunset.org API:

```
URL: https://api.sunrise-sunset.org/json?lat={latitude}&lng={longitude}&date={YYYY-MM-DD}&formatted=0
Prompt: "Extract the following data from the JSON response:
- Sunrise time (convert from UTC to local time if needed)
- Sunset time (convert from UTC to local time if needed)
- Day length (convert seconds to hours and minutes)
- Civil twilight begin/end (useful for alpine starts)
- Solar noon
Format times in a user-friendly way (e.g., '6:45 AM', '8:30 PM')"
```

**Data to extract and save for Phase 4:**
- Sunrise time (local)
- Sunset time (local)
- Day length in hours and minutes
- Civil twilight begin (useful for alpine starts)

**Error Handling:**
- If API call fails: Note in gaps section with link to timeanddate.com or sunrise-sunset.org
- If no coordinates available: Skip this step and note in gaps
- If date is far in future: API should still work, but note that times are calculated

#### Step 3G: Access and Permits (WebSearch)

```
WebSearch queries:
1. "{peak_name} trailhead access"
2. "{peak_name} permit requirements"
3. "{peak_name} forest service road conditions"
```

**Extract:**
- Trailhead names and locations
- Required permits (if any)
- Access notes (road conditions, seasonal closures)

#### Step 3H: Trip Report Identification

**Goal:** Identify trip reports across all sources for comprehensive route beta coverage.

This step synthesizes information from:
- PeakBagger ascent data (from Step 3B)
- Trip report source URLs (from Step 3C)

**Selection Strategy:**

Gather a representative sample of reports covering different perspectives:
- **Recency:** Recent reports (last 1-2 years) for current conditions
- **Variety:** Mix of sources (PeakBagger, WTA, Mountaineers) for diverse experiences
- **Temporal spread:** Include older reports if they provide unique insights
- **Sample size:** Aim for 10-15 reports total to capture range of conditions and perspectives

**Note:** Report length/word count is NOT a quality indicator. A concise 50-word report with specific route beta is more valuable than a 500-word narrative about the drive. Focus on reports that have substantive content regardless of length.

**PeakBagger Trip Reports (uses data from Step 3B):**

From the ascent data already retrieved in Step 3B:

1. **Identify reports with trip report content:**
   - Filter: Only ascents where `trip_report.word_count > 0`
   - Sort by date (most recent first) to identify recent reports
   - Also identify reports from various time periods (not just recent)

2. **Extract for each report:**
   - Date (`date` field)
   - Climber name (`climber.name` field)
   - Word count (`trip_report.word_count` field)
   - Ascent URL (`url` field)

3. **Select diverse sample:**
   - Take 5-10 recent reports (last 1-2 years)
   - Include 2-5 older reports if they provide unique insights
   - Include reports with GPX tracks when available (useful for users to download and verify route)
   - Mix of seasons if available

**WTA Trip Reports (if WTA URL found in Step 3C):**

If WTA URL was found, extract trip reports using the AJAX endpoint:

```bash
# Construct endpoint: {wta_url}/@@related_tripreport_listing
cd skills/route-researcher/tools
uv run python cloudscrape.py "{wta_url}/@@related_tripreport_listing"
```

Parse HTML to extract for each report: date, author, trip report URL. Target 10-15 individual URLs, prioritize recent but include variety of dates.

**Error Handling:**
- If extraction yields <5 reports: Note in "Information Gaps"
- If cloudscrape.py fails: Note with WTA browse link

**Mountaineers.org Trip Reports (if Mountaineers URL found in Step 3C):**

If Mountaineers URL was found, extract trip reports from the trip-reports endpoint:

```bash
# Construct endpoint: {mountaineers_url}/trip-reports
cd skills/route-researcher/tools
uv run python cloudscrape.py "{mountaineers_url}/trip-reports"
```

Parse HTML to extract for each report: date, title, author, trip report URL. Select top 3-5 most recent reports.

**Error Handling:**
- If cloudscrape.py fails: Note in "Information Gaps"
- If no trip reports found: Note in "Information Gaps"

**Extract and save for Phase 4 (Report Generation):**

**High-Quality PeakBagger Reports:**
- List of top 5-10 reports by word count (regardless of date)
- Each with: date, climber name, word count, URL

**Recent PeakBagger Reports:**
- List of top 3-5 most recent reports with trip reports
- Each with: date, climber name, word count, URL

**WTA Reports:**
- List of top 3-5 reports (recent or detailed)
- Each with: date, author/title, URL

**Mountaineers Reports:**
- List of top 3-5 reports (recent or detailed)
- Each with: date, title, URL

**Error Handling:**
- **WTA:** If cloudscrape.py fails for AJAX endpoint: Note in gaps, include WTA browse link only
- **WTA:** If HTML parsing yields <5 reports: Note as parsing failure in gaps
- **Mountaineers:** Do not attempt extraction - note limitation in gaps, include browse link
- **AllTrails:** Do not attempt trip report extraction - note limitation in gaps if AllTrails URL was found
- If no trip reports found on successfully fetched pages: Note in gaps, include browse link
- If WTA/Mountaineers URLs not found in Step 3C: Skip those sources
- PeakBagger data already available from Step 3B, no additional fetch needed

#### Step 3I: Fetch Trip Report Content

**Goal:** Fetch 10-15 trip reports to get representative sample of conditions and experiences (runs after Step 3H identifies candidates).

**Selection from Step 3H results:**
- Recent reports (last 1-2 years) for current conditions
- Mix of sources (PeakBagger, WTA, Mountaineers)
- Variety of dates/seasons to capture different conditions
- Include some reports with GPX tracks when available (provides users with downloadable route data for verification)

**Fetching:**

**PeakBagger:** Use CLI to fetch full trip report content:
```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger ascent show {ascent_id} --format json
```

**WTA/Mountaineers:** Use cloudscrape.py to fetch individual trip report pages:
```bash
cd skills/route-researcher/tools
uv run python cloudscrape.py "{trip_report_url}"
```

**Extract and organize by theme:**
- **Route:** Landmarks, variations, navigation details, actual times/distances
- **Crux:** Difficulty assessments, technical requirements, conditions impact
- **Hazards:** Rockfall, exposure, route-finding challenges, seasonal hazards, approach hazards
- **Gear:** What people used/needed, seasonal variations
- **Conditions:** Snow/ice timing, trail conditions, best months

**Error Handling:**
- If CLI/cloudscrape fails: Note which reports failed, continue with others
- If report appears to have no substantive content: Note and continue
- Minimum target: Successfully fetch at least 5-8 reports with useful content

**Phase 3 Execution Summary:**

Phase 3 has two execution stages:

**Stage 1 - Parallel Execution (Steps 3A through 3H):**
- Step 3A: Route descriptions (WebSearch + WebFetch)
- Step 3B: Ascent statistics (peakbagger-cli)
- Step 3C: Trip report sources (WebSearch)
- Step 3D: Weather forecast (Open-Meteo + NOAA)
- Step 3E: Avalanche forecast (Python script)
- Step 3F: Daylight calculations (Sunrise-Sunset API)
- Step 3G: Access and permits (WebSearch)
- Step 3H: High-quality trip report identification

**Stage 2 - Sequential Execution (Step 3I):**
- Step 3I: Fetch high-quality trip report content (MUST run after 3H completes)

**Performance Benefit:** Stage 1 total time = max(time(3A), time(3B), ..., time(3H)) instead of summing all step times. Stage 2 runs after Stage 1 completes to use identified reports from Step 3H.

### Phase 4: Route Analysis

**Goal:** Analyze gathered data to determine route characteristics and synthesize information.

#### Step 4A: Determine Route Type

Based on route descriptions, elevation, and gear mentions, classify as:
- **Glacier:** Crevasses mentioned, glacier travel, typically >8000ft
- **Rock:** Technical climbing, YDS ratings (5.x), protection mentioned
- **Scramble:** Class 2-4, exposed but non-technical
- **Hike:** Class 1-2, trail-based, minimal exposure

#### Step 4B: Synthesize Route Information from Multiple Sources

**Goal:** Combine trip reports (Step 3I), route descriptions (Step 3A), and other sources into comprehensive route beta.

**Source Priority:**
1. Trip reports (Step 3I) - first-hand experiences
2. Route descriptions (Step 3A) - published beta baseline
3. PeakBagger/ascent data (Steps 2 & 3B) - basic info, patterns

**Synthesis Pattern for Route, Crux, and Hazards:**

1. **Start with baseline** from route descriptions (standard route name, published difficulty)
2. **Enrich with trip report details** (landmarks, specific conditions, actual experiences)
3. **Note conflicts** when trip reports disagree with published info
4. **Highlight consensus** ("Multiple reports mention...")
5. **Include specifics** (elevations, locations, quotes)

**Example (Route Description):**
> "The standard route follows the East Ridge (Class 3). Multiple trip reports mention a well-cairned use trail branching right at 4,800 ft—this is the correct turn. The use trail climbs through talus (described as 'tedious' and 'ankle-rolling'). In early season, this section may be snow-covered, requiring microspikes."

**Apply this pattern to:**
- **Route:** Use baseline structure, add landmarks/navigation from trip reports, include actual times
- **Crux:** Describe location/difficulty, add trip report assessments, note conditions-dependent variations
- **Hazards:** Extract ALL hazards from trip reports (rockfall, exposure, route-finding, seasonal), organize by type, include specific locations and mitigation strategies. Be comprehensive—safety-critical.

**Extract Key Information:**

From all synthesized data, identify:
- **Difficulty Rating:** YDS class, scramble grade, or general difficulty (validated by trip reports)
- **Crux:** Hardest/most technical section of route (synthesized above)
- **Hazards:** All identified hazards (synthesized above)
- **Notable Gear:** Any unusual or important gear mentioned in trip reports or beta (to be included in relevant sections, not as standalone section)
- **Trailhead:** Name and approximate location
- **Distance/Gain:** Round-trip distance and elevation gain (compare published vs actual trip report data)
- **Time Estimates:** Calculate three-tier pacing based on distance and gain:
  - **Fast pace:** Calculate based on 2+ mph and 1000+ ft/hr gain rate
  - **Moderate pace:** Calculate based on 1.5-2 mph and 700-900 ft/hr gain rate
  - **Leisurely pace:** Calculate based on 1-1.5 mph and 500-700 ft/hr gain rate
  - Use the **slower** of distance-based or gain-based calculations for each tier
  - Example: For 4 miles, 2700 ft gain:
    - Fast: max(4mi/2mph, 2700ft/1000ft/hr) = max(2hr, 2.7hr) = ~2.5-3 hours
    - Moderate: max(4mi/1.5mph, 2700ft/800ft/hr) = max(2.7hr, 3.4hr) = ~3-4 hours
    - Leisurely: max(4mi/1mph, 2700ft/600ft/hr) = max(4hr, 4.5hr) = ~4-5 hours
- **Freezing Level Analysis:** Compare peak elevation with forecasted freezing levels:
  - **Include Freezing Level Alert if:** Any day in forecast has freezing level within 2000 ft of peak elevation
  - **Omit if:** Freezing level stays >2000 ft above peak throughout forecast (typical summer conditions)
  - Example: 5,469 ft peak with 5,000-8,000 ft freezing levels → Include alert (marginal conditions)
  - Example: 4,000 ft peak with 10,000+ ft freezing levels → Omit alert (well above summit)

#### Step 4C: Identify Information Gaps

Explicitly document what data was **not found or unreliable:**
- Missing trip reports
- No GPS tracks available
- Script failures (weather, avalanche, daylight)
- Conflicting information between sources
- Limited seasonal data

### Phase 5: Report Generation

**Goal:** Create comprehensive Markdown document following the template.

#### Step 5A: Generate Report Content

Create report in the current working directory: `{YYYY-MM-DD}-{peak-name-lowercase-hyphenated}.md`

**Filename Examples:**
- `2025-10-20-mount-baker.md`
- `2025-10-20-sahale-peak.md`

**Location:** Reports are generated in the user's current working directory, not in the plugin installation directory.

**Structure and Formatting:**

Read `assets/report-template.md` and follow it exactly for:
- Section structure and headings
- Content formatting (how to present ascent data, trip report links, etc.)
- Conditional sections (when to include/exclude sections based on available data)
- All layout and presentation decisions

The template is the **single source of truth** for report formatting. Phase 3 (Data Gathering) specifies **what data to extract**. This phase (Phase 5) uses the template to determine **how to present that data**.

#### Step 5B: Markdown Formatting Rules

Follow these formatting rules to ensure proper Markdown rendering:

1. **Blank lines before lists:** ALWAYS add a blank line before starting a bullet or numbered list
   ```markdown
   ✅ CORRECT:
   This is a paragraph.

   - First bullet
   - Second bullet

   ❌ INCORRECT:
   This is a paragraph.
   - First bullet  (missing blank line)
   ```

2. **Blank lines after section headers:** Always have a blank line after ## or ### headers

3. **Consistent list formatting:**
   - Use `-` for unordered lists (not `*` or `+`)
   - Indent sub-items with 2 spaces
   - Keep list items concise (if >2 sentences, consider paragraphs instead)

4. **Break up long text blocks:**
   - Paragraphs >4 sentences should be split or bulleted
   - Sequential steps should use numbered lists (1. 2. 3.)
   - Related items should use bullet lists

5. **Bold formatting:** Use `**text**` for emphasis, not for list item headers without bullets

6. **Hazards and Safety:** Use bullet lists with sub-items:
   ```markdown
   **Known Hazards:**

   - **Route-finding:** Orange markers help but can be missed
   - **Slippery conditions:** Boulders treacherous when wet/icy
   - **Weather exposure:** Above treeline sections exposed to elements
   ```

7. **Information that continues after colon:** Must have blank line before list:
   ```markdown
   ✅ CORRECT:
   Winter access adds the following:

   - **Additional Distance:** 5.6 miles
   - **Additional Elevation:** 1,700 ft

   ❌ INCORRECT:
   Winter access adds the following:
   - **Additional Distance:** 5.6 miles  (missing blank line)
   ```

#### Step 5C: Write Report File

Use the Write tool to create the file in the current working directory.

**Verification:**
- Use proper filename format (YYYY-MM-DD-peak-name.md)
- Save file in user's current working directory
- Validate Markdown syntax per formatting rules above
- Check that all lists have blank lines before them

### Phase 6: Report Review & Validation

**Goal:** Systematically review the generated report for inconsistencies, errors, and quality issues before presenting to the user.

This phase ensures report quality by catching common issues that may occur during automated generation.

#### Step 6A: Read Generated Report

Read the complete report file that was just created in Phase 5.

#### Step 6B: Systematic Quality Checks

Perform the following checks in order:

**1. Factual Consistency:**
- Verify dates match their stated day-of-week (e.g., "Thu Nov 6, 2025" is actually a Thursday)
- Verify narrative day-of-week references match the actual date
- Check coordinates, elevations, and distances are consistent across all mentions
- Verify weather forecasts align logically (freezing levels match precipitation types)
- Check difficulty ratings are consistent between sections

**2. Mathematical Accuracy:**
- Verify elevation gains add up correctly
- Check time estimates are reasonable given distance and elevation gain
- Verify pace calculations match stated mph/ft per hour rates
- Check unit conversions are correct (feet to meters, etc.)

**3. Internal Logic:**
- Verify hazard warnings align with route descriptions
- Check recommendations match current conditions (not recommending a route when hazards are extreme)
- Verify seasonal considerations are consistent with forecast data
- Check crux descriptions match the overall difficulty rating

**4. Completeness:**
- Check for placeholder texts that weren't replaced (e.g., {peak_name}, {YYYY-MM-DD})
- Verify all referenced links are actually provided
- Check mandatory sections are present (Overview, Route, Current Conditions, Trip Reports, Information Gaps, Data Sources)
- Verify trip report sections have actual URLs or proper placeholders

**5. Formatting Issues:**
- Check markdown headers are properly structured
- Verify lists have proper blank lines before them (per Phase 5B formatting rules)
- Check tables are properly formatted
- Verify bold/emphasis markers are used correctly and not overdone

**6. Source Consistency:**
- Verify quoted or paraphrased details are accurate to sources (if in doubt, re-check)
- Check conflicting information from different sources is acknowledged
- Verify URLs are correct and complete

**7. Safety & Responsibility:**
- Verify critical hazards are properly emphasized
- Check AI disclaimer is present and prominent
- Verify users are directed to verify information from primary sources
- Check limitations are explicitly stated in Information Gaps

#### Step 6C: Fix Issues

For each issue found:
1. **Document the issue** mentally (what's wrong, where it is, severity)
2. **Fix the issue** immediately by editing the report file
3. **Verify the fix** doesn't create new issues

**Priority for fixes:**
- **Critical:** Safety errors, factual errors, missing disclaimers (MUST fix)
- **Important:** Completeness, usability, consistency issues (SHOULD fix)
- **Minor:** Formatting, polish issues (FIX if quick, otherwise acceptable)

**Common issues to watch for:**
- Day-of-week mismatches (e.g., report dated Thursday but says "today (Wednesday)")
- Missing blank lines before lists (violates Phase 5B rules)
- Placeholder text not replaced
- Inconsistent elevation or distance values
- Weather data that doesn't make sense (e.g., snow at 12,000 ft freezing level)

#### Step 6D: Save Corrected Report

If any issues were found and fixed:
1. Use Edit or Write tool to save the corrected report
2. Verify the file is saved in the correct location
3. Proceed to Phase 7

If no issues were found:
1. Proceed directly to Phase 7

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
- **Universal fallback pattern:** Always try WebFetch first, then cloudscrape.py if it fails
- **Automatic retry:** If WebFetch fails or returns incomplete data, immediately retry with cloudscrape.py
- **Graceful degradation:** Missing one source shouldn't stop entire research
- **Document gaps:** Note which sources were unavailable (both WebFetch AND cloudscrape.py failed)
- **Prioritize safety:** If critical safety info (avalanche, hazards) unavailable, emphasize in gaps section

## Execution Timeouts

- **Individual Python scripts:** 30 seconds each
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

### Current Status (as of 2025-10-21)

**Implemented:**
- **peakbagger-cli** integration for peak search, info, and ascent data
- Python tools directory structure
- Report generation in user's current working directory
- **cloudscrape.py** - Universal fallback for WebFetch failures, works with ANY website including:
  - Cloudflare-protected sites (SummitPost, PeakBagger, Mountaineers.org)
  - AllTrails (when WebFetch fails)
  - WTA (when WebFetch fails)
  - Any other site that blocks or limits WebFetch access
- **Two-tier fetching strategy:** WebFetch first, cloudscrape.py as automatic fallback
- **Open-Meteo Weather API** for mountain weather forecasts (temperature, precipitation, freezing level, wind)
- **Open-Meteo Air Quality API** for AQI forecasting (US AQI scale with conditional alerts)
- Multi-source weather gathering (Open-Meteo, NOAA/NWS, NWAC)
- Adaptive ascent data retrieval based on peak popularity
- **Sunrise-Sunset.org API** for daylight calculations (sunrise, sunset, civil twilight, day length)
- **High-quality trip report identification** across PeakBagger and WTA sources
- **WTA AJAX endpoint** for trip report extraction (`{wta_url}/@@related_tripreport_listing`)

**Pending Implementation:**
- `fetch_avalanche.py` - NWAC avalanche data (currently using WebSearch/WebFetch as fallback)
- **Browser automation** for Mountaineers.org and AllTrails trip report extraction (requires Playwright/Chrome)
  - Current: Both sites load content via JavaScript, cloudscrape.py cannot extract
  - Future: Add browser automation as 3rd-tier fallback

**When Python scripts are not yet implemented:**
- Note in "Information Gaps" section
- Provide manual check links
- Continue with available data
- Don't block report generation

### peakbagger-cli Command Reference (v1.7.0)

All commands use `--format json` for structured output. Run via:
```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger <command> --format json
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

### Google Maps and USGS Links

#### Summit Coordinates Links

**Google Maps (for summit coordinates):**
```
https://www.google.com/maps/search/?api=1&query={latitude},{longitude}
```
Example: `https://www.google.com/maps/search/?api=1&query=48.7768,-121.8144`

**USGS TopoView (for summit coordinates):**
```
https://ngmdb.usgs.gov/topoview/viewer/#{{latitude}}/{longitude}/15
```
Example: `https://ngmdb.usgs.gov/topoview/viewer/#17/48.7768/-121.8144`

**Note:** Use decimal degree format for coordinates. TopoView uses zoom level in URL (15-17 works well for peaks).

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

