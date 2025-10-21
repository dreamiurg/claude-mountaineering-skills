# Route Researcher Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Claude Code skill that researches Pacific Northwest mountain peaks and generates comprehensive route beta reports with current conditions, gear statistics, and safety information.

**Architecture:** Skill orchestrates Python CLI tools (via Bash) to gather data from PeakBagger, weather services, and NWAC, then synthesizes everything into structured Markdown reports. Python tools use Click for CLI, httpx for HTTP, BeautifulSoup for parsing, and Pydantic for data validation.

**Tech Stack:** Python 3.11+, uv, Click, httpx, BeautifulSoup4, Pydantic, Claude Code SKILL.md

---

## Task 1: Create Directory Structure and Python Project Setup

**Files:**
- Create: `.worktrees/route-researcher/skills/route-researcher/SKILL.md`
- Create: `.worktrees/route-researcher/skills/route-researcher/tools/pyproject.toml`
- Create: `.worktrees/route-researcher/skills/route-researcher/tools/.python-version`
- Create: `.worktrees/route-researcher/route-beta/.gitkeep`

**Step 1: Create directory structure**

```bash
mkdir -p skills/route-researcher/tools
mkdir -p route-beta
```

**Step 2: Create Python version file**

Create `skills/route-researcher/tools/.python-version`:
```
3.11
```

**Step 3: Create pyproject.toml**

Create `skills/route-researcher/tools/pyproject.toml`:
```toml
[project]
name = "route-researcher-tools"
version = "0.1.0"
description = "Data gathering tools for Pacific Northwest route beta research"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1.0",
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    "pydantic>=2.0.0",
    "rich>=13.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 4: Create placeholder SKILL.md**

Create `skills/route-researcher/SKILL.md`:
```markdown
---
name: route-researcher
description: Research Pacific Northwest mountain peaks and generate comprehensive route beta reports
---

# Route Researcher

Skill implementation in progress.
```

**Step 5: Create route-beta directory placeholder**

```bash
touch route-beta/.gitkeep
```

**Step 6: Verify uv can sync the environment**

```bash
cd skills/route-researcher/tools
uv sync
```

Expected: Environment created successfully

**Step 7: Commit**

```bash
git add skills/ route-beta/
git commit -m "feat: initialize route-researcher skill structure and Python project"
```

---

## Task 2: Build PeakBagger CLI - Basic Structure and Search

**Files:**
- Create: `skills/route-researcher/tools/peakbagger.py`
- Create: `skills/route-researcher/tools/test_peakbagger.py`

**Step 1: Write failing test for peak search**

Create `skills/route-researcher/tools/test_peakbagger.py`:
```python
import json
from click.testing import CliRunner
from peakbagger import cli

def test_search_returns_results():
    """Test that search command returns structured results"""
    runner = CliRunner()
    result = runner.invoke(cli, ['search', 'Mt Baker'])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert 'peaks' in data
    assert len(data['peaks']) > 0
    assert 'name' in data['peaks'][0]
    assert 'url' in data['peaks'][0]
```

**Step 2: Run test to verify it fails**

```bash
cd skills/route-researcher/tools
uv run pytest test_peakbagger.py::test_search_returns_results -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'peakbagger'"

**Step 3: Create minimal peakbagger.py CLI structure**

Create `skills/route-researcher/tools/peakbagger.py`:
```python
#!/usr/bin/env python3
"""PeakBagger data scraper CLI"""

import json
import sys
import click
import httpx
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()

@click.group()
def cli():
    """PeakBagger data scraper for route research"""
    pass

@cli.command()
@click.argument('peak_name')
def search(peak_name: str):
    """Search for peaks by name"""
    try:
        # Search PeakBagger
        url = "https://www.peakbagger.com/search.aspx"
        params = {"tid": "S", "n": peak_name}

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()

        # Parse results
        soup = BeautifulSoup(response.text, 'lxml')
        peaks = []

        # Find peak results in search page
        # PeakBagger search results are in a table with class "gray"
        for row in soup.select('table.gray tr')[1:]:  # Skip header
            cells = row.find_all('td')
            if len(cells) >= 2:
                link = cells[0].find('a')
                if link:
                    peaks.append({
                        'name': link.text.strip(),
                        'url': 'https://www.peakbagger.com' + link['href'],
                        'elevation': cells[1].text.strip() if len(cells) > 1 else 'Unknown'
                    })

        output = {'peaks': peaks[:10]}  # Limit to top 10
        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        console.print(f"[red]Error searching PeakBagger: {e}[/red]", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    cli()
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest test_peakbagger.py::test_search_returns_results -v
```

Expected: PASS (or close - may need HTML structure adjustments based on actual PeakBagger HTML)

**Step 5: Manual test with real search**

```bash
uv run python peakbagger.py search "Mt Baker"
```

Expected: JSON output with peak results

**Step 6: Commit**

