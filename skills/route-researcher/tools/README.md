# Route Researcher Tools

Python CLI tools for gathering current conditions data for North American mountain route research.

## Overview

These tools are invoked by the `route-researcher` skill to fetch real-time data that supplements web-scraped route information. Each tool outputs structured JSON to stdout for easy parsing.

**Design Philosophy:**

- Tools focus on **computation and API calls**, not web scraping
- All tools handle API/network errors gracefully (exit 0 with JSON error output)
- JSON output includes helpful fallback info when data unavailable
- Timeout-friendly (30s default)

## Tools

### cloudscrape.py

Fetches HTML content from websites, with optional JS-rendering for Cloudflare-protected or JavaScript-heavy pages.

**Usage:**

```bash
# Default: fast httpx fetch (browser-like headers, no browser)
uv run python cloudscrape.py "https://www.peakbagger.com/peak.aspx?pid=1798"

# --render: Patchright headless browser for JS-rendered / Cloudflare-challenged pages
uv run python cloudscrape.py --render "https://www.hikeoftheweek.com/some-hike"
```

**Parameters:**

- `url` (required): URL to fetch
- `--render` (optional): Use Patchright stealth browser for JS-rendered or Cloudflare-protected pages
- `--timeout` (optional): Request timeout in seconds (default: 30)

**Output:**
Returns the full HTML content to stdout. On failure, exits 0 with a JSON error note to stdout so callers always succeed.

**Purpose:**

- Default path: plain httpx with browser-like headers (no browser required, no TLS spoofing)
- `--render` path: stealth headless Chromium via Patchright for pages that block plain HTTP or require JavaScript execution

**Behavior:**

- Default: plain httpx with browser-like headers; fast, no external install, no TLS spoofing
- `--render`: launches Patchright (undetected Playwright); Chromium is installed lazily on first use via `patchright install chromium` — base install stays light
- Any failure exits 0 (graceful degradation); error details go to stdout as JSON

**Dependencies:**

- httpx (default fetch path)
- patchright (stealth headless browser, `--render` path)
- click (CLI)

**Use Cases:**

- Fetching PeakBagger, SummitPost, WTA pages (default path usually sufficient)
- hikeoftheweek.com and other Cloudflare-challenged sites (require `--render`)
- Any site that serves content via JavaScript (require `--render`)

**Example:**

```bash
# Standard fetch — fast, no browser
uv run python cloudscrape.py "https://www.peakbagger.com/peak.aspx?pid=1798" | grep -i "elevation"

# JS-rendered / Cloudflare page
uv run python cloudscrape.py --render "https://www.hikeoftheweek.com/mount-baker"
```

---

### fetch_conditions.py

Unified conditions fetcher — weather, air quality, daylight, avalanche region, and PeakBagger statistics.

**Usage:**

```bash
uv run python fetch_conditions.py \
  --coordinates "48.7767,-121.8144" \
  --elevation 3286 \
  --peak-name "Mt Baker" \
  --peak-id 1798
```

**Parameters:**

- `--coordinates` (required): Lat/lon as "lat,lon"
- `--elevation` (required): Elevation in meters
- `--peak-name` (required): Peak name
- `--peak-id` (optional): PeakBagger peak ID for stats/ascents
- `--trailhead` (optional): Trailhead coordinates as "lat,lon" — enables multi-county path sampling (trailhead→summit); hospital/ranger lookups always run from the summit regardless
- `--date` (optional): Date as YYYY-MM-DD (default: today)
- `--distance-mi` (optional): Round-trip distance in miles — required for `time_estimates` and `itinerary`
- `--gain-ft` (optional): Total elevation gain in feet — required for `time_estimates` and `itinerary`
- `--start-time` (optional): Trip start time as HH:MM — requires `--distance-mi` and `--gain-ft`; adds `itinerary` key
- `--waypoint` (optional, repeatable): Waypoint as "lat,lon" — provide 2+ to add `bearings` key

**Output:**

Returns unified JSON. Always-present keys: `weather`, `air_quality`, `daylight`, `avalanche`, `peakbagger` (when `--peak-id` given), `counties`, `nearest_hospital`, `ranger_station`, `campgrounds`, `gaps`.

Conditional keys (only emitted when inputs are provided):
- `time_estimates` — roped/unroped + 3-tier pacing (requires `--distance-mi` + `--gain-ft`)
- `itinerary` — start/summit-ETA/turnaround-by/return-ETA, `after_dark` bool, `dusk_cutoff` (requires `--start-time` + `--distance-mi` + `--gain-ft`)
- `bearings` — per-segment spherical azimuth and distance (requires 2+ `--waypoint` args)

**Data Sources:**

- Open-Meteo Weather API (7-day forecast, freezing levels, per-day `snow_line_note`/`near_summit`)
- Open-Meteo Air Quality API (US AQI)
- astral library (full 8-key twilight table; null on white-night dates)
- NWAC region detection by coordinates
- peakbagger-cli (ascent statistics and recent ascents)
- FCC Area API (counties trailhead→summit)
- OSM Overpass (nearest hospital/ER, ranger station, campgrounds within ~12 mi)
- USFS ArcGIS EDW (admin district when on NF land)

**Testing:**

