---
name: route-researcher
description: Research North American mountain peaks and generate comprehensive route beta reports
---

# Route Researcher (New Architecture)

> **⚠️ Architecture Change Notice**
>
> The route-researcher skill has been restructured into a microservices-based design with specialized sub-agents and slash commands. The original monolithic workflow is preserved in `SKILL-legacy.md` for reference.

## New Architecture

This skill now uses **sub-agents** and **slash commands** for a modular, efficient workflow:

### Slash Commands

**Available to all users:**

- **`/beta <peak name>`** - Full route research pipeline (4-8 minutes)
  - Validates peak on PeakBagger
  - Scrapes route descriptions from multiple sites
  - Fetches current conditions (weather, avalanche, daylight)
  - Collects 10-15 trip reports
  - Generates comprehensive markdown report

- **`/conditions <peak name>`** - Quick conditions check (1-2 minutes)
  - Weather forecast (7-day)
  - Air quality
  - Avalanche conditions (if applicable)
  - Daylight calculations
  - No route research or trip reports (faster)

### Sub-Agents

**Invoked automatically by slash commands:**

1. **peak-finder** - Find and validate peak on PeakBagger
2. **conditions-gatherer** - Fetch weather, avalanche, daylight data
3. **route-info-gatherer** - Gather route descriptions from multiple websites
4. **trip-report-collector** - Gather ascent stats and trip reports
5. **report-generator** - Generate markdown report from synthesized data

## Usage

### Quick Start

```bash
# Full route research
/beta "Mt Baker"

# Quick conditions check
/conditions "Forbidden Peak"
```

### Traditional Skill Invocation

You can still use natural language (the skill automatically maps to `/beta`):

```bash
"Research Mt Baker"
"Get route beta for Forbidden Peak"
"I'm planning to climb Sahale Peak, can you research the route?"
```

## How It Works

### `/beta` Command Workflow

1. **Peak Validation** (30-90s)
   - Searches PeakBagger for peak
   - Confirms with user (may present multiple options)
   - Retrieves coordinates, elevation, location data

2. **Parallel Data Gathering** (120-240s)
   - **Conditions:** Weather forecast, air quality, avalanche, daylight
   - **Routes:** Scrape AllTrails, SummitPost, Mountaineers, WTA
   - **Trip Reports:** Collect 10-15 reports from PeakBagger, WTA, Mountaineers

3. **Report Synthesis** (60-120s)
   - Analyze and synthesize all data
   - Generate markdown report following template
   - Save to current working directory

### `/conditions` Command Workflow

1. **Peak Validation** (30-90s)
2. **Conditions Gathering** (60-120s)
3. **Quick Summary** or streamlined report

**Total:** ~2 minutes vs ~8 minutes for full `/beta`

## Features

### New in Microservices Architecture

- ✅ **Isolated sub-agents** - Each agent has focused responsibility
- ✅ **Parallel execution** - Data gathering runs concurrently (faster)
- ✅ **Caching** - Weather and avalanche data cached (6hr TTL)
- ✅ **Graceful degradation** - Missing data doesn't block pipeline
- ✅ **Independent testing** - Each agent can be invoked separately
- ✅ **Clear data contracts** - JSON schemas define interfaces

### Preserved Features

- ✅ **Multi-source data gathering** from specialized websites
- ✅ **Safety-first approach** with disclaimers and gap documentation
- ✅ **Trip report synthesis** from multiple platforms
- ✅ **Current conditions** (weather, avalanche, daylight)
- ✅ **Comprehensive route analysis** (approach, crux, hazards)

## Data Sources

Same as original architecture:
- **PeakBagger** - Peak info, coordinates, ascent stats
- **SummitPost** - Route descriptions
- **AllTrails** - Trail information, reviews
- **WTA** - Trip reports, trail conditions
- **The Mountaineers** - Route guides
- **Open-Meteo** - Weather and air quality forecasts
- **NOAA/NWS** - Official weather forecasts and alerts
- **NWAC** - Avalanche forecasts (when applicable)
- **Sunrise-Sunset.org** - Daylight calculations

