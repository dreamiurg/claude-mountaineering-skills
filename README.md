# Mountaineering Skills for Claude Code

Claude Code plugin for researching Pacific Northwest mountain peaks and generating comprehensive route beta reports.

## Installation

### Prerequisites

- [Claude Code](https://docs.claude.com/claude-code) installed
- [uv](https://docs.astral.sh/uv/) (optional, for Python tools)

### Install Plugin

This repo contains both marketplace and skills. It add it to Claude Code, run the following commands:

```bash
% claude
> /plugin marketplace add dreamiurg/claude-mountaineering-skills
  ⎿  Successfully added marketplace: mountaineering-skills-marketplace

> /plugin install mountaineering-skills@mountaineering-skills-marketplace
  ⎿  ✓ Installed mountaineering-skills. Restart Claude Code to load new plugins.```

The plugin installs Python dependencies automatically if `uv` is available. If not, see [Manual Installation](#manual-installation) below.

### Verify Installation

In any Claude Code session:

```bash
"What skills are available?"
```

You should see `route-researcher` listed.

## Usage

Simply ask Claude to research a mountain peak:

```bash
"Research Mt Baker"
"Get route beta for Forbidden Peak"
"I'm planning to climb Sahale Peak, can you research the route?"
```

Claude will automatically invoke the route-researcher skill and generate a comprehensive route beta report in your current directory.

### Generated Output

Reports are created as Markdown files in your current working directory:

```
2025-10-20-mount-baker.md
```

Each report includes:
- Summit information (elevation, coordinates, location)
- Route description (approach, standard route, crux)
- Current conditions (weather, avalanche, daylight)
- Recent trip reports with links
- Access and permit information
- Explicit documentation of information gaps

See [examples](skills/route-researcher/examples/) for sample outputs.

## Features

### Multi-Source Data Gathering

- **PeakBagger**: Peak information, coordinates, elevation
- **Weather**: Mountain-Forecast.com, NOAA/NWS point forecasts
- **Avalanche**: NWAC forecasts (when applicable)
- **Trip Reports**: CascadeClimbers, PeakBagger, Mountain Project
- **Route Info**: SummitPost, Mountaineers.org, Mountain Project

### Safety-First Approach

- Prominent AI-generated content disclaimers
- Explicit information gap documentation
- Manual verification links for all data sources
- Clear safety warnings and hazard information

### Graceful Degradation

If data sources are unavailable:
- Skill continues with available sources
- Notes missing data in "Information Gaps" section
- Provides manual check links
- Always generates a report, even with partial data

## Python Tools

The plugin includes Python utilities for enhanced functionality:

- `cloudscrape.py` - Bypasses Cloudflare protection for PeakBagger, SummitPost
- `fetch_weather.py` - Mountain weather forecasts (in development)
- `fetch_avalanche.py` - NWAC avalanche data (in development)
- `calculate_daylight.py` - Sunrise/sunset calculations (in development)

### Manual Installation

If automatic installation failed or you don't have `uv`:

```bash
# Navigate to plugin installation
cd ~/.claude/plugins/mountaineering-skills/skills/route-researcher/tools

# Install dependencies with uv
uv sync

# Or with pip
pip install -r requirements.txt
```

The skill will work without these tools, falling back to available data sources.

## Troubleshooting

### Hook Installation Failed

If you see "post-install hook failed":

1. Check if `uv` is installed: `uv --version`
2. Try manual installation (see above)
3. The skill will still work, just without some Python tools

### Cloudflare Blocking Requests

The `cloudscrape.py` tool handles Cloudflare protection, but may occasionally fail:

- Skill automatically falls back to available sources
- Check "Information Gaps" section in generated reports
- Use manual verification links provided

### No Route Beta Generated

Ensure you're in a directory where you have write permissions. Reports are created in your current working directory, not in the plugin installation.

## Updates

Check for plugin updates:

```bash
/plugin list
```

Update to the latest version:

```bash
/plugin update mountaineering-skills
```

## Contributing

Found a bug or have a feature request? Please [open an issue](https://github.com/dreamiurg/claude-mountaineering-skills/issues).

Pull requests welcome! This project uses:
- Conventional commits for automated releases
- `feat:` for new features (minor version bump)
- `fix:` for bug fixes (patch version bump)
- `feat!:` or `BREAKING CHANGE:` for breaking changes (major version bump)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

This tool generates AI-assisted research and should be used as a starting point only. Always verify critical information from primary sources, check current conditions, and use your own judgment for trip planning and safety decisions.

The mountains are inherently dangerous. You are responsible for your own safety.
