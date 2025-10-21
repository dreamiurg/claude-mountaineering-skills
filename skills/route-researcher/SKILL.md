---
name: route-researcher
description: Research Pacific Northwest mountain peaks and generate comprehensive route beta reports
---

# Route Researcher

Research mountain peaks in the Pacific Northwest and generate comprehensive route beta reports combining data from multiple sources including PeakBagger, weather forecasts, avalanche conditions, and trip reports.

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

## Orchestration Workflow

### Phase 1: Peak Validation

**Goal:** Identify and validate the specific peak to research.

1. **Extract Peak Name** from user message
   - Look for peak names, mountain names, or climbing objectives
   - Common patterns: "Mt Baker", "Mount Rainier", "Sahale Peak", etc.

2. **Search PeakBagger** using peakbagger-cli:
   ```bash
   uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git peakbagger search "{peak_name}" --format json
   ```
   - Parse JSON output to extract peak matches
   - Each result includes: peak_id, name, elevation (feet/meters), location, url

3. **Handle Multiple Matches:**
   - If **multiple peaks** found: Use AskUserQuestion to present options
     - Show peak name, elevation, and location for each
     - Let user select the correct peak
     - Provide "Other" option if none match

   - If **single match** found: Confirm with user
     - Show: "Found: [Peak Name] ([Elevation], [Location]) - [PeakBagger URL]"
     - Use AskUserQuestion: "Is this the correct peak?"

   - If **no matches** found:
     - Try peak name variations (Mt/Mount, with state/range)
     - If still no results, use AskUserQuestion to ask for:
       - A different peak name variation
       - Direct PeakBagger peak ID or URL
       - General PeakBagger search

4. **Extract Peak ID:**
   - From search results JSON, extract the `peak_id` field
   - Store for use in subsequent peakbagger-cli commands
   - Also store the PeakBagger URL for reference links

### Phase 2: Data Gathering

**Goal:** Gather comprehensive information from all available sources.

Execute the following data collection steps **in parallel where possible** to minimize total execution time:

#### 2A. PeakBagger Peak Information (peakbagger-cli)

Retrieve detailed peak information using the peak ID from Phase 1:

```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git peakbagger info {peak_id} --format json
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

#### 2B. Route Description Research (WebSearch + WebFetch)

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

**For Cloudflare-protected sites (SummitPost, PeakBagger, Mountaineers.org):**
```bash
cd skills/route-researcher/tools
uv run python cloudscrape.py "{summitpost_or_peakbagger_or_mountaineers_url}"
```
Parse the returned HTML to extract route information.

**For AllTrails:**
Use WebFetch with prompt:
```
Prompt: "Extract route information including:
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

**For other sites (Mountain Project, WTA, etc.):**
Use WebFetch with prompt:
```
Prompt: "Extract route information including:
- Approach details
- Route description and key sections
- Technical difficulty (YDS class, scramble grade, etc.)
- Crux description
- Distance and elevation gain
- Estimated time
- Known hazards"
```

**Error Handling:**
- If no route descriptions found: Note in gaps and provide general guidance
- If conflicting information: Note discrepancies in report
- If cloudscrape.py fails: Try WebFetch as fallback, then note if both fail

#### 2C. Peak Ascent Statistics (peakbagger-cli)

Retrieve ascent data and patterns using the peak ID:

**Step 1: Get overall ascent statistics**
```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git peakbagger peak-ascents {peak_id} --format json
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
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git peakbagger peak-ascents {peak_id} --format json --within 1y --list-ascents
```
Recent data (1 year) is sufficient for active peaks.

**For moderate peaks (10-50 ascents total):**
```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git peakbagger peak-ascents {peak_id} --format json --within 5y --list-ascents
```
Expand to 5 years to get meaningful sample size.

