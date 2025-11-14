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
- [ ] Phase 3: Data Gathering (dispatch agents for parallel data collection)
  - [ ] Phase 3 Stage 1: Dispatch agents (Steps 3A-3C - 6 agents in parallel)
  - [ ] Phase 3 Stage 2: Inline operations (Steps 3D-3E - access/permits, trip reports)
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

**Execution Strategy:** Dispatch multiple specialized agents in parallel to minimize total execution time and reduce context pollution.

**IMPORTANT:** Agents read their own instruction files at runtime to avoid passing large instruction blocks multiple times.

#### Step 3A: Dispatch Route Researcher Agents (Parallel)

Dispatch 5 route-researcher-agent instances in parallel, one per source:

**Agent 1: PeakBagger Source**

```
Task(
  subagent_type="general-purpose",
  prompt="""You are a route-researcher agent.

Read your instructions from: skills/route-researcher/agents/route-researcher.md

Inputs:
- peak_name: "{peak_name}"
- peak_id: {peak_id}
- peak_info: {peak_info}
- source: "PeakBagger"
- extraction_goals: ["ascent_data", "trip_reports"]

Extract ascent statistics and identify trip reports with content."""
)
```

**Agent 2: SummitPost Source**

```
Task(
  subagent_type="general-purpose",
  prompt="""You are a route-researcher agent.

Read your instructions from: skills/route-researcher/agents/route-researcher.md

Inputs:
- peak_name: "{peak_name}"
- peak_info: {peak_info}
- source: "SummitPost"
- extraction_goals: ["route_descriptions"]

Extract route descriptions, difficulty ratings, and hazards."""
)
```

**Agent 3: WTA Source**

```
Task(
  subagent_type="general-purpose",
  prompt="""You are a route-researcher agent.

Read your instructions from: skills/route-researcher/agents/route-researcher.md

Inputs:
- peak_name: "{peak_name}"
- peak_info: {peak_info}
- source: "WTA"
- extraction_goals: ["route_descriptions", "trip_reports"]

Extract route information and trip report listings."""
)
```

**Agent 4: Mountaineers Source**

```
Task(
  subagent_type="general-purpose",
  prompt="""You are a route-researcher agent.

Read your instructions from: skills/route-researcher/agents/route-researcher.md

Inputs:
- peak_name: "{peak_name}"
- peak_info: {peak_info}
- source: "Mountaineers"
- extraction_goals: ["route_descriptions"]

Extract route beta and technical requirements."""
)
```

**Agent 5: AllTrails Source**

```
Task(
  subagent_type="general-purpose",
  prompt="""You are a route-researcher agent.

Read your instructions from: skills/route-researcher/agents/route-researcher.md

Inputs:
- peak_name: "{peak_name}"
- peak_info: {peak_info}
- source: "AllTrails"
- extraction_goals: ["route_descriptions"]

Extract trail information and difficulty ratings."""
)
```

#### Step 3B: Dispatch Conditions Researcher Agent (Parallel)

Dispatch conditions-researcher-agent:

```
Task(
  subagent_type="general-purpose",
  prompt="""You are a conditions-researcher agent.

Read your instructions from: skills/route-researcher/agents/conditions-researcher.md

Inputs:
- coordinates: {latitude}, {longitude}
- elevation: {elevation_m}
- peak_name: "{peak_name}"
- date_range: 7

Gather weather forecast, air quality, avalanche conditions, and daylight data."""
)
```

**Execute all 6 agents in parallel by including all Task calls in a single response.**

#### Step 3C: Aggregate Agent Results

After all agents return, aggregate their structured data:

- Route descriptions from 5 sources
- Ascent statistics and trip report listings from PeakBagger
- Conditions data (weather, air quality, daylight, avalanche)

Store in organized data structure for Phase 4 analysis.

#### Step 3D: Access and Permits (Inline)

Run WebSearch for access information:

```
WebSearch queries:
1. "{peak_name} trailhead access"
2. "{peak_name} permit requirements"
3. "{peak_name} forest service road conditions"
```

Extract trailhead names, required permits, access notes.

#### Step 3E: Fetch Trip Report Content (Inline)

Using trip report URLs identified by route-researcher agents, fetch 10-15 report contents:

**For PeakBagger reports:**

```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger ascent show {ascent_id} --format json
```

**For WTA/Mountaineers reports:**

```bash
cd skills/route-researcher/tools
uv run python cloudscrape.py "{trip_report_url}"
```

**Selection strategy:**
- Recent reports (last 1-2 years)
- Mix of sources
- Variety of dates/seasons
- Include reports with GPX tracks