```bash
git add peakbagger.py test_peakbagger.py
git commit -m "feat: add PeakBagger search command with basic HTML parsing"
```

---

## Task 3: Add Peak Info Extraction

**Files:**
- Modify: `skills/route-researcher/tools/peakbagger.py`
- Modify: `skills/route-researcher/tools/test_peakbagger.py`

**Step 1: Write failing test for peak-info command**

Add to `test_peakbagger.py`:
```python
def test_peak_info_extracts_details():
    """Test that peak-info extracts elevation, prominence, coordinates"""
    runner = CliRunner()
    # Use a known peak URL
    result = runner.invoke(cli, ['peak-info', 'https://www.peakbagger.com/peak.aspx?pid=1859'])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert 'name' in data
    assert 'elevation' in data
    assert 'prominence' in data
    assert 'coordinates' in data
    assert 'latitude' in data['coordinates']
    assert 'longitude' in data['coordinates']
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest test_peakbagger.py::test_peak_info_extracts_details -v
```

Expected: FAIL with "Error: No such command 'peak-info'"

**Step 3: Implement peak-info command**

Add to `peakbagger.py`:
```python
@cli.command()
@click.argument('peak_url')
def peak_info(peak_url: str):
    """Extract detailed peak information from PeakBagger URL"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(peak_url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # Extract peak name from title or h1
        name = soup.find('h1')
        peak_name = name.text.strip() if name else 'Unknown'

        # Extract statistics from the page
        # PeakBagger stores peak stats in specific patterns
        info = {
            'name': peak_name,
            'url': peak_url,
            'elevation': None,
            'prominence': None,
            'coordinates': {'latitude': None, 'longitude': None}
        }

        # Find elevation (look for pattern like "Elevation: 10,781 ft")
        for text in soup.stripped_strings:
            if 'Elevation:' in text or 'elevation' in text.lower():
                # Extract number from text
                import re
                match = re.search(r'([\d,]+)\s*(?:ft|feet)', text)
                if match:
                    info['elevation'] = match.group(1).replace(',', '') + ' ft'

            if 'Prominence:' in text or 'prominence' in text.lower():
                import re
                match = re.search(r'([\d,]+)\s*(?:ft|feet)', text)
                if match:
                    info['prominence'] = match.group(1).replace(',', '') + ' ft'

        # Extract coordinates from meta tags or coordinate display
        lat_tag = soup.find('span', {'id': 'latitude'}) or soup.find(string=re.compile(r'\d+\.\d+°[NS]'))
        lon_tag = soup.find('span', {'id': 'longitude'}) or soup.find(string=re.compile(r'\d+\.\d+°[EW]'))

        if lat_tag:
            info['coordinates']['latitude'] = str(lat_tag.string if hasattr(lat_tag, 'string') else lat_tag).strip()
        if lon_tag:
            info['coordinates']['longitude'] = str(lon_tag.string if hasattr(lon_tag, 'string') else lon_tag).strip()

        click.echo(json.dumps(info, indent=2))

    except Exception as e:
        console.print(f"[red]Error fetching peak info: {e}[/red]", file=sys.stderr)
        sys.exit(1)
```

**Step 4: Run test**

```bash
uv run pytest test_peakbagger.py::test_peak_info_extracts_details -v
```

Expected: PASS (may need HTML parsing adjustments)

**Step 5: Manual verification**

```bash
uv run python peakbagger.py peak-info "https://www.peakbagger.com/peak.aspx?pid=1859"
```

Expected: JSON with Mt Baker details

**Step 6: Commit**

```bash
git add peakbagger.py test_peakbagger.py
git commit -m "feat: add peak-info command to extract elevation, prominence, coordinates"
```

---

## Task 4: Add Gear Statistics Extraction

**Files:**
- Modify: `skills/route-researcher/tools/peakbagger.py`
- Modify: `skills/route-researcher/tools/test_peakbagger.py`

**Step 1: Write failing test for stats command**

Add to `test_peakbagger.py`:
```python
def test_stats_analyzes_gear_from_reports():
    """Test that stats command analyzes gear usage across trip reports"""
    runner = CliRunner()
    result = runner.invoke(cli, ['stats', 'https://www.peakbagger.com/peak.aspx?pid=1859'])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert 'sample_size' in data
    assert 'date_range' in data
    assert 'gear_stats' in data
    assert 'confidence' in data
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest test_peakbagger.py::test_stats_analyzes_gear_from_reports -v
```

Expected: FAIL with "Error: No such command 'stats'"

**Step 3: Implement stats command**

