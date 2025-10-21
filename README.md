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
  ⎿  ✓ Installed mountaineering-skills. Restart Claude Code to load new plugins.
```

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

Reports are created as Markdown files in your current working directory with comprehensive route information, current conditions, trip reports, and safety disclaimers.

**Example:** See [Granite Mountain (Snoqualmie) route beta](skills/route-researcher/examples/2025-10-21-granite-mountain-snoqualmie.md) for a sample report.

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

The plugin includes Python utilities for enhanced data gathering (weather forecasts, avalanche conditions, daylight calculations). See [skills/route-researcher/tools/README.md](skills/route-researcher/tools/README.md) for details on available tools, manual installation, and troubleshooting.

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
