---
description: Quick conditions check - weather, avalanche, and daylight for a peak (no route research)
---

# Conditions - Quick Weather and Conditions Check

Get current weather forecast, air quality, avalanche conditions, and daylight information for a peak WITHOUT the full route research.

**Usage:** `/conditions <peak name>`

**Examples:**
- `/conditions Mt Baker`
- `/conditions Forbidden Peak`
- `/conditions "Sahale Peak"`

**Expected Duration:** 60-120 seconds

**What this command does:**

1. **Validates the peak** on PeakBagger (confirms coordinates/elevation)
2. **Fetches current conditions:**
   - 7-day weather forecast (Open-Meteo + NOAA)
   - Air quality forecast
   - Avalanche forecast (if applicable)
   - Daylight calculations (sunrise/sunset)
3. **Generates quick report** OR returns formatted summary

**Use this when:**
- You already know the route, just need current conditions
- Quick weather check before committing to a climb
- Comparing conditions across multiple peaks
- Following up on a previous beta report

## Workflow

This command uses two sub-agents:

### Step 1: Peak Validation (30-90 seconds)

Invoke **peak-validator** agent:
```
Task: Find and validate "{peak_name}" on PeakBagger, retrieve coordinates and elevation data.
```

**Input:**
```json
{
  "peak_name": "{user_provided_peak_name}"
}
```

**Wait for agent completion.** May ask user to confirm peak.

**Output:** `peak_data` JSON

### Step 2: Conditions Gathering (60-120 seconds)

Invoke **conditions-gatherer** agent:
```
Task: Gather weather forecast, air quality, avalanche conditions, and daylight data.
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

**Wait for agent completion.**

**Output:** `conditions_data` JSON

### Step 3: Present Results

**Option A - Quick Summary (Inline):**

Format conditions data as text response:

```
Mt Baker Conditions (Oct 26, 2025)

Weather (7-day forecast):
Mon Oct 26: ☀️ Clear, High 45°F, Low 32°F, 0% precip
Tue Oct 27: ⛅ Partly cloudy, High 48°F, Low 35°F, 20% precip
Wed Oct 28: 🌧️ Rain, High 42°F, Low 38°F, 80% precip, 15mm
Thu Oct 29: 🌧️❄️ Rain/snow mix, High 38°F, Low 30°F, 90% precip, 25mm
Fri Oct 30: ❄️ Snow, High 32°F, Low 28°F, 70% precip, 18mm
Sat Oct 31: 🌨️ Snow showers, High 34°F, Low 29°F, 50% precip
Sun Nov 1: ⛅ Partly cloudy, High 38°F, Low 31°F, 30% precip

Freezing Level Alert (Peak: 10,781 ft):
- Mon-Tue: 8,000+ ft (well above summit)
- Wed-Fri: 5,000-6,500 ft (BELOW summit - expect snow above 6,000 ft)

Air Quality: Good (AQI <50)

Avalanche: Check NWAC North Cascades region - https://nwac.us

Daylight (Oct 26): Sunrise 7:25 AM, Sunset 5:58 PM (10h 33m)
Civil twilight begins 6:52 AM (good for alpine starts)

Weather Links:
- Mountain-Forecast: {link}
- Open-Meteo: {link}
- NOAA: {link}

Summary: Best window Monday-Tuesday before storm arrives Wednesday. Weekend sees heavy precipitation and cold temps.
```

**Option B - Streamlined Report (File):**

Use **report-synthesizer** agent with `template: "conditions-only"`:

```
Task: Generate streamlined conditions report using templates/conditions-only.md
```

**Input:**
```json
{
  "peak_data": {peak_data},
  "conditions_data": {conditions_data},
  "template": "conditions-only"
}
```

Creates: `{YYYY-MM-DD}-{peak-name}-conditions.md`

## Error Handling

- **Peak not found:** Ask user for alternate name
- **Weather API fails:** Provide manual check links
- **Avalanche not applicable:** Skip that section
- **Partial data:** Present what's available + note gaps

## User Experience

**Expected interaction:**
1. User runs: `/conditions Mt Baker`
2. Agent asks: "Found: Mount Baker (10,781 ft, Washington). Is this correct?" [Yes/No]
3. User confirms: "Yes"
4. Agent returns formatted summary (inline or file)

**Total time:** ~2 minutes vs ~8 minutes for full `/beta`

## Comparison with /beta

| Feature | /conditions | /beta |
|---------|-------------|-------|
| Peak validation | ✅ | ✅ |
| Weather forecast | ✅ | ✅ |
| Avalanche conditions | ✅ | ✅ |
| Daylight calculations | ✅ | ✅ |
| Route descriptions | ❌ | ✅ |
| Trip reports | ❌ | ✅ |
| Full synthesis | ❌ | ✅ |
| **Duration** | **~2 min** | **~8 min** |

## Notes

- **Fast alternative to /beta** when you just need conditions
- **No route research** - skips web scraping of AllTrails, SummitPost, etc.
- **No trip report collection** - saves significant time
- **Same data sources** for weather (Open-Meteo, NOAA, NWAC)
- **Inline or file output** - choose based on user preference
- **Can cache results** for repeated queries (once caching implemented)

## Implementation Guidance

Simpler than /beta - only 2 sequential agents:

```
# Step 1 - Peak validation
invoke Task with subagent_type="peak-validator", prompt="Find and validate..."

# Step 2 - Conditions gathering
invoke Task with subagent_type="conditions-gatherer", prompt="Gather weather..."

# Step 3 - Format results
Either:
A) Format inline response from conditions_data
B) invoke Task with subagent_type="report-synthesizer", prompt="Generate conditions-only report..."
```

Recommend **Option A (inline)** for speed, **Option B (file)** if user wants to save.
