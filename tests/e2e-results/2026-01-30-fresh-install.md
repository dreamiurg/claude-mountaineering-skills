# E2E Test: Fresh Installation Following README

**Date:** 2026-01-30
**Tester:** furiosa (polecat)
**Issue:** cms-ha3s

## Test Environment

- Clean temp directory: `/var/folders/.../tmp.tR0EYwejNN`
- No prior plugin installation
- macOS Darwin 24.6.0

## Steps Executed

### 1. Clone the Repository

```bash
$ git clone https://github.com/dreamiurg/claude-mountaineering-skills.git
Cloning into 'claude-mountaineering-skills'...
```

**Result:** SUCCESS

### 2. Verify Plugin Structure

```bash
$ ls -la .claude-plugin/
hooks.json
marketplace.json
plugin.json
```

**Result:** SUCCESS - All required plugin files present

### 3. Validate JSON Configuration Files

```bash
$ cat .claude-plugin/plugin.json | python3 -m json.tool > /dev/null
$ cat .claude-plugin/marketplace.json | python3 -m json.tool > /dev/null
```

**Result:** SUCCESS - Both files are valid JSON

### 4. Verify Skill Structure

```bash
$ test -f skills/route-researcher/SKILL.md
```

**Result:** SUCCESS - Skill file exists

### 5. Install Python Dependencies

```bash
$ cd skills/route-researcher/tools
$ uv run python -c "import sys; print(f'Python: {sys.version}')"
Creating virtual environment at: .venv
   Building route-researcher-tools...
Installed 32 packages in 39ms
Python: 3.11.11
```

**Result:** SUCCESS - Dependencies installed automatically with `uv`

### 6. Test Python Tools

```bash
$ uv run python calculate_daylight.py --date 2026-01-30 --coordinates "47.4507,-121.4139"
{
  "date": "2026-01-30",
  "coordinates": {"latitude": 47.4507, "longitude": -121.4139},
  "sunrise": "07:34",
  "sunset": "17:04",
  "daylight_hours": 9.5,
  "note": "Times in Pacific timezone"
}

$ uv run python fetch_weather.py --peak-name "Mount Si" --coordinates "47.4507,-121.7239"
{
  "source": "Mountain-Forecast.com",
  "url": "https://www.mountain-forecast.com/peaks/mount-si",
  ...
}
```

**Result:** SUCCESS - All tools execute correctly

### 7. Run Unit Tests

```bash
$ uv run pytest -v
test_calculate_daylight.py::test_calculate_daylight_returns_times PASSED
test_fetch_avalanche.py::test_fetch_avalanche_returns_nwac_data PASSED
test_fetch_weather.py::test_fetch_weather_returns_forecast PASSED
========================= 3 passed, 4 skipped =========================
```

**Result:** SUCCESS - 3 passed, 4 skipped (expected)

## Issues Found

### BUG: Version Mismatch Between Files

The v4.0.0 release has inconsistent version numbers:

| File | Version |
|------|---------|
| package.json | 4.0.0 |
| .claude-plugin/plugin.json | 3.8.0 |
| .claude-plugin/marketplace.json | 3.8.0 |

The version bump commit (3e6b0a0) only updated `package.json` and `CHANGELOG.md` but missed the plugin configuration files.

**Impact:** Users installing via marketplace would see version 3.8.0 even after v4.0.0 release.

**Filed as:** cms-n8kd
**Fixed in:** This PR (updated plugin.json and marketplace.json to 4.0.0)

## Success Criteria Evaluation

| Criteria | Status |
|----------|--------|
| Installation completes without errors | PASS |
| All dependencies installed | PASS |
| Plugin recognized by Claude Code | PARTIAL - structure valid, version mismatch found |

## Recommendations

1. Fix version mismatch in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
2. Add pre-release check to ensure all version files are in sync
3. Consider semantic-release configuration to auto-update all version files

## Conclusion

Fresh installation **MOSTLY SUCCESSFUL** with one bug found: version mismatch between package.json (4.0.0) and plugin configuration files (3.8.0).