**Extract and organize by theme:**
- Route: Landmarks, navigation details, actual times/distances
- Crux: Difficulty assessments, conditions impact
- Hazards: Rockfall, exposure, route-finding challenges
- Gear: What people used/needed
- Conditions: Snow/ice timing, trail conditions, best months

### Phase 4: Route Analysis

**Goal:** Analyze gathered data to determine route characteristics and synthesize information.

#### Step 4A: Determine Route Type

Based on route descriptions, elevation, and gear mentions, classify as:
- **Glacier:** Crevasses mentioned, glacier travel, typically >8000ft
- **Rock:** Technical climbing, YDS ratings (5.x), protection mentioned
- **Scramble:** Class 2-4, exposed but non-technical
- **Hike:** Class 1-2, trail-based, minimal exposure

#### Step 4B: Synthesize Route Information from Multiple Sources

**Goal:** Combine trip reports (Step 3E), route descriptions (Step 3A agents), and other sources into comprehensive route beta.

**Source Priority:**
1. Trip reports (Step 3E) - first-hand experiences
2. Route descriptions (Step 3A agents) - published beta baseline
3. PeakBagger/ascent data (Steps 2 & 3A) - basic info, patterns

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

**Goal:** Create comprehensive Markdown document by dispatching report-writer agent.

#### Step 5A: Prepare Data Package

Organize all gathered and analyzed data into structured format:

```python
data_package = {
    "peak_metadata": {
        "peak_name": peak_name,
        "peak_id": peak_id,
        "elevation": elevation,
        "coordinates": (latitude, longitude),
        "location": location,
        "peakbagger_url": peakbagger_url
    },
    "route_data": {
        # Aggregated from route-researcher agents
        "descriptions": [...],
        "difficulty": [...],
        "trip_reports": [...],
        "ascent_stats": {...}
    },
    "conditions_data": {
        # From conditions-researcher agent
        "weather": [...],
        "air_quality": {...},
        "daylight": {...},
        "avalanche": {...}
    },
    "analysis": {
        # From Phase 4
        "route_type": route_type,
        "crux": crux_description,
        "hazards": hazards_list,
        "time_estimates": {...},
        "information_gaps": [...]
    }
}
```

#### Step 5B: Dispatch Report Writer Agent

```
Task(
  subagent_type="general-purpose",
  prompt="""You are the report-writer agent.

Read your instructions from: skills/route-researcher/agents/report-writer.md
Read the template from: skills/route-researcher/assets/report-template.md

Data package:

{json.dumps(data_package, indent=2)}

Generate the report following the template structure exactly.
Save to current working directory with filename format: YYYY-MM-DD-peak-name.md"""
)
```

#### Step 5C: Capture Report File Path

Extract file path from agent response for use in Phase 6.

### Phase 6: Report Review & Validation

**Goal:** Systematically review the generated report for quality issues by dispatching report-reviewer agent.

#### Step 6A: Dispatch Report Reviewer Agent

```
Task(
  subagent_type="general-purpose",
  prompt="""You are the report-reviewer agent.

Read your instructions from: skills/route-researcher/agents/report-reviewer.md

Input:
- report_file_path: "{report_file_path}"

Perform systematic quality checks and fix any critical or important issues."""
)
```

#### Step 6B: Process Validation Results

Review the validation results from the agent:

- If status is PASS or PASS_WITH_FIXES: Proceed to Phase 7
- If status is FAIL: Present issues to user and ask for guidance
- Capture final corrected report path for Phase 7

**Note:** The report-reviewer agent automatically fixes issues and returns the corrected file path.

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

### Architecture (as of 2025-11-06)

The route-researcher skill uses a distributed agent architecture:

**Agent Types:**
- **route-researcher-agent** - Reusable agent for extracting data from mountaineering websites (PeakBagger, SummitPost, WTA, Mountaineers, AllTrails)
- **conditions-researcher-agent** - Gathers location-based environmental data (weather, avalanche, daylight)
- **report-writer-agent** - Generates markdown reports from aggregated data
- **report-reviewer-agent** - Validates report quality before presentation

**Benefits:**
- **Reduced context pollution** - Each agent handles focused tasks with isolated context
- **Parallel execution** - Phase 3 dispatches 6 agents simultaneously
- **Easier maintenance** - Individual agents can be updated without touching orchestrator logic
- **Clear boundaries** - Well-defined inputs, outputs, and responsibilities

**Agent Files:**
- `skills/route-researcher/agents/route-researcher.md`
- `skills/route-researcher/agents/conditions-researcher.md`
- `skills/route-researcher/agents/report-writer.md`
- `skills/route-researcher/agents/report-reviewer.md`

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

