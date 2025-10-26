---
description: Generate comprehensive route beta report for a North American mountain peak
---

# Beta - Full Route Research Pipeline

Generate a comprehensive route beta report combining peak information, route descriptions, current conditions, and trip reports.

**Usage:** `/beta <peak name>`

**Examples:**
- `/beta Mt Baker`
- `/beta Forbidden Peak`
- `/beta "Sahale Peak"`

**Expected Duration:** 4-8 minutes

**What this command does:**

1. **Validates the peak** on PeakBagger (may ask you to confirm)
2. **Gathers route descriptions** from multiple climbing websites
3. **Fetches current conditions** (weather, avalanche, daylight)
4. **Collects trip reports** from PeakBagger, WTA, Mountaineers
5. **Synthesizes everything** into a markdown report
6. **Saves report** in your current working directory

## Workflow

This command orchestrates multiple sub-agents in sequence:

### Step 1: Peak Validation (30-90 seconds)

Invoke **peak-finder** agent:
```
Task: Find and validate "{peak_name}" on PeakBagger, retrieve coordinates and elevation data.
```

**Input to agent:**
```json
{
  "peak_name": "{user_provided_peak_name}"
}
```

**Wait for agent completion.** You may need to interact with user to confirm peak selection.

**Output:** `peak_data` JSON (see `schemas/peak-data.json`)

### Step 2: Parallel Data Gathering (120-240 seconds)

Once peak data is obtained, invoke THREE agents in PARALLEL:

**Agent 1: conditions-gatherer**
```
Task: Gather weather forecast, air quality, avalanche conditions, and daylight data for this peak.
```

**Input:**
```json
{
  "peak_name": "{peak_data.name}",
  "coordinates": {peak_data.coordinates},
  "elevation": {peak_data.elevation},
  "location": {peak_data.location},
  "date": "{current_date_YYYY-MM-DD}"
}
```

**Agent 2: route-info-gatherer**
```
Task: Gather route descriptions from AllTrails, SummitPost, Mountaineers, Mountain Project, and WTA.
```

**Input:**
```json
{
  "peak_name": "{peak_data.name}",
  "coordinates": {peak_data.coordinates}
}
```

**Agent 3: trip-report-collector**
```
Task: Collect ascent statistics and fetch 10-15 representative trip reports.
```

**Input:**
```json
{
  "peak_id": "{peak_data.peak_id}",
  "peak_name": "{peak_data.name}",
  "coordinates": {peak_data.coordinates}
}
```

**Wait for ALL three agents to complete.**

**Outputs:**
- `conditions_data` JSON (see `schemas/conditions-data.json`)
- `route_data` JSON (see `schemas/route-data.json`)
- `trip_reports_data` JSON (see `schemas/trip-reports-data.json`)

### Step 3: Report Synthesis (60-120 seconds)

Invoke **report-generator** agent:
```
Task: Synthesize all gathered data and generate markdown route beta report following the template.
```

**Input:**
```json
{
  "peak_data": {peak_data},
  "conditions_data": {conditions_data},
  "route_data": {route_data},
  "trip_reports_data": {trip_reports_data}
}
```

**Wait for agent completion.**

**Output:** Markdown file created in user's current working directory

### Step 4: Completion

Report generator will notify user with:
- Success message
- File location
- Brief summary
- Next steps

## Error Handling

- **Peak not found:** peak-finder will ask user for alternate name or peak ID
- **Agent failures:** Continue with available data, document gaps in report
- **Partial data:** Report will include what was obtained plus "Information Gaps" section
- **No write permissions:** Report error, suggest alternate location

## User Experience

**Expected interaction:**
1. User runs: `/beta Mt Baker`
2. Agent asks: "Found: Mount Baker (10,781 ft, Washington). Is this correct?" [Yes/No]
3. User confirms: "Yes"
4. Agents run in background (progress updates optional)
5. User receives: "Route research complete for Mount Baker! Report saved to: /home/user/2025-10-26-mount-baker.md"

## Notes

- **Requires user interaction** for peak confirmation (cannot be fully automated)
- **Caching** will speed up repeated queries (once implemented in tools/cache.py)
- **Best for well-documented peaks** in North America (PeakBagger coverage)
- **Report quality depends on data availability** - gaps will be documented
- **Peak confirmation is critical** - prevents researching wrong mountain

## Implementation Guidance

When invoking sub-agents via Task tool:

1. **peak-finder:** Synchronous, sequential (MUST complete first)
2. **Data gathering trio:** Asynchronous, parallel (use single message with 3 Task calls)
3. **report-generator:** Synchronous, sequential (needs all inputs)

Example Task tool usage:
```
# Step 1 - Sequential
invoke Task with subagent_type="peak-finder", prompt="Find and validate Mt Baker..."

# Step 2 - Parallel (single message with 3 Task calls)
invoke Task with subagent_type="conditions-gatherer", prompt="Gather weather..."
invoke Task with subagent_type="route-info-gatherer", prompt="Gather routes..."
invoke Task with subagent_type="trip-report-collector", prompt="Collect reports..."

# Step 3 - Sequential
invoke Task with subagent_type="report-generator", prompt="Synthesize data..."
```
