# Privacy Policy

**Effective date:** 2026-07-05

This privacy policy covers the **Mountaineering plugin for Claude Code** (`claude-mountaineering-skills`), including the `route-researcher` skill and its bundled tools.

## Summary

This plugin collects no data. It has no servers, no telemetry, no analytics, no accounts, and no way for the author to see how you use it. Everything runs locally inside your own Claude Code session.

## What the plugin does

The plugin is a set of instructions and small command-line tools that your own Claude Code installation executes on your machine. When you ask Claude to research a mountain, the plugin fetches publicly available information from third-party websites and compiles it into a Markdown report saved to your local filesystem.

## Data we collect

**None.** The author of this plugin does not collect, store, transmit, sell, or share any personal data or usage data. The plugin contains no telemetry, analytics, crash reporting, or tracking code of any kind.

## Network requests your machine makes

When you use the skill, requests are sent **directly from your machine** to public third-party services to gather route information. These requests include the name and location of the peak you are researching and, like any web request, expose your IP address to the receiving service. Depending on the peak, these services include:

- **Route and trip-report sites:** PeakBagger, SummitPost, Washington Trails Association (wta.org), AllTrails, The Mountaineers, PeakVisor, Mountain-Forecast
- **Weather and daylight services:** Open-Meteo, National Weather Service (weather.gov), sunrise-sunset.org
- **Avalanche centers:** Northwest Avalanche Center (nwac.us) and other regional avalanche centers
- **Government and mapping services:** USDA Forest Service, USGS, FCC geo API, OpenStreetMap Overpass API, state transportation sites (e.g., WSDOT)

Each of these services has its own privacy policy that governs the requests it receives. The plugin sends them only what is needed to look up route information; it never sends your Claude conversation or anything else from your machine.

## Runtime dependencies

On first use, the plugin's tools are installed on your machine from public package registries (PyPI via `uv`/`uvx`, and GitHub for `peakbagger-cli`). Those registries see a standard package-download request from your machine, governed by their own privacy policies.

## Data stored on your machine

Generated route reports are written to your local filesystem and stay there. You control them entirely; nothing is uploaded anywhere by this plugin.

## Claude and Anthropic

The plugin runs inside Claude Code, which means your requests and the fetched content are processed by Anthropic's Claude models as part of your normal Claude Code usage. That processing is governed by [Anthropic's Privacy Policy](https://www.anthropic.com/legal/privacy), not by this document. This plugin does not change what Claude Code sends to Anthropic.

## Changes to this policy

If the plugin's behavior ever changes in a way that affects privacy (it has no plans to), this document will be updated in the repository and the change will appear in the project changelog and release notes.

## Contact

Questions about this policy: [open an issue](https://github.com/dreamiurg/claude-mountaineering-skills/issues) on the repository.
