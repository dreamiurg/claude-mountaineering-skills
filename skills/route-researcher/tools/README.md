# Route Researcher Tools

Python CLI tools for gathering current conditions data for Pacific Northwest route research.

## Overview

These tools are invoked by the `route-researcher` skill to fetch real-time data that supplements web-scraped route information. Each tool outputs structured JSON to stdout for easy parsing.

**Design Philosophy:**
- Tools focus on **computation and API calls**, not web scraping
- All tools handle errors gracefully (exit 0 even on failure)
- JSON output includes helpful fallback info when data unavailable
- Timeout-friendly (30s default)

## Tools

### cloudscrape.py

Fetches HTML content from Cloudflare-protected websites using cloudscraper.

**Usage:**
```bash
uv run python cloudscrape.py "https://www.peakbagger.com/peak.aspx?pid=1798"
```

**Parameters:**
- `url` (required): URL to fetch
- `--timeout` (optional): Request timeout in seconds (default: 30)

**Output:**
Returns the full HTML content to stdout.

**Purpose:**
- Bypasses Cloudflare bot protection on PeakBagger and SummitPost
- Uses cloudscraper library which solves Cloudflare's JavaScript challenges
- No browser required - pure HTTP with smart request mimicking

**Behavior:**
- Creates scraper instance with Chrome browser profile
- Mimics macOS desktop Chrome browser
- Automatically solves Cloudflare challenges
- Returns raw HTML for parsing by the skill

**Dependencies:**
- cloudscraper (Cloudflare bypass)
- click (CLI)
- rich (console output)

**Use Cases:**
- Fetching PeakBagger peak pages
- Fetching SummitPost route descriptions
- Any Cloudflare-protected climbing/hiking resource

**Example:**
```bash
# Fetch Mount Pilchuck page from PeakBagger
uv run python cloudscrape.py "https://www.peakbagger.com/peak.aspx?pid=1798" | grep -i "elevation"
```

---

### fetch_weather.py

Fetches mountain weather forecasts from Mountain-Forecast.com.

**Usage:**
```bash
uv run python fetch_weather.py --peak-name "Mt Baker" --coordinates "48.7767,-121.8144"
```

**Parameters:**
- `--peak-name` (required): Peak name for forecast lookup
- `--coordinates` (required): Lat/lon as "lat,lon"

**Output:**
```json
{
  "source": "Mountain-Forecast.com",
  "url": "https://www.mountain-forecast.com/peaks/Mount-Baker",
  "forecast": ["Day 1 data", "Day 2 data"],
  "note": "Visit URL for detailed multi-day forecast with temperatures, wind, and precipitation"
}
```

**Behavior:**
- Attempts to parse Mountain-Forecast.com forecast tables
- Falls back to URL reference if parsing fails
- Never hard-fails - always returns useful JSON

**Dependencies:**
- httpx (HTTP client)
- beautifulsoup4 + lxml (HTML parsing)
- click (CLI)
- rich (console output)

**Testing:**
```bash
uv run pytest test_fetch_weather.py -v
```

---

### fetch_avalanche.py

Fetches avalanche forecasts from Northwest Avalanche Center (NWAC).

**Usage:**
```bash
uv run python fetch_avalanche.py --region "North Cascades"
```

**Parameters:**
- `--region` (required): NWAC forecast region name
- `--coordinates` (optional): Lat/lon for future enhancements

**Supported Regions:**
- North Cascades
- Mt Baker
- Snoqualmie Pass
- Stevens Pass
- Olympics
- Mt Hood
- East Slopes
- South Cascades

**Output:**
```json
{
  "source": "NWAC",
  "region": "North Cascades",
  "url": "https://nwac.us/avalanche-forecast/#north-cascades",
  "forecast": "Current avalanche forecast available at URL",
  "note": "NWAC provides detailed avalanche danger ratings by elevation (alpine, treeline, below treeline). Visit the URL for current conditions, weather, snowpack analysis, and recent avalanche activity."
}
```