```bash
RUN_INTEGRATION_TESTS=1 uv run pytest test_fetch_conditions.py -v
```

---

## Installation

All tools are managed via `uv` with dependencies in `pyproject.toml`.

**Setup:**

```bash
cd skills/route-researcher/tools
uv sync
```

This creates a virtual environment and installs all dependencies.

**Python Version:**
Python 3.11+ (specified in `.python-version`)

### Common Issues

**Dependencies not installing**

1. Check if `uv` is installed: `uv --version`
2. Try `uv sync --reinstall` in the tools directory
3. The skill will still work, just without some Python tools

**Cloudflare Blocking Requests**

The `cloudscrape.py` tool handles Cloudflare and JS-rendered pages. If the default path fails:

- Retry with `--render` flag to use Patchright stealth browser
- First `--render` use installs Chromium lazily (`patchright install chromium`) — subsequent calls are fast
- If both paths fail, the skill notes it in "Information Gaps" and continues
- Use manual verification links provided in the report

**No Route Beta Generated**

Ensure you're in a directory where you have write permissions. Reports are created in your current working directory, not in the plugin installation directory.

## Development

### Adding a New Tool

1. Create `new_tool.py` with Click CLI:

```python
#!/usr/bin/env python3
import json
import sys
import click

@click.command()
@click.option('--param', required=True)
def cli(param: str):
    """Tool description"""
    try:
        # Tool logic here
        output = {"result": "data"}
        click.echo(json.dumps(output, indent=2))
    except Exception as e:
        # Graceful error handling
        output = {"error": str(e), "note": "Fallback message"}
        click.echo(json.dumps(output, indent=2))
        sys.exit(0)  # Don't hard-fail

if __name__ == '__main__':
    cli()
```

2. Create `test_new_tool.py`:

```python
from click.testing import CliRunner
from new_tool import cli

def test_basic_functionality():
    runner = CliRunner()
    result = runner.invoke(cli, ['--param', 'value'])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert 'result' in data
```

3. Add dependencies to `pyproject.toml` if needed

4. Test: `uv run pytest test_new_tool.py -v`

### Error Handling Guidelines

All tools follow these principles:

1. **Never hard-fail on API errors** - Exit 0 on network/API failures; exit 1 only on invalid arguments
2. **Always return JSON** - Structured output for parsing
3. **Include helpful context** - URLs, notes, suggestions
4. **Timeout gracefully** - 30s default, degrade if exceeded
5. **Log to stderr** - Use `click.echo(..., err=True)` or `rich.Console(stderr=True)` for warnings

Example error output:

```json
{
  "source": "Service Name",
  "error": "Connection timeout",
  "note": "Check service.com manually for current data",
  "url": "https://service.com/relevant-page"
}
```

This ensures the skill can continue even if individual tools fail.

### Testing Best Practices

- Test with real coordinates when possible
- Mock HTTP requests for reliability
- Test both success and failure paths
- Verify JSON structure and required fields
- Check graceful error handling

### Running All Tests

```bash
cd skills/route-researcher/tools
uv run pytest -v
```

Expected output: All tests passing

## Integration with Skill

Tools are invoked by the skill via Bash commands:

```bash
cd skills/route-researcher/tools
uv run python fetch_conditions.py --coordinates "48.7767,-121.8144" --elevation 3286 --peak-name "Mt Baker"
```

The skill:

1. Parses JSON output from stdout
2. Handles errors gracefully (checks for "error" field)
3. Includes data in report or notes gap
4. Provides manual check links from tool output

## Performance

**Typical execution times:**

- `fetch_conditions.py`: 5-15s without --peak-id (includes OSM/FCC geodata calls); 30-120s with --peak-id (peakbagger-cli is slow)
- `cloudscrape.py`: 1-3s default httpx; 10-30s first `--render` (Chromium install), 3-8s subsequent `--render`

**Timeouts:**

- Individual tools: 30s
- Total skill execution: 3-5 minutes target

## Troubleshooting

### Tool returns error JSON

Check:

1. Network connectivity
2. Service website availability (Open-Meteo, NWAC)
3. Coordinate format (must be "lat,lon" with comma, no spaces)
4. Date format (must be YYYY-MM-DD)

### Dependencies not found

```bash
cd skills/route-researcher/tools
uv sync --reinstall
```

### Tests failing

Check Python version:

```bash
python --version  # Should be 3.11+
```

Reinstall dependencies:

```bash
uv sync
uv run pytest -v
```

## Future Enhancements

Potential tool additions:

- `fetch_road_conditions.py` - WSDOT or forest service road status
- `fetch_permit_info.py` - Recreation.gov availability
- `aggregate_gps_tracks.py` - Combine tracks from multiple sources
- `analyze_historical_conditions.py` - Seasonal patterns from trip reports
- `fetch_noaa_forecast.py` - Alternative weather source

## Contributing

These tools are part of a personal experimental skill. Code is provided as-is for reference.

## Dependencies

Managed in `pyproject.toml`:

- **click** - CLI framework
- **httpx** - Modern HTTP client
- **astral** - Astronomy calculations (daylight)
- **patchright** - Stealth headless browser (`--render` path in cloudscrape.py)

Dev dependencies: pytest
