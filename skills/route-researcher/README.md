# Route Researcher Skill

Research Pacific Northwest mountain peaks and generate comprehensive route beta reports combining data from multiple sources.

## Features

- **Peak validation** - Search PeakBagger and confirm correct peak with user
- **Comprehensive data gathering** - Peak info, weather forecasts, avalanche conditions, daylight calculations
- **Web-based research** - Uses WebSearch and WebFetch to gather route descriptions and trip reports
- **Statistical analysis** - Python tools calculate sunrise/sunset, fetch weather and avalanche forecasts
- **Structured reports** - Markdown documents with all essential route beta
- **Safety-focused** - Prominent disclaimers and explicit information gaps
- **Graceful degradation** - Handles missing data without failing

## Usage

Invoke the skill by requesting route research on a Pacific Northwest peak:

```
"Research Mt Baker"
"Get route beta for Sahale Peak"
"I'm planning to climb Forbidden Peak, can you research the route?"
```

The skill will:
1. Search PeakBagger for the peak using WebSearch
2. Validate with you (if multiple matches found)
3. Gather data from multiple sources in parallel
4. Synthesize information into a comprehensive report
5. Generate report in `route-beta/YYYY-MM-DD-peak-name.md`

## Output

Reports include:

- **Safety disclaimer** - Prominent AI-generated content warning
- **Summit information** - Elevation, prominence, coordinates, location
- **Route description** - Approach, standard route, key details
- **Crux** - Description of hardest/most technical section
- **Hazards & safety** - Known hazards, seasonal considerations, bailout options
- **Current conditions**:
  - Daylight hours (sunrise/sunset)
  - Weather forecast (Mountain-Forecast.com)
  - Avalanche forecast (NWAC) when applicable
- **Recent trip reports** - Links to 5-10 most recent reports
- **Access & permits** - Trailhead info, permit requirements, road conditions
- **Gear recommendations** - Based on route type and trip reports
- **Information gaps** - Explicit list of missing or uncertain data

## Data Sources

### Primary Sources (via WebSearch/WebFetch)
- **PeakBagger.com** - Peak information, coordinates, elevation, trip report links
- **Summit Post** - Route descriptions and approach details
- **Mountain Project** - Technical climbing route information
- **CascadeClimbers.com** - Recent trip reports and conditions
- **Mountaineers.org** - Historical reports and route information

### Current Conditions (via Python Tools)
- **Mountain-Forecast.com** - Mountain weather forecasts
- **NWAC** (Northwest Avalanche Center) - Avalanche forecasts and conditions
- **Astral library** - Sunrise/sunset calculations for daylight planning

## Architecture

The skill uses a hybrid approach:

1. **WebSearch/WebFetch** for qualitative data:
   - Peak validation and basic information
   - Route descriptions from climbing websites
   - Recent trip reports
   - Access and permit information

2. **Python CLI tools** for computational tasks:
   - Weather forecast retrieval
   - Avalanche forecast retrieval
   - Daylight calculations (sunrise/sunset)

This design leverages Claude's built-in web tools for scraping while keeping Python focused on computation and data processing.

## Requirements

- Python 3.11+
- uv (for Python environment management)
- Dependencies managed in `tools/pyproject.toml`:
  - click (CLI framework)
  - httpx (HTTP client)
  - beautifulsoup4 + lxml (HTML parsing)
  - rich (terminal output)
  - astral (astronomy calculations)

## Development

### Python Tools

Located in `skills/route-researcher/tools/`:

- `fetch_weather.py` - Fetch weather forecast from Mountain-Forecast.com
- `fetch_avalanche.py` - Fetch avalanche forecast from NWAC
- `calculate_daylight.py` - Calculate sunrise/sunset times
- `peakbagger.py` - *Note: Originally for scraping, now deprecated in favor of WebSearch/WebFetch*

### Running Tests

```bash
cd skills/route-researcher/tools
uv run pytest
```

All tools have corresponding test files (`test_*.py`).

### Manual Testing

Test individual tools:

```bash
cd skills/route-researcher/tools

# Weather forecast
uv run python fetch_weather.py --peak-name "Mt Baker" --coordinates "48.7767,-121.8144"

# Avalanche forecast
uv run python fetch_avalanche.py --region "North Cascades"

# Daylight calculation
uv run python calculate_daylight.py --date "2025-10-20" --coordinates "48.7767,-121.8144"
```

### Tool Output Format

All tools output JSON to stdout for easy parsing by the skill:

```json
{
  "source": "Mountain-Forecast.com",
  "url": "https://...",
  "forecast": ["Day 1 data", "Day 2 data"],
  "note": "Additional context"
}
```

Errors are gracefully handled - tools return helpful fallback data even on failure.

## Design Notes

### WebSearch/WebFetch Approach

The skill originally planned to use `peakbagger.py` for scraping PeakBagger pages. The implementation was changed to use Claude's built-in WebSearch and WebFetch tools instead:

**Benefits:**
- More reliable than custom HTML parsing
- Reduces maintenance burden (no HTML selectors to update)
- Leverages Claude's strengths in web content extraction
- Python tools focus on computation, not scraping

**Trade-offs:**
- Less precise extraction (LLM-based vs. selector-based)
- Dependent on WebFetch availability and quality
- May require more tokens for complex pages

This approach works well because:
1. Peak validation only needs search results (WebSearch)
2. Peak details can be extracted via prompting (WebFetch)
3. Route descriptions come from multiple sources (WebSearch + WebFetch)
4. Python tools handle calculations, not data extraction

### Graceful Degradation

The skill is designed to never fail completely. If a data source is unavailable:
- Document the gap explicitly in "Information Gaps" section
- Provide manual check links (e.g., "Check Mountain-Forecast.com")
- Continue with available data
- Generate report anyway

This ensures users get useful output even with partial data.

### Error Handling Strategy

- **Python scripts**: Return JSON with error info, exit 0 (not 1) for graceful degradation
- **WebFetch/WebSearch failures**: Note in gaps, continue with other sources
- **Missing coordinates**: Skip tools that require them, note in gaps
- **No trip reports found**: Include empty section with note about limited data

## Safety Notice

This skill generates AI-assisted research documents. All reports include prominent safety disclaimers.

**Users must:**
- Verify all critical information from primary sources
- Use their own judgment and experience to assess conditions and risk
- Cross-reference with current trip reports and local conditions
- Understand that conditions change rapidly in the mountains

**This is NOT a substitute for:**
- Proper training and experience
- Current weather and avalanche forecasts
- Your own research and route planning
- Sound mountaineering judgment

**The mountains are inherently dangerous. You are responsible for your own safety.**

## Example Report

See generated reports in `route-beta/` directory for examples.

Typical report structure:
```
route-beta/
├── 2025-10-20-mount-baker.md
├── 2025-10-20-sahale-peak.md
└── 2025-10-20-forbidden-peak.md
```

Each report is self-contained with all gathered information, source links, and explicit gaps.

## Future Enhancements

Potential improvements:
- Gear statistics analysis from trip reports (currently manual synthesis)
- GPS track aggregation from multiple sources
- Historical conditions database for seasonal patterns
- More sophisticated route type detection
- Integration with additional weather sources (NOAA, Weather.gov)
- Permit availability checking
- Trailhead parking info and recommendations

## Contributing

This is a personal experimental skill. Feedback and suggestions welcome but not actively seeking contributions.

## License

Personal use. Not licensed for redistribution.
