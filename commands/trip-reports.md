---
name: trip-reports
description: Fetch and summarize recent trip reports for a mountain peak from PeakBagger and WTA
---

# Trip Report Fetcher

Find and summarize recent trip reports for a mountain peak. Searches PeakBagger and Washington Trails Association for first-hand trip reports with route conditions, gear notes, and key observations.

If the user provided a peak name as an argument (e.g., `/mountaineering:trip-reports Mt Si`), use that as the target peak. Otherwise, ask which peak to look up.

## Phase 1: Peak Identification

1. **Search PeakBagger** for the peak:

   ```bash
   uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger peak search "{peak_name}" --format json
   ```

2. **Handle results:**

   - **Multiple matches:** Use AskUserQuestion to present options. For each: "[Name] ([Elevation], [Location]) - [PeakBagger URL]". Include "Other" option.
   - **Single match:** Confirm with user: "Found: [Name] ([Elevation], [Location]) - [URL]. Is this correct?"
   - **No matches:** Try variations (Mt/Mount, word order reversal, remove titles). If still nothing, ask user for clarification.

3. **Extract peak_id** from the selected result.

## Phase 2: Peak Details

Fetch peak coordinates and basic info:

```bash
uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger peak show {peak_id} --format json
```

Extract: `peak_name`, `elevation_ft`, `location`, `latitude`, `longitude`.

## Phase 3: Fetch Trip Reports

Run these two sources **in parallel**:

### Source A: PeakBagger Trip Reports

1. Get recent ascents with trip reports:

   ```bash
   uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger peak ascents {peak_id} --with-tr --within 2y --limit 20 --format json
   ```

2. For the **10 most recent** ascents that have trip reports (word_count > 0), fetch full content:

   ```bash
   uvx --from git+https://github.com/dreamiurg/peakbagger-cli.git@v1.7.0 peakbagger ascent show {ascent_id} --format json
   ```

3. From each report extract: date, author, route taken, conditions described, gear mentioned, hazards noted, key observations.

### Source B: WTA Trip Reports

1. Search for the WTA hike page:

   ```
   WebSearch: "{peak_name} site:wta.org"
   ```

2. If a WTA hike page is found, fetch trip reports from the AJAX endpoint:

   ```
   WebFetch: {wta_hike_url}/@@related_tripreport_listing
   ```

3. For up to **5 recent trip reports**, fetch full content. If WebFetch fails, use cloudscrape:

   ```bash
   cd ${CLAUDE_PLUGIN_ROOT}/skills/route-researcher/tools && uv run python cloudscrape.py "{trip_report_url}"
   ```

4. Extract the same fields: date, author, route, conditions, hazards, key observations.

### Handling Failures

- If PeakBagger has no trip reports: Note this and rely on WTA.
- If WTA has no page for this peak: Note this and rely on PeakBagger.
- If both fail: Inform user that no trip reports were found on either source. Suggest checking SummitPost or Mountaineers.org manually.

## Phase 4: Present Results

Format trip reports for the user:

1. **Peak header:** Name, elevation, location
2. **Report summary:** "Found X trip reports from Y sources covering [date range]"
3. **Reports by date** (most recent first). For each report:
   - **Date** | **Author** | **Source** (PeakBagger/WTA)
   - **Route:** Which route was taken
   - **Conditions:** Snow, ice, trail conditions, weather experienced
   - **Key takeaways:** 1-2 sentence summary of the most useful info
   - **Link:** URL to the full report
4. **Consensus patterns:** If 3+ reports exist, highlight common themes:
   - Route conditions that multiple reports agree on
   - Recurring hazards or challenges
   - Gear recommendations that appear across reports
5. **Gaps:** Note if one source had no data, or if reports are all old (>6 months)