## Directory Structure

```
mountaineering-skills/                    ← Plugin root
├── .claude-plugin/                       ← Plugin metadata
├── agents/                               ← Sub-agents (at plugin root)
│   ├── peak-finder.md
│   ├── conditions-gatherer.md
│   ├── route-info-gatherer.md
│   ├── trip-report-collector.md
│   └── report-generator.md
├── commands/                             ← Slash commands (at plugin root)
│   ├── beta.md
│   └── conditions.md
└── skills/route-researcher/              ← Skill resources
    ├── SKILL.md                          ← This file
    ├── SKILL-legacy.md                   ← Original monolithic workflow
    ├── templates/
    │   ├── full-report.md                ← Report template
    │   └── conditions-only.md            ← Conditions template
    ├── schemas/
    │   ├── peak-data.json                ← Peak finder output
    │   ├── conditions-data.json          ← Conditions gatherer output
    │   ├── route-data.json               ← Route info gatherer output
    │   └── trip-reports-data.json        ← Trip report collector output
    ├── tools/
    │   ├── cache.py                      ← NEW: File-based caching
    │   ├── cloudscrape.py                ← Cloudflare bypass
    │   ├── fetch_weather.py              ← Updated with caching
    │   ├── fetch_avalanche.py            ← Updated with caching
    │   └── calculate_daylight.py         ← Daylight calculations
    ├── assets/
    │   └── report-template.md            ← Original template (reference)
    └── examples/
        └── *.md                          ← Sample reports
```

## Caching

**New feature:** Python tools now use file-based caching to improve performance:

- **Weather data:** 6 hour TTL (`.cache/`)
- **Avalanche data:** 6 hour TTL
- **Trip reports:** 24 hour TTL (planned)
- **Route descriptions:** 7 day TTL (planned)

**Benefits:**
- Faster repeated queries for same peak
- Reduced API calls
- Better offline capability

**Clear cache:**
```bash
cd skills/route-researcher/tools
rm -rf .cache/
```

## Migration Notes

### For Users

- **No breaking changes** - Natural language invocations still work
- **New slash commands** - Faster, more explicit workflows
- **Same report quality** - Templates and synthesis unchanged
- **Improved performance** - Parallel execution + caching

### For Developers

- **Modular agents** - Easy to test and modify independently
- **Clear contracts** - JSON schemas define agent I/O
- **Legacy preserved** - SKILL-legacy.md available for reference
- **Python tools unchanged** - Only added caching layer

## Known Limitations

Same as original:
- **Best for well-documented peaks** in North America
- **Data quality depends on sources** - gaps are documented
- **Cloudflare challenges** - Some sites may block access
- **Trip report extraction** - Limited for AllTrails/Mountaineers (JS-heavy)

## Troubleshooting

### Agents not found
If slash commands fail with "agent not found":
- Ensure `.claude-plugin/plugin.json` is correctly configured
- Verify `agents/` and `commands/` are at plugin root
- Restart Claude Code

### Caching issues
If data seems stale:
```bash
# Skip cache for fresh data
cd skills/route-researcher/tools
uv run python fetch_weather.py --peak-name "Mt Baker" --coordinates "48.7768,-121.8144" --skip-cache
```

### Python tools failing
```bash
cd skills/route-researcher/tools
uv sync --reinstall
```

## Future Enhancements

Planned improvements:
- Gear advisor agent (`/packlist` command)
- Extended caching for trip reports and routes
- Browser automation for AllTrails/Mountaineers extraction
- Regional expansion beyond North America

## Contributing

This is part of the [claude-mountaineering-skills](https://github.com/dreamiurg/claude-mountaineering-skills) repository.

See [SKILL-legacy.md](./SKILL-legacy.md) for the original monolithic workflow documentation.