**Behavior:**
- Maps common region names to NWAC URL slugs
- NWAC is a JavaScript-heavy SPA, so parsing is limited
- Provides URL for manual checking
- Includes helpful context about NWAC's elevation-based ratings

**Dependencies:**
- httpx (HTTP client)
- beautifulsoup4 + lxml (HTML parsing, though limited due to JS)
- click (CLI)
- rich (console output)

**Testing:**
```bash
uv run pytest test_fetch_avalanche.py -v
```

---

### calculate_daylight.py

Calculates sunrise, sunset, and daylight hours for trip planning.

**Usage:**
```bash
uv run python calculate_daylight.py --date "2025-10-20" --coordinates "48.7767,-121.8144"
```

**Parameters:**
- `--date` (required): Date as YYYY-MM-DD
- `--coordinates` (required): Lat/lon as "lat,lon"

**Output:**
```json
{
  "date": "2025-10-20",
  "coordinates": {
    "latitude": 48.7767,
    "longitude": -121.8144
  },
  "sunrise": "07:42",
  "sunset": "18:24",
  "daylight_hours": 10.7,
  "note": "Times in Pacific timezone"
}
```

**Behavior:**
- Uses astral library for astronomical calculations
- All times in Pacific timezone (America/Los_Angeles)
- High precision for trip planning (alpine starts, etc.)

**Dependencies:**
- astral (astronomy/solar calculations)
- click (CLI)
- rich (console output)

**Testing:**
```bash
uv run pytest test_calculate_daylight.py -v
```

---

### peakbagger.py (Deprecated)

Originally designed for scraping PeakBagger.com. **No longer used by the skill.**

**Why deprecated:**
- Skill now uses WebSearch/WebFetch for PeakBagger data
- More reliable than custom HTML parsing
- Reduces maintenance burden
- Python tools now focus on computation only

**Still in repository for:**
- Reference implementation
- Possible future use if WebFetch becomes unavailable
- Test case examples

**Commands** (if using directly):
- `search "peak name"` - Search for peaks
- `peak-info "url"` - Extract peak details
- `stats "url"` - Analyze gear from trip reports

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

## Development

### Adding a New Tool

1. Create `new_tool.py` with Click CLI:
```python
#!/usr/bin/env python3
import json
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

1. **Never hard-fail** - Exit 0 even on errors
2. **Always return JSON** - Structured output for parsing
3. **Include helpful context** - URLs, notes, suggestions
4. **Timeout gracefully** - 30s default, degrade if exceeded
5. **Log to stderr** - Use rich Console(stderr=True) for warnings

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
uv run python fetch_weather.py --peak-name "Mt Baker" --coordinates "48.7767,-121.8144"
```

The skill:
1. Parses JSON output from stdout
2. Handles errors gracefully (checks for "error" field)
3. Includes data in report or notes gap
4. Provides manual check links from tool output

## Performance

**Typical execution times:**
- `calculate_daylight.py`: <0.1s (pure computation)
- `fetch_weather.py`: 1-3s (HTTP + parsing)
- `fetch_avalanche.py`: 1-3s (HTTP + parsing)

**Timeouts:**
- Individual tools: 30s
- Total skill execution: 3-5 minutes target

## Troubleshooting

### Tool returns error JSON

Check:
1. Network connectivity
2. Service website availability (Mountain-Forecast, NWAC)
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

```toml
[project]
name = "route-researcher-tools"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1.0",       # CLI framework
    "httpx>=0.27.0",      # Modern HTTP client
    "beautifulsoup4>=4.12.0",  # HTML parsing
    "lxml>=5.0.0",        # Fast XML/HTML parser
    "pydantic>=2.0.0",    # Data validation (future use)
    "rich>=13.0.0",       # Rich terminal output
    "astral>=3.2",        # Astronomy calculations
]
```

All pinned to modern versions for security and features.