Add to `peakbagger.py`:
```python
from collections import Counter
from datetime import datetime

@cli.command()
@click.argument('peak_url')
@click.option('--format', default='json', help='Output format')
def stats(peak_url: str, format: str):
    """Analyze gear statistics from trip reports"""
    try:
        # Get peak ID from URL
        import re
        match = re.search(r'pid=(\d+)', peak_url)
        if not match:
            raise ValueError("Invalid PeakBagger URL")

        peak_id = match.group(1)

        # Fetch trip reports page
        reports_url = f"https://www.peakbagger.com/climber/ascent.aspx?pid={peak_id}"

        with httpx.Client(timeout=30.0) as client:
            response = client.get(reports_url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # Parse trip reports
        reports = []
        gear_counter = Counter()
        dates = []

        # Find trip report table
        # PeakBagger shows reports in a table format
        for row in soup.select('table.gray tr')[1:]:  # Skip header
            cells = row.find_all('td')
            if len(cells) >= 3:
                # Extract date
                date_text = cells[0].text.strip()
                try:
                    date_obj = datetime.strptime(date_text, '%Y-%m-%d')
                    dates.append(date_obj)
                except:
                    pass

                # Extract gear mentions from trip report text
                report_text = ' '.join([cell.text.lower() for cell in cells])

                # Common gear keywords
                gear_keywords = {
                    'ice axe': ['ice axe', 'ice-axe', 'ice ax'],
                    'crampons': ['crampon', 'crampons'],
                    'rope': ['rope', 'roped'],
                    'helmet': ['helmet'],
                    'glacier gear': ['glacier', 'crevasse'],
                    'snowshoes': ['snowshoe', 'snowshoes'],
                    'ski': ['ski', 'skis', 'skiing'],
                }

                for gear, keywords in gear_keywords.items():
                    if any(kw in report_text for kw in keywords):
                        gear_counter[gear] += 1

                reports.append(report_text)

        # Calculate statistics
        total_reports = len(reports)
        confidence = 'high' if total_reports >= 50 else 'medium' if total_reports >= 15 else 'low'

        # Calculate date range
        date_range = {}
        if dates:
            date_range = {
                'start': min(dates).strftime('%Y-%m-%d'),
                'end': max(dates).strftime('%Y-%m-%d'),
                'years': (max(dates) - min(dates)).days / 365.25
            }

        # Calculate percentages
        gear_stats = {
            gear: {
                'count': count,
                'percentage': round((count / total_reports) * 100, 1)
            }
            for gear, count in gear_counter.most_common()
        }

        output = {
            'sample_size': total_reports,
            'date_range': date_range,
            'gear_stats': gear_stats,
            'confidence': confidence
        }

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        console.print(f"[red]Error analyzing gear stats: {e}[/red]", file=sys.stderr)
        sys.exit(1)
```

**Step 4: Run test**

```bash
uv run pytest test_peakbagger.py::test_stats_analyzes_gear_from_reports -v
```

Expected: PASS

**Step 5: Manual test**

```bash
uv run python peakbagger.py stats "https://www.peakbagger.com/peak.aspx?pid=1859"
```

Expected: JSON with gear statistics

**Step 6: Commit**

```bash
git add peakbagger.py test_peakbagger.py
git commit -m "feat: add stats command for gear usage analysis from trip reports"
```

---

## Task 5: Build Weather Fetcher Script

**Files:**
- Create: `skills/route-researcher/tools/fetch_weather.py`
- Create: `skills/route-researcher/tools/test_fetch_weather.py`

**Step 1: Write failing test**

Create `skills/route-researcher/tools/test_fetch_weather.py`:
```python
import json
from click.testing import CliRunner
from fetch_weather import cli

def test_fetch_weather_returns_forecast():
    """Test weather fetching returns structured forecast"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--peak-name', 'Mt Baker', '--coordinates', '48.7767,-121.8144'])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert 'forecast' in data
    assert 'source' in data
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest test_fetch_weather.py -v
```

Expected: FAIL

**Step 3: Implement fetch_weather.py**

Create `skills/route-researcher/tools/fetch_weather.py`:
```python
#!/usr/bin/env python3
"""Mountain weather forecast fetcher"""

import json
import sys
import click
import httpx
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()

@click.command()
@click.option('--peak-name', required=True, help='Peak name for weather lookup')
@click.option('--coordinates', required=True, help='Coordinates as lat,lon')
def cli(peak_name: str, coordinates: str):
    """Fetch mountain weather forecast"""
    try:
        lat, lon = coordinates.split(',')

        # Try Mountain-Forecast.com
        # Format: mountain-forecast.com/peaks/Peak-Name
        peak_slug = peak_name.lower().replace(' ', '-').replace('.', '')
        url = f"https://www.mountain-forecast.com/peaks/{peak_slug}"

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')

                # Extract forecast data
                # Mountain-Forecast has structured forecast tables
                forecast_days = []

                # This is simplified - actual implementation needs to parse their specific HTML
                for day_elem in soup.select('.forecast-table-days__cell')[:5]:
                    forecast_days.append(day_elem.text.strip())

                output = {
                    'source': 'Mountain-Forecast.com',
                    'url': url,
                    'forecast': forecast_days if forecast_days else ['Forecast data available at URL'],
                    'note': 'Visit URL for detailed multi-day forecast'
                }
            else:
                # Fallback message
                output = {
                    'source': 'Mountain-Forecast.com',
                    'url': url,
                    'forecast': [],
                    'note': f'Check {url} for weather forecast'
                }

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        console.print(f"[red]Error fetching weather: {e}[/red]", file=sys.stderr)
        output = {
            'source': 'Error',
            'forecast': [],
            'error': str(e),
            'note': 'Check Mountain-Forecast.com manually'
        }
        click.echo(json.dumps(output, indent=2))
        sys.exit(0)  # Don't fail hard on weather errors

if __name__ == '__main__':
    cli()
```

