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
- `--date` (optional): Date as YYYY-MM-DD (default: today)

**Output:**

Returns unified JSON with keys: `weather`, `air_quality`, `daylight`, `avalanche`, `peakbagger`, `gaps`.

**Data Sources:**

- Open-Meteo Weather API (7-day forecast, freezing levels)
- Open-Meteo Air Quality API (US AQI)
- astral library (sunrise, sunset, civil twilight)
- NWAC region detection by coordinates
- peakbagger-cli (ascent statistics and recent ascents)

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

The `cloudscrape.py` tool handles Cloudflare protection, but may occasionally fail:

- Skill automatically falls back to available sources
- Check "Information Gaps" section in generated reports
- Use manual verification links provided

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

- `fetch_conditions.py`: 2-5s without --peak-id; 30-120s with --peak-id (peakbagger-cli is slow)
- `cloudscrape.py`: 1-3s (HTTP with Cloudflare bypass)

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
- **rich** - Rich terminal output
- **astral** - Astronomy calculations (daylight)
- **cloudscraper** - Cloudflare bypass

Dev dependencies: pytest
