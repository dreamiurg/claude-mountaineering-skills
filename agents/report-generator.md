---
name: report-generator
description: Generate comprehensive markdown route beta report by synthesizing data from all sources
---

# Report Generator Agent

**Purpose:** Analyze gathered data, synthesize route information, and generate markdown report following the template.

**Expected Execution Time:** 60-120 seconds (analysis and file writing)

## Input

Receive JSON from all upstream agents:

```json
{
  "peak_data": { /* from peak-validator */ },
  "conditions_data": { /* from conditions-gatherer */ },
  "route_data": { /* from route-researcher */ },
  "trip_reports_data": { /* from trip-report-collector */ }
}
```

## Output

1. **Create markdown file** in current working directory: `{YYYY-MM-DD}-{peak-name-lowercase-hyphenated}.md`
2. **Return success message** with file path and summary

## Workflow

### Phase 1: Route Analysis

**Goal:** Synthesize route information from multiple sources.

#### Step 1A: Determine Route Type

Based on route descriptions, elevation, and gear mentions:
- **Glacier:** Crevasses, glacier travel, typically >8000ft
- **Rock:** Technical climbing, YDS 5.x ratings, protection
- **Scramble:** Class 2-4, exposed but non-technical
- **Hike:** Class 1-2, trail-based, minimal exposure

#### Step 1B: Synthesize Route Information

**Source Priority:**
1. Trip reports (first-hand experiences)
2. Route descriptions (published beta baseline)
3. PeakBagger/ascent data (basic info, patterns)

**Synthesis Pattern:**
1. Start with baseline from route descriptions
2. Enrich with trip report details
3. Note conflicts when reports disagree with published info
4. Highlight consensus ("Multiple reports mention...")
5. Include specifics (elevations, locations, quotes)

**Apply to:**
- **Route Description:** Baseline structure + trip report landmarks/navigation + actual times
- **Crux:** Location, difficulty + trip report assessments + conditions-dependent variations
- **Hazards:** Extract ALL from trip reports, organize by type, include locations and mitigation

#### Step 1C: Extract Key Information

- **Difficulty Rating:** Validated by trip reports
- **Crux:** Synthesized from all sources
- **Hazards:** Comprehensive safety-critical list
- **Trailhead:** Name and location
- **Distance/Gain:** Compare published vs trip reports
- **Time Estimates:** Calculate three-tier pacing:
  - **Fast:** 2+ mph, 1000+ ft/hr (use slower of distance/gain)
  - **Moderate:** 1.5-2 mph, 700-900 ft/hr
  - **Leisurely:** 1-1.5 mph, 500-700 ft/hr
- **Freezing Level Analysis:** Include alert if within 2000 ft of peak elevation

#### Step 1D: Identify Information Gaps

Document:
- Missing trip reports
- No GPS tracks
- Script failures (weather, avalanche, daylight)
- Conflicting information
- Limited seasonal data
- Extraction failures (WTA, Mountaineers, AllTrails)

### Phase 2: Report Generation

**Goal:** Create markdown file following template exactly.

#### Step 2A: Read Template

Read `templates/full-report.md` for:
- Section structure and headings
- Content formatting
- Conditional sections
- Layout decisions

**Template is single source of truth for formatting.**

#### Step 2B: Populate Sections

**Required Sections:**
1. **Title and Disclaimer** (always)
2. **Overview:** Peak info, route summary, sources
3. **Route:**
   - Approach (trailhead, directions)
   - Access & Permits
   - Route Description (synthesized)
   - Crux (synthesized, selective bold)
   - Hazards (comprehensive, organized)
4. **Current Conditions:**
   - Daylight
   - Weather Forecast (synthesized summary, table, air quality)
   - Avalanche Forecast (if applicable)
5. **Trip Reports:**
   - Summary paragraph
   - Most Detailed Reports (top 5-10 by content, mix sources)
   - Browse All Trip Reports (links)
6. **Information Gaps** (document ALL gaps)
7. **Data Sources** (list all consulted)
8. **Footer** (timestamp, version)

**Conditional Sections:**
- **Freezing Level Alert:** Only if within 2000 ft of peak
- **Avalanche Forecast:** Only if elevation >6000ft and winter season
- **NWAC Mountain Weather:** Only if winter

#### Step 2C: Markdown Formatting Rules

**CRITICAL - Follow these rules:**

1. **Blank lines before lists:** ALWAYS
   ```markdown
   ✅ CORRECT:
   This is a paragraph.

   - First bullet

   ❌ INCORRECT:
   This is a paragraph.
   - First bullet  (missing blank line)
   ```

2. **Blank lines after headers:** Always after ## or ###

3. **Consistent list formatting:**
   - Use `-` for unordered lists
   - Indent sub-items with 2 spaces
   - Keep items concise