**Step 4: Run test**

```bash
uv run pytest test_fetch_weather.py -v
```

Expected: PASS

**Step 5: Manual test**

```bash
uv run python fetch_weather.py --peak-name "Mt Baker" --coordinates "48.7767,-121.8144"
```

**Step 6: Commit**

```bash
git add fetch_weather.py test_fetch_weather.py
git commit -m "feat: add weather forecast fetcher for mountain conditions"
```

---

## Task 6: Build Avalanche Forecast Fetcher

**Files:**
- Create: `skills/route-researcher/tools/fetch_avalanche.py`
- Create: `skills/route-researcher/tools/test_fetch_avalanche.py`

**Step 1: Write failing test**

Create `skills/route-researcher/tools/test_fetch_avalanche.py`:
```python
import json
from click.testing import CliRunner
from fetch_avalanche import cli

def test_fetch_avalanche_returns_nwac_data():
    """Test NWAC avalanche forecast fetching"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--region', 'North Cascades'])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert 'source' in data
    assert 'region' in data
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest test_fetch_avalanche.py -v
```

Expected: FAIL

**Step 3: Implement fetch_avalanche.py**

Create `skills/route-researcher/tools/fetch_avalanche.py`:
```python
#!/usr/bin/env python3
"""NWAC avalanche forecast fetcher"""

import json
import sys
import click
import httpx
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()

# NWAC region mapping
NWAC_REGIONS = {
    'north cascades': 'north-cascades',
    'mt baker': 'mt-baker',
    'snoqualmie pass': 'snoqualmie-pass',
    'stevens pass': 'stevens-pass',
    'olympics': 'olympics',
}

@click.command()
@click.option('--region', required=True, help='NWAC forecast region')
@click.option('--coordinates', help='Coordinates as lat,lon (optional)')
def cli(region: str, coordinates: str = None):
    """Fetch NWAC avalanche forecast"""
    try:
        # Normalize region name
        region_slug = NWAC_REGIONS.get(region.lower(), region.lower().replace(' ', '-'))

        url = f"https://nwac.us/avalanche-forecast/#{region_slug}"

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            # Try to fetch current forecast
            response = client.get(f"https://nwac.us/avalanche-forecast/")

            if response.status_code == 200:
                output = {
                    'source': 'NWAC',
                    'region': region,
                    'url': url,
                    'forecast': 'Check URL for current avalanche forecast',
                    'note': 'NWAC provides detailed avalanche danger ratings by elevation'
                }
            else:
                output = {
                    'source': 'NWAC',
                    'region': region,
                    'url': url,
                    'forecast': 'Unable to fetch forecast',
                    'note': 'Visit NWAC website for current conditions'
                }

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        console.print(f"[red]Error fetching avalanche forecast: {e}[/red]", file=sys.stderr)
        output = {
            'source': 'NWAC',
            'region': region,
            'url': 'https://nwac.us',
            'error': str(e),
            'note': 'Check NWAC website manually'
        }
        click.echo(json.dumps(output, indent=2))
        sys.exit(0)  # Don't fail hard

if __name__ == '__main__':
    cli()
```

**Step 4: Run test**

```bash
uv run pytest test_fetch_avalanche.py -v
```

Expected: PASS

**Step 5: Manual test**

```bash
uv run python fetch_avalanche.py --region "North Cascades"
```

**Step 6: Commit**

```bash
git add fetch_avalanche.py test_fetch_avalanche.py
git commit -m "feat: add NWAC avalanche forecast fetcher"
```

---

## Task 7: Build Daylight Calculator

**Files:**
- Create: `skills/route-researcher/tools/calculate_daylight.py`
- Create: `skills/route-researcher/tools/test_calculate_daylight.py`

**Step 1: Add astronomy dependency to pyproject.toml**

Modify `pyproject.toml` dependencies:
```toml
dependencies = [
    "click>=8.1.0",
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    "pydantic>=2.0.0",
    "rich>=13.0.0",
    "astral>=3.2",  # For sunrise/sunset calculations
]
```

Run: `uv sync`

**Step 2: Write failing test**

