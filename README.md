<h1 align="center">Mountaineering Skills for Claude Code</h1>

<p align="center">
  <a href="https://github.com/hesreallyhim/awesome-claude-code">
    <img src="https://awesome.re/mentioned-badge-flat.svg" alt="Mentioned in Awesome Claude Code">
  </a>
  <a href="https://docs.anthropic.com/en/docs/claude-code/overview">
    <img src="https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg" alt="Claude Code Plugin">
  </a>
</p>

<h4 align="center">Automated mountain route research for North American peaks, built for <a href="https://claude.com/claude-code" target="_blank">Claude Code</a>.</h4>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#support">Support</a>
</p>

Ask Claude to research any mountain. The route-researcher skill pulls from 10+ mountaineering sources and compiles a detailed Markdown report with current weather, avalanche conditions, daylight windows, trip reports, and route beta. What used to take 3-5 hours of tab-hopping now takes 3-5 minutes.

**See it in action:**

| Peak | Elevation | What it shows |
|------|-----------|---------------|
| [Mount Si](skills/route-researcher/examples/2025-10-23-mount-si.md) | 4,167 ft | High-traffic trail with abundant trip reports |
| [Mount Adams](skills/route-researcher/examples/2025-11-06-mount-adams.md) | 12,280 ft | Glaciated volcano with weather/avy conditions |
| [Wolf Peak](skills/route-researcher/examples/2025-11-06-wolf-peak.md) | 5,813 ft | Technical scramble with sparse beta |
| [Mount Shuksan](skills/route-researcher/examples/2026-01-29-mount-shuksan.md) | 9,129 ft | Glacier climb requiring crevasse rescue skills |
| [Tinkham Peak](skills/route-researcher/examples/2026-01-29-tinkham-peak.md) | 5,398 ft | Accessible Class 2-3 scramble near Snoqualmie Pass |

---

## Quick Start

```
/plugin marketplace add dreamiurg/claude-mountaineering-skills
/plugin install mountaineering-skills@mountaineering-skills-marketplace
```

Restart Claude Code, then ask:

```
"Research Mount Rainier"
```

That's it. Claude generates a route beta report in your current directory.

---

## How It Works

The skill follows seven phases, mostly parallelized:

```mermaid
graph TB
    Start([User asks Claude to<br/>research a peak]) --> Search[Phase 1: Peak Identification<br/>Search PeakBagger database]
    Search --> Match{Multiple<br/>matches?}
    Match -->|Yes| Confirm[Ask user to confirm<br/>correct peak]
    Match -->|No| Info
    Confirm --> Info[Phase 2: Peak Information<br/>Fetch elevation, coordinates,<br/>location, prominence]

    Info --> Parallel[Phase 3: Parallel Data Gathering<br/>Execute 8+ tasks simultaneously]

    Parallel --> Routes[Route Descriptions<br/>SummitPost, WTA,<br/>AllTrails, Mountaineers]
    Parallel --> Weather[Weather Forecasts<br/>Open-Meteo API<br/>7-day forecasts]
    Parallel --> Avy[Avalanche Conditions<br/>NWAC, regional<br/>avalanche centers]
    Parallel --> Day[Daylight Calculations<br/>Sunrise, sunset,<br/>alpine start times]
    Parallel --> Stats[Ascent Statistics<br/>PeakBagger patterns<br/>seasonal analysis]
    Parallel --> Reports[Trip Reports<br/>Discover & rank by<br/>content quality]
    Parallel --> Access[Access & Permits<br/>Trailhead info,<br/>regulations, fees]

    Routes --> Analyze
    Weather --> Analyze
    Avy --> Analyze
    Day --> Analyze
    Stats --> Analyze
    Reports --> Analyze
    Access --> Analyze

    Analyze[Phase 4: Route Analysis<br/>Synthesize data, identify hazards,<br/>calculate time estimates,<br/>document information gaps]

    Analyze --> Generate[Phase 5: Report Generation<br/>Create structured Markdown<br/>report file]

    Generate --> Review[Phase 6: Report Review<br/>Validate factual accuracy,<br/>fix inconsistencies,<br/>ensure quality]

    Review --> Save[Phase 7: Completion<br/>Save to working directory<br/>YYYY-MM-DD-peak-name.md]

    Save --> End([User receives detailed<br/>route beta report])

    style Start fill:#e1f5ff
    style End fill:#e1f5ff
    style Parallel fill:#fff4e1
    style Routes fill:#f0f0f0
    style Weather fill:#f0f0f0
    style Avy fill:#f0f0f0
    style Day fill:#f0f0f0
    style Stats fill:#f0f0f0
    style Reports fill:#f0f0f0
    style Access fill:#f0f0f0
```

The skill runs data-gathering tasks in parallel, ranks trip reports by content quality, and validates the final report for accuracy. If a source fails, it documents the gap and keeps going.

---

## Features

### Data Sources

The skill aggregates from specialized mountaineering sites:

| Category | Sources |
|----------|---------|
| Peak info | [PeakBagger](https://www.peakbagger.com) |
| Routes | [SummitPost](https://www.summitpost.org), [WTA](https://www.wta.org), [AllTrails](https://www.alltrails.com), [The Mountaineers](https://www.mountaineers.org) |
| Weather | [Mountain-Forecast.com](https://www.mountain-forecast.com), [NOAA/NWS](https://www.weather.gov) |
| Avalanche | [NWAC](https://nwac.us), regional centers |
| Trip reports | [CascadeClimbers](https://cascadeclimbers.com), [PeakBagger](https://www.peakbagger.com), [Mountain Project](https://www.mountainproject.com) |

**Coverage note:** Report quality depends on how well-documented your peak is across these sources. Works best for popular North American peaks.

### Graceful Degradation

Missing data? The skill notes what's unavailable in an "Information Gaps" section and provides manual lookup links. You always get a report, even if some sources are down.

---

## Installation

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview), optionally [uv](https://docs.astral.sh/uv/) for Python tools.

```
/plugin marketplace add dreamiurg/claude-mountaineering-skills
/plugin install mountaineering-skills@mountaineering-skills-marketplace
```

Python dependencies install automatically if `uv` is available.

**Verify it worked:**

```
"What skills are available?"
```

You should see `route-researcher` in the list.

---

## Usage

Just ask naturally:

```
"Research Mt Baker"
"Get route beta for Forbidden Peak"
"I'm planning to climb Sahale Peak, can you research it?"
```

Reports save to your current directory as `YYYY-MM-DD-peak-name.md`.

---

## Dependencies

- [peakbagger-cli](https://github.com/dreamiurg/peakbagger-cli) v1.7.0 - peak data and trip reports
- [Python tools](skills/route-researcher/tools/README.md) - weather, avalanche, and daylight calculations

---

## Updates

```
/plugin list                          # check current version
/plugin update mountaineering-skills  # update to latest
```

---

## Contributing

Pull requests welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Support

[Open an issue](https://github.com/dreamiurg/claude-mountaineering-skills/issues) or [start a discussion](https://github.com/dreamiurg/claude-mountaineering-skills/discussions).

---

## License

[MIT](LICENSE)