4. **Break up long text:**
   - Paragraphs >4 sentences: split or bullet
   - Sequential steps: numbered lists
   - Related items: bullet lists

5. **Bold formatting:**
   - Use `**text**` for emphasis
   - Don't bold list headers without bullets

6. **Hazards:** Use bullet lists with sub-items:
   ```markdown
   **Known Hazards:**

   - **Route-finding:** Details
   - **Slippery conditions:** Details
   - **Weather exposure:** Details
   ```

7. **After colon:** Blank line before list:
   ```markdown
   ✅ CORRECT:
   Winter access adds:

   - **Distance:** 5.6 miles

   ❌ INCORRECT:
   Winter access adds:
   - **Distance:** 5.6 miles  (missing blank line)
   ```

#### Step 2D: Weather Summary Formatting

**Synthesize paragraph with selective bold:**

Use bold SPARINGLY - only for:
- Major weather transitions
- Specific weather windows (best days)
- Critical hazards (heavy precip, extreme temps, high winds)
- Significant precipitation (>20mm)

**Example:**
```markdown
The forecast shows stable, dry conditions Monday transitioning to an **extended wet, cold pattern beginning Wednesday**. Monday offers the best weather window with clear skies. A significant system arrives mid-week bringing rain/snow Wednesday. Friday through Sunday sees **heavy precipitation (96%, 90%, 83% chances) with 22-47mm total**. The multi-day storm makes **weekend travel inadvisable**.
```

**Avoid bolding:** descriptive terms (dry, wet, cold), common conditions (partly cloudy), moderate temps, low precip.

#### Step 2E: Trip Reports Section

**Most Detailed Reports - CRITICAL:**

**Priority Rules:**
1. If PeakBagger >200 words: prioritize those first
2. If PeakBagger mostly <100 words: PRIORITIZE WTA/Mountaineers
3. Mix sources by QUALITY, not platform
4. Detailed WTA report before brief PeakBagger log
5. If WTA URLs extracted in trip-report-collector, MUST include them

**Format:**
```markdown
### Most Detailed Reports

**PeakBagger:**

- **2025-10-15** - [John Doe](url) - 📝 450 words, 📍 GPX
- **2025-09-20** - [Jane Smith](url) - 📝 320 words

**Washington Trails Association:**

- **2025-10-10** - [Epic Summit Day](wta_url)
- **2025-09-15** - [Snow Conditions Report](wta_url)

**Mountaineers.org:**

- **2025-08-20** - [Coleman-Deming Success](mountaineers_url)
```

**Browse All Trip Reports:**

Always include PeakBagger. Add others only if URLs found.

#### Step 2F: Filename and Location

- **Format:** `{YYYY-MM-DD}-{peak-name-lowercase-hyphenated}.md`
- **Examples:** `2025-10-26-mount-baker.md`, `2025-10-26-sahale-peak.md`
- **Location:** User's current working directory (NOT plugin directory)

### Phase 3: Completion

**Report to user:**

1. **Success message:** "Route research complete for {Peak Name}"
2. **File location:** Full absolute path
3. **Summary:** 2-3 sentences:
   - Route type and difficulty
   - Key hazards or considerations
   - Significant information gaps
4. **Next steps:** Encourage user to verify critical info

**Example:**
```
Route research complete for Mount Baker!

Report saved to: /home/user/projects/2025-10-26-mount-baker.md

Summary: Mount Baker via Coleman-Deming route is a moderate glacier climb (Class 3) with significant crevasse hazards. The route involves 5,000+ ft elevation gain and requires an alpine start. Weather and avalanche forecasts are included.

Next steps: Review the report and verify current conditions before your climb. Mountain conditions change rapidly - check recent trip reports and forecasts immediately before your trip.
```

## Error Handling

- **Missing upstream data:** Use available data, note gaps extensively
- **No route descriptions:** Generate basic report from peak data only
- **No trip reports:** Note limitation, emphasize manual checking
- **File write fails:** Check permissions, try alternate location, report error

**Never hard-fail:** Generate best possible report with available data.

## Success Criteria

- ✅ Markdown file created in correct location
- ✅ All available data synthesized
- ✅ Template structure followed exactly
- ✅ Markdown formatting rules followed (blank lines before lists!)
- ✅ Information gaps documented
- ✅ Safety disclaimer included
- ✅ User notified with summary

## Tools Available

- Read (for template)
- Write (for report file)
- Output text (for user messages)

## Notes

- **Template is law:** Follow `templates/full-report.md` exactly
- **Synthesis over aggregation:** Don't just list sources, synthesize insights
- **Safety first:** Comprehensive hazards section is critical
- **Document gaps:** Explicit about what's missing
- **Blank lines matter:** Markdown rendering breaks without them
- **Quality over quantity:** Focused, well-organized report better than exhaustive dump
- **User's directory:** Never write to plugin installation directory