Create `skills/route-researcher/tools/test_calculate_daylight.py`:
```python
import json
from click.testing import CliRunner
from calculate_daylight import cli

def test_calculate_daylight_returns_times():
    """Test daylight calculation returns sunrise/sunset"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--date', '2025-10-20', '--coordinates', '48.7767,-121.8144'])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert 'sunrise' in data
    assert 'sunset' in data
    assert 'daylight_hours' in data
```

**Step 3: Run test to verify it fails**

```bash
uv run pytest test_calculate_daylight.py -v
```

Expected: FAIL

**Step 4: Implement calculate_daylight.py**

Create `skills/route-researcher/tools/calculate_daylight.py`:
```python
#!/usr/bin/env python3
"""Sunrise/sunset daylight calculator"""

import json
import sys
from datetime import datetime, date
import click
from astral import LocationInfo
from astral.sun import sun
from rich.console import Console

console = Console()

@click.command()
@click.option('--date', required=True, help='Date as YYYY-MM-DD')
@click.option('--coordinates', required=True, help='Coordinates as lat,lon')
def cli(date: str, coordinates: str):
    """Calculate sunrise, sunset, and daylight hours"""
    try:
        lat, lon = map(float, coordinates.split(','))
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        # Create location
        location = LocationInfo(latitude=lat, longitude=lon)

        # Calculate sun times
        s = sun(location.observer, date=date_obj, tzinfo='America/Los_Angeles')

        sunrise_time = s['sunrise']
        sunset_time = s['sunset']

        # Calculate daylight hours
        daylight = sunset_time - sunrise_time
        daylight_hours = daylight.total_seconds() / 3600

        output = {
            'date': date,
            'coordinates': {'latitude': lat, 'longitude': lon},
            'sunrise': sunrise_time.strftime('%H:%M'),
            'sunset': sunset_time.strftime('%H:%M'),
            'daylight_hours': round(daylight_hours, 2),
            'note': 'Times in Pacific timezone'
        }

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        console.print(f"[red]Error calculating daylight: {e}[/red]", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    cli()
```

**Step 5: Run test**

```bash
uv run pytest test_calculate_daylight.py -v
```

Expected: PASS

**Step 6: Manual test**

```bash
uv run python calculate_daylight.py --date "2025-10-20" --coordinates "48.7767,-121.8144"
```

**Step 7: Commit**

```bash
git add calculate_daylight.py test_calculate_daylight.py pyproject.toml
git commit -m "feat: add daylight calculator with sunrise/sunset times"
```

---

## Task 8: Implement Skill Orchestration Logic (Part 1 - Validation)

**Files:**
- Modify: `skills/route-researcher/SKILL.md`

**Step 1: Write skill header and description**

Modify `skills/route-researcher/SKILL.md`:
```markdown
---
name: route-researcher
description: Research Pacific Northwest mountain peaks and generate comprehensive route beta reports with current conditions, weather, gear statistics, and safety information
---

# Route Researcher

Research Pacific Northwest mountain peaks and generate comprehensive route beta reports.

## Overview

This skill orchestrates Python CLI tools to gather data from multiple sources:
- PeakBagger.com (peak info, trip reports, gear statistics)
- Mountain weather services
- NWAC avalanche forecasts
- Daylight calculations

Outputs structured Markdown reports to `route-beta/YYYY-MM-DD-peak-name.md`.

## Invocation

User requests research on a peak:
- "Research Mt Baker"
- "Get route beta for Sahale Peak"
- "Plan expedition to Forbidden Peak"

## Workflow

### Phase 1: Peak Validation

1. Extract peak name from user message
2. Search PeakBagger using tools
3. Validate with user before proceeding

**Implementation:**

```
When user requests route research:

1. Extract peak name from message
2. Run search: `uv run python skills/route-researcher/tools/peakbagger.py search "{peak_name}"`
3. Parse JSON results
4. If multiple matches:
   - Use AskUserQuestion tool to present options
   - Show: peak name, elevation, PeakBagger link
   - User selects correct peak
5. If single match:
   - Confirm with user: "I found {name} ({elevation}) on PeakBagger: {link}. Is this correct?"
   - Wait for confirmation
6. If no matches:
   - Ask user to verify peak name
   - Suggest checking PeakBagger.com directly
7. Once validated, proceed to Phase 2
```

**Error handling:**
- If PeakBagger search fails, report error and ask user for direct PeakBagger URL
- Timeout: 30 seconds for search

## Phase 2 Implementation (to be continued in next task)

[Placeholder for data gathering phase]
```

**Step 2: Commit**

```bash
git add skills/route-researcher/SKILL.md
git commit -m "feat: add skill validation workflow for peak selection"
```

---

## Task 9: Implement Skill Orchestration Logic (Part 2 - Data Gathering)

**Files:**
- Modify: `skills/route-researcher/SKILL.md`

**Step 1: Add data gathering phase to SKILL.md**

Add to `skills/route-researcher/SKILL.md` after Phase 1:

```markdown
### Phase 2: Data Gathering

Once peak is validated, gather data from all sources in parallel.

**Run these commands via Bash tool:**

1. **Peak information:**
   ```bash
   cd skills/route-researcher/tools && uv run python peakbagger.py peak-info "{peak_url}"
   ```

2. **Gear statistics:**
   ```bash
   cd skills/route-researcher/tools && uv run python peakbagger.py stats "{peak_url}"
   ```

3. **Weather forecast:**
   ```bash
   cd skills/route-researcher/tools && uv run python fetch_weather.py --peak-name "{peak_name}" --coordinates "{lat},{lon}"
   ```

4. **Avalanche forecast** (if applicable):
   ```bash
   cd skills/route-researcher/tools && uv run python fetch_avalanche.py --region "{region}"
   ```

5. **Daylight calculation:**
   ```bash
   cd skills/route-researcher/tools && uv run python calculate_daylight.py --date "{today}" --coordinates "{lat},{lon}"
   ```

**Qualitative sources via WebFetch/WebSearch:**

6. Search for recent trip reports:
   - WebSearch: "{peak_name} trip report cascadeclimbers"
   - WebSearch: "{peak_name} route conditions recent"

7. Fetch route descriptions:
   - WebFetch Summit Post peak page
   - WebFetch Mountain Project route page (if applicable)

8. Check access/permits:
   - WebSearch: "{peak_name} trailhead permit"
   - WebSearch: "{peak_name} road access conditions"

**Error handling:**
- If any script fails, note in "Information Gaps" section
- Don't block entire research on single failure
- Continue gathering other data
- Timeout: 30s per script, 5 minutes total

### Phase 3: Data Synthesis

[Placeholder for synthesis phase]
```

**Step 2: Commit**

```bash
git add skills/route-researcher/SKILL.md
git commit -m "feat: add data gathering orchestration to skill"
```

---

## Task 10: Implement Skill Orchestration Logic (Part 3 - Report Generation)

**Files:**
- Modify: `skills/route-researcher/SKILL.md`

**Step 1: Add synthesis and report generation to SKILL.md**

Add to `skills/route-researcher/SKILL.md` after Phase 2:

```markdown
### Phase 3: Data Synthesis & Report Generation

Analyze gathered data and generate structured Markdown report.

**Analysis steps:**

1. **Determine route type:**
   - Analyze route descriptions for keywords:
     - Glacier: mentions of "glacier", "crevasse", "bergschrund"
     - Rock: mentions of "pitch", "belay", "climbing", YDS ratings
     - Scramble: mentions of "scramble", "class 2/3/4"
     - Hike: mentions of "trail", "hiking", no technical language
   - Set route type based on primary activity

2. **Extract difficulty rating:**
   - Rock: YDS class (5.0-5.15) from route descriptions
   - Scramble: Class 1-4 from descriptions
   - Glacier: Difficulty descriptor (easy/moderate/difficult)
   - Hike: Trail difficulty if mentioned

3. **Identify crux section:**
   - Look for keywords: "crux", "hardest", "most difficult", "exposed"
   - Extract 1-2 sentence description of technical challenge
   - Note location on route

4. **Compile hazards:**
   - From descriptions: rockfall, exposure, avalanche, crevasses
   - From conditions: current hazards mentioned in trip reports
   - Synthesize into bullet list

5. **Extract trailhead info:**
   - Trailhead name from route descriptions
   - Create Google Maps link: `https://www.google.com/maps/search/?api=1&query={lat},{lon}`
   - Estimate drive time from Seattle (or major city)

6. **Calculate elevation gain:**
   - From route descriptions or calculate: summit_elevation - trailhead_elevation

7. **Compile recent reports:**
   - Extract 5-10 most recent trip report links
   - Note dates and key conditions mentioned

**Generate report:**

Use Write tool to create: `route-beta/{YYYY-MM-DD}-{peak-name-slug}.md`

Follow this exact structure:

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
**Difficulty:** {rating if applicable}

## Summit Information
- Elevation: {from PeakBagger}
- Prominence: {from PeakBagger}
- Location: {coordinates, region}
- PeakBagger: {link}

## Route Description
- **Trailhead:** {name and Google Maps link}
- **Drive Time:** {estimated from Seattle}
- **Elevation Gain:** {calculated}
- **Distance:** {from descriptions}
- **Estimated Time:** {from descriptions}

### Route Details
{Synthesized route description from Summit Post, Mountain Project, etc.}

### Crux
{One paragraph describing hardest section}

### Hazards & Safety
{Bullet list of hazards}
- {hazard 1}
- {hazard 2}
- **Bailout options:** {if mentioned}
- **Emergency contacts:** {if applicable}

### GPS Tracks
- View trip reports with GPS tracks: {PeakBagger link with filter}

## Current Conditions & Weather

### Daylight
- **Sunrise/Sunset:** {from calculate_daylight.py}
- **Available Daylight:** {hours}
- **Considerations:** {alpine start recommendation if relevant}

