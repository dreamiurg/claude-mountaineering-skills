# Route Researcher Architecture

## Overview

The route-researcher skill uses a hybrid architecture combining:

- **Python scripts** for deterministic API calls (weather, air quality, daylight, peakbagger stats)
- **LLM agents** for tasks requiring judgment (web scraping, content extraction, report writing, validation)

This approach minimizes token usage while maximizing parallelism and reliability.

## Components

### Python Scripts (`tools/`)

| Script | Purpose | Output |
| :----- | :------ | :----- |
| `fetch_conditions.py` | Unified conditions fetcher | JSON with weather, air quality, daylight, avalanche, peakbagger data |
| `cloudscrape.py` | Fallback web fetcher for blocked sites | HTML content |

### Agent Types (3 total)

| Agent | Role | Count | When |
| :---- | :--- | :---- | :--- |
| **Researcher** | Gather data from web sources, fetch trip reports | 3 parallel | Phase 3 |
| **Report Writer** | Generate markdown report from data package | 1 | Phase 5 |
| **Report Reviewer** | Validate report quality, fix issues | 1 | Phase 6 |

### Orchestrator (SKILL.md)

The orchestrator handles:

- Peak identification (Phases 1-2)
- Coordinating parallel data gathering (Phase 3)
- Data synthesis and analysis (Phase 4)
- Agent dispatch and result aggregation (Phases 3, 5, 6)
- User presentation (Phase 7)

## Execution Flow

```text
User Request
    │
    ▼
Phase 1-2: Peak Identification
    │ (peakbagger-cli search/info)
    ▼
Phase 3: Data Gathering (PARALLEL)
    ┌─────────────────────────────────────────────┐
    │  Python: fetch_conditions.py                │
    │  (weather, air quality, daylight,           │
    │   avalanche, peakbagger stats)              │
    ├─────────────────────────────────────────────┤
    │  Agent 1: PeakBagger + SummitPost           │
    │  Agent 2: WTA + Mountaineers                │
    │  Agent 3: AllTrails                         │
    │  (each fetches route info + trip reports)   │
    └─────────────────────────────────────────────┘
    │
    ▼
Phase 4: Analysis (orchestrator inline)
    │ (route type, crux, hazards, time estimates)
    ▼
Phase 5: Report Writer Agent
    │ (generates markdown from data package)
    ▼
Phase 6: Report Reviewer Agent
    │ (validates and fixes issues)
    ▼
Phase 7: Present to User
```

## Data Contracts

All agents return JSON matching explicit schemas defined in SKILL.md.

### Researcher Agent Output

```json
{
  "sources": ["PeakBagger", "SummitPost"],
  "route_info": [
    {"source": "...", "name": "...", "difficulty": "...", "description": "...", "hazards": [...]}
  ],
  "trip_reports": [
    {"source": "...", "date": "...", "author": "...", "url": "...", "summary": "...", "conditions": "..."}
  ],
  "gaps": ["what couldn't be fetched and why"]
}
```

### Report Writer Output

```json
{
  "status": "SUCCESS",
  "file_path": "/path/to/report.md",
  "filename": "YYYY-MM-DD-peak-name.md",
  "sections_generated": N
}
```

### Report Reviewer Output

```json
{
  "status": "PASS | PASS_WITH_FIXES | FAIL",
  "issues_found": N,
  "fixes_applied": ["description of fixes"],
  "remaining_issues": [],
  "report_path": "/path/to/report.md"
}
```

## Error Handling

| Layer | Failure | Response |
| :---- | :------ | :------- |
| Python API call | Timeout/down | Return partial data + gaps array |
| Researcher agent | Entire agent fails | Proceed with other agents' data |
| Researcher agent | Single source fails | Return partial data + gaps |
| Report Writer | Can't generate | Fail loudly (critical) |
| Report Reviewer | Unfixable issues | Return FAIL status, ask user |

**Minimum viable report:** Peak metadata + at least one route source + conditions data.

## Design Decisions

### Why Python for API calls?

- Deterministic: No LLM judgment needed for structured API responses
- Reliable: No prompt variability
- Fast: Direct HTTP calls, no agent overhead
- Cheap: Zero tokens for weather/daylight/air quality

### Why inline agent prompts?

- Reliable: No "read instructions from file" failure mode
- Self-contained: Agent has everything it needs in the prompt
- Explicit contracts: JSON output format clearly specified
- Testable: Can verify prompt produces expected results

### Why 3 researcher agents (not 5)?

- Balance: Enough parallelism without coordination overhead
- Source grouping: Related sources assigned together (PeakBagger+SummitPost, WTA+Mountaineers)
- Trip report batching: Each agent fetches its own reports (no separate fetch step)

## Maintenance

To modify agent behavior:

1. Edit the inline prompt in SKILL.md (Phases 3, 5, or 6)
2. Update the JSON output contract if needed
3. Test with a real peak to verify changes work

To add new data sources:

1. Decide if it's API-based (add to fetch_conditions.py) or web-based (add to a Researcher agent)
2. Update the relevant component
3. Update data aggregation in Phase 3C
4. Update Report Writer prompt if new sections needed