**For rarely-climbed peaks (<10 ascents total):**
```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git peakbagger peak-ascents {peak_id} --format json --list-ascents
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

#### 2D. Trip Report Sources Discovery (WebSearch)

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

#### 2E. Weather Forecast (Multiple Sources)

**Only if coordinates available from Step 2A:**

Gather weather data from multiple sources in parallel:

**Source 1: Mountain-Forecast.com (Cloudflare-protected)**

First, search for the peak's mountain-forecast.com page:
```
WebSearch: "{peak_name} site:mountain-forecast.com"
```

Then use cloudscrape.py to fetch the forecast page:
```bash
cd skills/route-researcher/tools
uv run python cloudscrape.py "https://www.mountain-forecast.com/peaks/{peak-slug}/forecasts/{elevation_m}"
```

Parse HTML to extract:
- 6-day forecast (temperature, precipitation, wind, snow level)
- Summit-level conditions
- Mid-mountain conditions if available
- Freezing level

**Source 2: NOAA/NWS Point Forecast**

Use WebFetch to get NOAA point forecast:
```
URL: https://forecast.weather.gov/MapClick.php?textField1={lat}&textField2={lon}
Prompt: "Extract the 7-day weather forecast including:
- Daily high/low temperatures
- Precipitation chances
- Wind speed and direction
- Detailed day/night forecasts
- Any weather warnings or alerts"
```

**Source 3: NWAC Mountain Weather (if available)**

If in avalanche season (roughly Nov-Apr), check NWAC mountain weather:
```
WebFetch: https://nwac.us/mountain-weather-forecast/
Prompt: "Extract general mountain weather patterns for the Cascades region including:
- Synoptic weather pattern
- Freezing levels
- Snow level
- Wind forecast
- Multi-day weather trend"
```

**Error Handling:**
- If mountain-forecast.com URL not found: Continue with other sources
- If cloudscrape.py fails: Note in gaps, provide manual link
- If NOAA WebFetch fails: Note in gaps
- If NWAC not in season or fails: Skip this source
- Timeout: 60s for cloudscrape.py, default for WebFetch
- **Always provide manual check links** even when data successfully retrieved

#### 2F. Avalanche Forecast (Python Script)

**Only for peaks with glaciers or avalanche terrain (elevation >6000ft in winter months):**

```bash
cd skills/route-researcher/tools
uv run python fetch_avalanche.py --region "North Cascades" --coordinates "{lat},{lon}"
```

**Expected Output:** JSON with NWAC avalanche forecast

**Error Handling:**
- Script not yet implemented: Note "Avalanche script pending - check NWAC.us manually"
- Script fails: Note in gaps with link to NWAC
- Not applicable (low elevation, summer): Skip this step

#### 2G. Daylight Calculations (Python Script)

```bash
cd skills/route-researcher/tools
uv run python calculate_daylight.py --date "{YYYY-MM-DD}" --coordinates "{lat},{lon}"
```

**Expected Output:** JSON with sunrise, sunset, daylight hours

**Error Handling:**
- Script not yet implemented: Use general guidance or note gap
- Script fails: Calculate approximate values or note gap
- No coordinates: Skip this step

#### 2H. Access and Permits (WebSearch)

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

### Phase 3: Route Analysis and Synthesis

**Goal:** Analyze gathered data to determine route characteristics and synthesize information.

#### 3A. Determine Route Type

Based on route descriptions, elevation, and gear mentions, classify as:
- **Glacier:** Crevasses mentioned, glacier travel, typically >8000ft
- **Rock:** Technical climbing, YDS ratings (5.x), protection mentioned
- **Scramble:** Class 2-4, exposed but non-technical
- **Hike:** Class 1-2, trail-based, minimal exposure

#### 3B. Extract Key Information

From all gathered data, identify:
- **Difficulty Rating:** YDS class, scramble grade, or general difficulty
- **Crux:** Hardest/most technical section of route
- **Hazards:** Rockfall, crevasses, exposure, weather, avalanche danger
- **Notable Gear:** Any unusual or important gear mentioned in trip reports or beta (to be included in relevant sections, not as standalone section)
- **Trailhead:** Name and approximate location
- **Distance/Gain:** Round-trip distance and elevation gain
- **Time Estimate:** Typical completion time

#### 3C. Identify Information Gaps

Explicitly document what data was **not found or unreliable:**
- Missing trip reports
- No GPS tracks available
- Script failures (weather, avalanche, daylight)
- Conflicting information between sources
- Limited seasonal data

### Phase 4: Report Generation

**Goal:** Create comprehensive Markdown document following the template.

#### 4A. Generate Report Content

Create report in the current working directory: `{YYYY-MM-DD}-{peak-name-lowercase-hyphenated}.md`

**Filename Examples:**
- `2025-10-20-mount-baker.md`
- `2025-10-20-sahale-peak.md`

**Location:** Reports are generated in the user's current working directory, not in the plugin installation directory.

**Structure and Formatting:**

**CRITICAL:** Read `assets/report-template.md` and follow it exactly for:
- Section structure and headings
- Content formatting (how to present ascent data, trip report links, etc.)
- Conditional sections (when to include/exclude sections based on available data)
- All layout and presentation decisions

The template is the **single source of truth** for report formatting. Phase 2 (Data Gathering) specifies **what data to extract**. This phase (Phase 4) uses the template to determine **how to present that data**.

#### 4B. Markdown Formatting Rules

**CRITICAL:** Follow these formatting rules to ensure proper Markdown rendering:

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

#### 4C. Write Report File

Use the Write tool to create the file in the current working directory.

**Verification:**
- Use proper filename format (YYYY-MM-DD-peak-name.md)
- Save file in user's current working directory
- Validate Markdown syntax per formatting rules above
- Check that all lists have blank lines before them

### Phase 5: Completion

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
- **Graceful degradation:** Missing one source shouldn't stop entire research
- **Document gaps:** Note which sources were unavailable
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
- cloudscrape.py for Cloudflare-protected sites (SummitPost, Mountaineers.org, Mountain-Forecast.com)
- Multi-source weather gathering (Mountain-Forecast.com, NOAA/NWS, NWAC)
- Adaptive ascent data retrieval based on peak popularity

**Pending Implementation:**
- `fetch_avalanche.py` - NWAC avalanche data (currently using WebSearch/WebFetch as fallback)
- `calculate_daylight.py` - Sunrise/sunset calculations

**When Python scripts are not yet implemented:**
- Note in "Information Gaps" section
- Provide manual check links
- Continue with available data
- Don't block report generation

### Design Evolution: peakbagger-cli Integration

**Latest Design (2025-10-21):**
- Use **peakbagger-cli** (via uvx) for all PeakBagger data retrieval:
  - Peak search with structured JSON output
  - Peak information (elevation, coordinates, routes, etc.)
  - Ascent statistics and trip report links
- Use **cloudscrape.py** only for non-PeakBagger Cloudflare-protected sites:
  - SummitPost route pages
  - Mountaineers.org route information
  - Mountain-Forecast.com weather forecasts
- Reserve Python scripts for **calculations only** (weather, avalanche, daylight)

**Previous Design (2025-10-20):**
- Used WebSearch to find PeakBagger peak pages
- Used WebFetch or cloudscrape.py to extract data from PeakBagger
- Required HTML parsing of PeakBagger pages

**Rationale for peakbagger-cli:**
- Structured JSON output eliminates HTML parsing complexity
- Built-in rate limiting and Cloudflare bypass
- Reliable ascent data and trip report discovery
- Better maintainability (less brittle than HTML parsing)
- Native support for filtering ascents by date, GPX, and trip reports
- Adaptive timeframe selection based on peak popularity

### Peak Name Variations

Common variations to try if initial search fails:
- "Mt" → "Mount"
- "St" → "Saint"
- Add state/range: "Baker, WA" or "Baker, North Cascades"
- Try just surname: "Baker" instead of "Mt Baker"

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

## Testing Checklist

When testing this skill, verify:
- [ ] Peak validation works with single match (peakbagger-cli search)
- [ ] Peak validation works with multiple matches
- [ ] Peak validation handles no matches gracefully
- [ ] peakbagger-cli info extracts peak data correctly (JSON format)
- [ ] peakbagger-cli peak-ascents retrieves ascent statistics
- [ ] Adaptive timeframe selection works (1y/5y/all based on popularity)
- [ ] Ascent trip report links are included in output
- [ ] Route description synthesis is comprehensive
- [ ] Trip reports from multiple sources (PeakBagger + CascadeClimbers)
- [ ] Python scripts execute (when implemented)
- [ ] Python script failures handled gracefully
- [ ] Information gaps documented explicitly
- [ ] Report follows template structure
- [ ] Report saves to correct location
- [ ] Filename format is correct
- [ ] Safety disclaimer is prominent
- [ ] Completion message is helpful

## Example Invocations

**Example 1: Simple peak name**
```
User: "Research Mt Baker"