### Weather Forecast
{From fetch_weather.py}
- {forecast summary or link}

### Avalanche Forecast
{From fetch_avalanche.py - only if glacier/snow route}
- {forecast summary or link}

## Gear Statistics & Recommendations
{From peakbagger.py stats}
- **Sample size:** Based on {X} reports over {Y} years ({start}-{end})
- **Confidence:** {high/medium/low}

**Gear usage:**
{For each gear item with >20% usage:}
- {gear name}: {percentage}% of reports

{Seasonal trends if available}

## Recent Trip Reports
{From WebSearch results}
- [{date}] {title} - {link}
- [{date}] {title} - {link}
...

## Access & Permits
{From WebSearch results}
- {access information}
- {permit requirements}
- {road conditions if mentioned}

## Information Gaps
{List any sections where data was insufficient}
- Example: "No recent winter trip reports found"
- Example: "Weather forecast unavailable - check Mountain-Forecast.com"
```

**Step 2: Add completion message**

Add to end of SKILL.md:

```markdown
### Phase 4: Completion

Report file path and summary to user:

"Route beta report generated: `route-beta/{YYYY-MM-DD}-{peak-name}.md`

**Summary:**
- Route type: {type}
- Difficulty: {rating}
- Based on {N} trip reports
- Current conditions and weather included

**Key hazards:** {top 2-3 hazards}

Review the full report for detailed information. Remember to verify critical details and use your own judgment."
```

**Step 3: Commit**

```bash
git add skills/route-researcher/SKILL.md
git commit -m "feat: add report synthesis and generation logic to skill"
```

---

## Task 11: Test End-to-End Skill Execution

**Files:**
- Create: `skills/route-researcher/TEST_CASES.md`

**Step 1: Create test cases document**

Create `skills/route-researcher/TEST_CASES.md`:
```markdown
# Route Researcher Skill Test Cases

## Test Case 1: Mt Baker (Popular Peak, Abundant Data)

**Input:** "Research Mt Baker"

**Expected:**
- Multiple PeakBagger results found
- User validates correct peak
- Comprehensive data gathered (100+ trip reports)
- Route type: Glacier
- Difficulty: Moderate glacier climb
- High confidence gear statistics
- Weather and avalanche forecasts retrieved
- Report generated successfully

**Validation:**
- Report file created in route-beta/
- All major sections populated
- No critical information gaps
- Safety disclaimer present

## Test Case 2: Obscure Peak (Limited Data)

**Input:** "Research Vesper Peak"

**Expected:**
- Peak found on PeakBagger
- Limited trip reports (10-30)
- Route type determined (scramble)
- Medium/low confidence gear statistics
- Weather forecast available
- Some information gaps explicitly noted

**Validation:**
- Information gaps section lists what's missing
- Report still useful despite limited data
- Doesn't fail on missing information

## Test Case 3: Invalid Peak Name

**Input:** "Research Mt Nonexistent"

**Expected:**
- PeakBagger search returns no results
- Skill asks user to verify peak name
- Suggests checking PeakBagger manually
- Graceful exit without generating report

## Test Case 4: Ambiguous Peak Name

**Input:** "Research Baker Mountain"

**Expected:**
- Multiple matches (Mt Baker, Baker Mountain, etc.)
- AskUserQuestion presents options with elevations
- User selects correct peak
- Continues normally after selection
```

**Step 2: Manual test with Mt Baker**

From main session, invoke skill:
```
"Research Mt Baker for me"
```

Verify skill:
1. Searches PeakBagger
2. Validates peak with user
3. Runs all data gathering scripts
4. Generates report
5. Report is well-formatted and comprehensive

**Step 3: Document any issues found**

Add to TEST_CASES.md:
```markdown
## Test Results

### {Date} - Mt Baker Test
- Status: {Pass/Fail}
- Issues found: {list}
- Improvements needed: {list}
```

**Step 4: Commit**

```bash
git add skills/route-researcher/TEST_CASES.md
git commit -m "docs: add test cases for skill validation"
```

---

## Task 12: Final Documentation and README

**Files:**
- Create: `skills/route-researcher/README.md`
- Modify: `README.md` (root)

**Step 1: Create skill README**

Create `skills/route-researcher/README.md`:
```markdown
# Route Researcher Skill

Research Pacific Northwest mountain peaks and generate comprehensive route beta reports.

## Features

- **Peak validation** - Search PeakBagger and confirm correct peak
- **Comprehensive data gathering** - Peak info, gear stats, weather, avalanche conditions
- **Statistical analysis** - Gear usage trends from historical trip reports
- **Structured reports** - Markdown documents with all essential beta
- **Safety-focused** - Prominent disclaimers and explicit information gaps

## Usage

Invoke the skill with a peak name:

```
"Research Mt Baker"
"Get route beta for Sahale Peak"
```

