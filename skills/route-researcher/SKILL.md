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

2. **Search PeakBagger** using WebSearch:
   ```
   Query: "{peak_name} site:peakbagger.com peak"
   ```
   - Parse search results for PeakBagger peak page URLs (format: `https://www.peakbagger.com/peak.aspx?pid=...`)
   - Extract peak names, elevations, and locations from search snippets

3. **Handle Multiple Matches:**
   - If **multiple peaks** found: Use AskUserQuestion to present options
     - Show peak name, elevation, and location for each
     - Let user select the correct peak
     - Provide "Other" option if none match

   - If **single match** found: Confirm with user
     - Show: "Found: [Peak Name] ([Elevation], [Location]) - [PeakBagger URL]"
     - Use AskUserQuestion: "Is this the correct peak?"

   - If **no matches** found:
     - Use AskUserQuestion to ask user to provide PeakBagger URL directly
     - Suggest trying a different name variation
     - Provide general PeakBagger search URL

4. **Validate PeakBagger URL:**
   - Ensure URL matches pattern: `https://www.peakbagger.com/peak.aspx?pid=\d+`
   - If user provides URL directly, validate format before proceeding

### Phase 2: Data Gathering

**Goal:** Gather comprehensive information from all available sources.

Execute the following data collection steps **in parallel where possible** to minimize total execution time:

#### 2A. PeakBagger Peak Information (cloudscrape.py)

PeakBagger is protected by Cloudflare, so use the cloudscrape.py tool:

```bash
cd skills/route-researcher/tools
uv run python cloudscrape.py "{peakbagger_url}"
```

This returns the full HTML. Parse it to extract:
- Peak name (from title or h1)
- Elevation (feet and meters)
- Prominence (feet and meters)
- Coordinates (latitude, longitude in decimal degrees)
- Location description (state, range, area)
- Standard route description if available
- Difficulty rating or class if mentioned
- Any notable hazards or warnings mentioned

**Error Handling:**
- If cloudscrape.py fails: Note in "Information Gaps" and continue with WebSearch results
- If specific fields missing in HTML: Mark as "Not available" in gaps section
- Timeout: 60 seconds for cloudscrape.py

#### 2B. Route Description Research (WebSearch + WebFetch)

**Step 1:** Search for route descriptions:
```
WebSearch queries (run in parallel):
1. "{peak_name} route description climbing"
2. "{peak_name} summit post route"
3. "{peak_name} mountain project"
4. "{peak_name} site:mountaineers.org route"
5. "{peak_name} standard route"
```

**Step 2:** Fetch top relevant pages:

**For Cloudflare-protected sites (SummitPost, PeakBagger, Mountaineers.org):**
```bash
cd skills/route-researcher/tools
uv run python cloudscrape.py "{summitpost_or_peakbagger_or_mountaineers_url}"
```
Parse the returned HTML to extract route information.

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

#### 2C. Recent Trip Reports (WebSearch)

Search for recent conditions:
```
WebSearch queries:
1. "{peak_name} trip report site:cascadeclimbers.com"
2. "{peak_name} conditions site:peakbagger.com"
3. "{peak_name} recent climb 2025"
```

**Extract from results:**
- Report dates (most recent 5-10)
- Links to full reports
- Any conditions mentioned in snippets

**Optional WebFetch:**
- If specific high-value trip reports identified, fetch 1-2 for detailed conditions

#### 2D. Weather Forecast (Multiple Sources)

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

#### 2E. Avalanche Forecast (Python Script)

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

#### 2F. Daylight Calculations (Python Script)

```bash
cd skills/route-researcher/tools
uv run python calculate_daylight.py --date "{YYYY-MM-DD}" --coordinates "{lat},{lon}"
```

**Expected Output:** JSON with sunrise, sunset, daylight hours

**Error Handling:**
- Script not yet implemented: Use general guidance or note gap
- Script fails: Calculate approximate values or note gap
- No coordinates: Skip this step

#### 2G. Access and Permits (WebSearch)

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

**Structure:** Follow this template exactly:

```markdown
# {Peak Name} - Route Beta Research

> **⚠️ AI-Generated Research Document**
>
> This document was generated by an AI assistant and should be used as a **starting point only**.
>
> **YOU MUST:**
> - Verify all critical information from primary sources
> - Use your own judgment and experience to assess conditions and risk
> - Cross-reference with current trip reports and local conditions
> - Understand that conditions change rapidly in the mountains
>
> **This is NOT a substitute for:**
> - Proper training and experience
> - Current weather and avalanche forecasts
> - Your own research and route planning
> - Sound mountaineering judgment
>
> The mountains are inherently dangerous. You are responsible for your own safety.

**Generated:** {YYYY-MM-DD}
**Route Type:** {glacier/rock/scramble/hike}
**Difficulty:** {e.g., "Class 3 scramble" or "5.7 rock" or "Moderate glacier"}

## Summit Information
- **Elevation:** {elevation with units}
- **Prominence:** {prominence with units}
- **Location:** {state, range}
- **Coordinates:** {latitude}, {longitude} ([Google Maps]({google_maps_coordinates_link}) | [USGS Topo]({usgs_topo_link}))
- **PeakBagger:** [{peak name}]({peakbagger_url})

## Route Description

### Approach
{Trailhead information, access details}

### Standard Route
{Route description synthesized from multiple sources}

**Key Details:**
- **Distance:** {round trip distance}
- **Elevation Gain:** {total gain}
- **Estimated Time:** {typical completion time}

### Crux
{One paragraph describing the hardest/most technical section:
- What makes it challenging
- Where it's located on route
- Skills/gear required for this section}

### Hazards & Safety
{Synthesized from multiple sources:
- Known hazards (crevasses, rockfall, exposure)
- Seasonal considerations
- Bailout options
- Emergency contacts
- If trip reports mention unusual or important gear (e.g., "approach shoes recommended for talus" or "bring extra pickets"), include brief mention here}

## Current Conditions

### Daylight
{If available from script:}
- **Date:** {date}
- **Sunrise:** {time}
- **Sunset:** {time}
- **Daylight Hours:** {hours}
- **Considerations:** {alpine start recommendations, etc.}

{If not available:}
- **Note:** Daylight calculations not available. Check sunrise/sunset times for your planned date.

### Weather Forecast

{Synthesize data from multiple sources when available:}

**Mountain-Forecast.com:** {6-day forecast summary with temps, precip, wind}

**NOAA/NWS Point Forecast:** {7-day forecast with detailed conditions}

**Key Takeaways:**
- {Synthesized weather patterns}
- {Notable conditions (storms, good weather windows, etc.)}
- {Freezing levels if available}

**Check Current Forecasts:**
- [Mountain-Forecast.com]({mountain_forecast_link})
- [NOAA Point Forecast]({noaa_link})
{If winter season:}
- [NWAC Mountain Weather](https://nwac.us/mountain-weather-forecast/)

{If partial data available:}
**Note:** {Specify which sources were unavailable and why}

{If no data available:}
**Weather data not available.** Check the links above for current conditions.

### Avalanche Forecast
{If applicable and available:}
{Current danger rating, problems, travel advice}

{If not applicable:}
- **Not applicable** for this route type/season.

{If applicable but not available:}
- **Avalanche forecast not available.** Check [NWAC.us](https://nwac.us) for current conditions.

## Recent Trip Reports
{List 5-10 most recent reports with dates and links:}
- **{Date}** - [{Source}]({url}) - {Brief note if available from snippet, including any unusual or important gear mentioned}

{If limited reports:}
- **Note:** Limited recent trip reports available. Consider posting your own after your climb!

## Access & Permits

### Trailhead
{Trailhead name and location}

**Directions:** [View on Google Maps]({google_maps_link})

### Permits & Regulations
{Required permits, fees, regulations}

{If not found:}
- **Note:** Permit information not confirmed. Check with local forest service or park service.

### Road Conditions
{Current access notes, seasonal closures}

## Information Gaps
{Explicit list of what data was not found or is uncertain:}
- {Example: "Limited trip reports available for winter season"}
- {Example: "Weather forecast unavailable - script not yet implemented"}
- {Example: "No GPS tracks found on PeakBagger"}
- {Example: "Route description sources conflicted on crux difficulty"}

## Data Sources
{List all sources consulted:}
- PeakBagger: {url}
- {Other source names and URLs}

---

**Research completed:** {timestamp}
**Skill:** route-researcher v1.0
```

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

### Current Status (as of 2025-10-20)

**Implemented:**
- PeakBagger search functionality
- Python tools directory structure
- Report generation in user's current working directory
- cloudscrape.py for Cloudflare-protected sites (PeakBagger, SummitPost, Mountaineers.org, Mountain-Forecast.com)
- Multi-source weather gathering (Mountain-Forecast.com, NOAA/NWS, NWAC)

**Pending Implementation:**
- `fetch_avalanche.py` - NWAC avalanche data (currently using WebSearch/WebFetch as fallback)
- `calculate_daylight.py` - Sunrise/sunset calculations

**When Python scripts are not yet implemented:**
- Note in "Information Gaps" section
- Provide manual check links
- Continue with available data
- Don't block report generation

### Design Change: WebSearch/WebFetch Instead of Scraping

**Original Design:** Use `peakbagger.py` to scrape PeakBagger pages directly

**Current Design:**
- Use **WebSearch** to find PeakBagger peak pages
- Use **WebFetch** to extract data from those pages
- Reserve Python scripts for **calculations only** (weather, avalanche, daylight)

**Rationale:**
- WebFetch is more reliable than custom scraping
- Reduces maintenance burden (no HTML parsing to maintain)
- Leverages Claude's built-in tools effectively
- Python scripts focus on computation, not scraping

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
- [ ] Peak validation works with single match
- [ ] Peak validation works with multiple matches
- [ ] Peak validation handles no matches gracefully
- [ ] WebFetch extracts PeakBagger data correctly
- [ ] Route description synthesis is comprehensive
- [ ] Trip reports are recent and relevant
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
1. WebSearch: "Mt Baker site:peakbagger.com peak"
2. Find: Mount Baker (10,786 ft) - North Cascades, WA
3. Confirm with user
4. Gather data from all sources
5. Generate report: 2025-10-20-mount-baker.md (in current directory)
6. Report completion
```

**Example 2: Ambiguous peak name**
```
User: "Research Sahale Peak"

Skill Actions:
1. WebSearch: "Sahale Peak site:peakbagger.com peak"
2. Find: Multiple results:
   - Sahale Peak (8,680 ft) - North Cascades, WA
   - Sahale Arm (7,600 ft) - North Cascades, WA
3. Present options to user with AskUserQuestion
4. User selects Sahale Peak
5. Continue with data gathering
```

**Example 3: Peak not found**
```
User: "Research Mailbox Peak"

Skill Actions:
1. WebSearch: "Mailbox Peak site:peakbagger.com peak"
2. No clear PeakBagger results
3. Try variation: "Mailbox Peak Washington"
4. Still no clear results
5. AskUserQuestion: "I couldn't find this peak on PeakBagger. Would you like to:
   - Provide a direct PeakBagger URL
   - Try a different peak name
   - Continue research with general web sources only"
```

---

**Skill Version:** 1.0
**Last Updated:** 2025-10-20
**Status:** Ready for execution (with Python scripts pending)