Skill Actions:
1. uvx peakbagger search "Mt Baker" --format json
2. Find: Mount Baker (10,786 ft, peak_id: 2296) - North Cascades, WA
3. Confirm with user
4. Gather data from all sources in parallel:
   - uvx peakbagger info 2296 --format json
   - uvx peakbagger peak-ascents 2296 --format json (check total count)
   - uvx peakbagger peak-ascents 2296 --format json --within 1y --list-ascents (popular peak)
   - Route descriptions via WebSearch/WebFetch
   - Weather forecasts
5. Generate report: 2025-10-21-mount-baker.md (in current directory)
6. Report completion
```

**Example 2: Ambiguous peak name**
```
User: "Research Sahale Peak"

Skill Actions:
1. uvx peakbagger search "Sahale Peak" --format json
2. Find: Multiple results:
   - Sahale Peak (8,680 ft, peak_id: 1798) - North Cascades, WA
   - Sahale Arm (7,600 ft, peak_id: 1799) - North Cascades, WA
3. Present options to user with AskUserQuestion
4. User selects Sahale Peak (peak_id: 1798)
5. Continue with data gathering using peak_id 1798
```

**Example 3: Rarely-climbed peak**
```
User: "Research Vesper Peak"

Skill Actions:
1. uvx peakbagger search "Vesper Peak" --format json
2. Find: Vesper Peak (6,214 ft, peak_id: 1234) - North Cascades, WA
3. Confirm with user
4. uvx peakbagger peak-ascents 1234 --format json
5. Discover: Only 8 total ascents recorded
6. uvx peakbagger peak-ascents 1234 --format json --list-ascents (get all ascents, no date filter)
7. Note in report: "Limited ascent data available (8 total ascents recorded)"
8. Continue with other data sources
```

---

**Skill Version:** --help
**Last Updated:** 2025-10-21
**Status:** Ready for execution (with Python scripts pending)