The skill will:
1. Search PeakBagger for the peak
2. Validate with you (if multiple matches)
3. Gather data from multiple sources
4. Generate report in `route-beta/YYYY-MM-DD-peak-name.md`

## Output

Reports include:
- Summit information (elevation, prominence, coordinates)
- Route description with trailhead info and Google Maps link
- Route type and difficulty rating
- Crux section description
- Hazards and safety information
- Current weather and avalanche forecasts
- Daylight hours for planning
- Gear statistics from trip reports
- Recent trip report links
- Access and permit information

## Data Sources

- **PeakBagger.com** - Peak info, trip reports, gear statistics
- **Mountain-Forecast.com** - Weather forecasts
- **NWAC** - Avalanche conditions
- **Summit Post** - Route descriptions
- **Mountain Project** - Climbing route info
- **CascadeClimbers.com** - Recent trip reports
- **Mountaineers.org** - Historical reports

## Requirements

- Python 3.11+
- uv (for environment management)
- Dependencies managed in `tools/pyproject.toml`

## Development

Python tools located in `skills/route-researcher/tools/`:
- `peakbagger.py` - PeakBagger scraper and analyzer
- `fetch_weather.py` - Weather forecast fetcher
- `fetch_avalanche.py` - NWAC avalanche forecast fetcher
- `calculate_daylight.py` - Sunrise/sunset calculator

Run tests:
```bash
cd skills/route-researcher/tools
uv run pytest
```

## Safety Notice

This skill generates AI-assisted research documents. All reports include prominent safety disclaimers. Users must:
- Verify critical information from primary sources
- Use their own judgment and experience
- Cross-reference with current conditions
- Understand that mountain conditions change rapidly

**The mountains are inherently dangerous. You are responsible for your own safety.**
```

**Step 2: Update root README**

Modify root `README.md`:
```markdown
# Claude Skills

This is my personal skill experimentation repository for Claude Code.

## About

This repository contains custom skills I'm developing to extend Claude's capabilities for specialized tasks and workflows. Skills are modular extensions that provide Claude with domain-specific knowledge, structured processes, and tool integrations.

## Current Skills

### Route Researcher
Research Pacific Northwest mountain peaks and generate comprehensive route beta reports with current conditions, weather, gear statistics, and safety information.

**Status:** Implemented
**Location:** `skills/route-researcher/`
**Documentation:** [Route Researcher README](skills/route-researcher/README.md)

## Usage

These skills are experimental and tailored to my specific workflows and needs.

## Repository Structure

```
claude-skills/
├── skills/              # Skill implementations
│   └── route-researcher/
├── route-beta/          # Generated route beta reports
└── docs/
    └── plans/           # Design documents and plans
```
```

**Step 3: Commit**

```bash
git add skills/route-researcher/README.md README.md
git commit -m "docs: add comprehensive documentation for route-researcher skill"
```

---

## Task 13: Final Integration Test and Refinement

**Step 1: Run full end-to-end test**

In a fresh session, test the complete workflow:
```
"Use the route-researcher skill to research Mt Baker"
```

**Step 2: Verify report quality**

Check generated report:
- All sections present
- Data is accurate and well-formatted
- Safety disclaimer prominent
- Information gaps clearly noted
- Links work correctly

**Step 3: Fix any issues found**

If issues discovered:
- Fix in appropriate file (SKILL.md or Python tools)
- Test again
- Commit fixes

**Step 4: Final commit**

```bash
git add -A
git commit -m "fix: address issues found in end-to-end testing"
```

---

## Task 14: Prepare for Merge

**Step 1: Run all tests**

```bash
cd skills/route-researcher/tools
uv run pytest -v
```

Expected: All tests passing

**Step 2: Check git status**

```bash
git status
```

Expected: Clean working tree, all changes committed

**Step 3: Review commits**

```bash
git log --oneline
```

Verify commits are logical and well-described

**Step 4: Push branch (if remote configured)**

```bash
git push -u origin feature/route-researcher
```

**Step 5: Return to main workspace**

User should now decide whether to:
- Create PR for review
- Merge directly to main
- Continue iterating

Use `superpowers:finishing-a-development-branch` skill for completion.

---

## Success Criteria

Implementation complete when:

- ✅ All Python tools implemented and tested
- ✅ Skill orchestration logic complete in SKILL.md
- ✅ End-to-end workflow tested successfully
- ✅ Reports generated with all required sections
- ✅ Error handling graceful (no hard failures on missing data)
- ✅ Documentation complete (README, TEST_CASES)
- ✅ All tests passing
- ✅ Clean git history with logical commits

## Notes

- Follow TDD: Write test, watch it fail, implement, watch it pass
- Commit frequently (after each task step)
- Don't skip manual testing - automated tests can't catch everything
- PeakBagger HTML structure may require adjustment during implementation
- Weather/avalanche forecast parsing may need refinement based on actual site structure
- Be prepared to iterate on report format based on first real outputs
