## [4.0.2](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v4.0.1...v4.0.2) (2026-01-30)


### Bug Fixes

* add version footer to SKILL.md for semantic-release ([#62](https://github.com/dreamiurg/claude-mountaineering-skills/issues/62)) ([1e5bab1](https://github.com/dreamiurg/claude-mountaineering-skills/commit/1e5bab13f64faa5791972032c8a32b1e8bca79d1))

## [4.0.1](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v4.0.0...v4.0.1) (2026-01-30)

### Features

* **e2e-validation**: comprehensive multi-peak end-to-end testing ([#60](https://github.com/dreamiurg/claude-mountaineering-skills/issues/60))

### Summary

This patch release includes comprehensive end-to-end validation of the parallel agent architecture:

- **Mount Hood**: Full route research with winter conditions analysis
- **Grand Teton**: Technical route beta with seasonal recommendations
- **Mount Whitney**: Complete mountaineering report with permit information

All tests validated the parallel agent workflow: PeakBagger data collection, weather/avalanche conditions, trip reports aggregation, and final report synthesis.

## [3.8.2](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.8.1...v3.8.2) (2026-01-30)


### Bug Fixes

* update demo GIF with correct model name and wider terminal ([#58](https://github.com/dreamiurg/claude-mountaineering-skills/issues/58)) ([dac9cd7](https://github.com/dreamiurg/claude-mountaineering-skills/commit/dac9cd726f48588a35fcfa39b06d09f55114d8ec))

## [3.8.1](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.8.0...v3.8.1) (2026-01-30)


### Bug Fixes

* sync plugin version to 4.0.0 and add E2E test results ([#57](https://github.com/dreamiurg/claude-mountaineering-skills/issues/57)) ([1ac0405](https://github.com/dreamiurg/claude-mountaineering-skills/commit/1ac04053603ac8e096b53492acc40be0d82bc4b7))

## [4.0.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.8.0...v4.0.0) (2026-01-30)

### ⚠ BREAKING CHANGES

* Major release bundling significant architecture improvements and developer experience enhancements.

### Features

* **parallel-agents**: implement parallel agent architecture for route-researcher skill ([#25](https://github.com/dreamiurg/claude-mountaineering-skills/issues/25))
* **pre-commit**: add production-ready pre-commit hooks for code quality
* **docs**: add animated demo GIF and polish README documentation
* **examples**: consolidate and improve example route beta reports

### Summary

This major version release consolidates the v3.6-v3.8 improvements into a stable release:

- **Parallel Agent Architecture**: Route research now uses multiple specialized agents working concurrently, significantly improving research speed and quality
- **Pre-commit Hooks**: Automated code quality checks including linting, formatting, and conventional commit enforcement
- **Documentation Polish**: README improvements with animated demonstration GIF showing the skill in action
- **Examples Consolidation**: Cleaned up and improved example route beta reports

## [3.8.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.7.0...v3.8.0) (2026-01-30)


### Features

* add animated demo GIF to README ([#52](https://github.com/dreamiurg/claude-mountaineering-skills/issues/52)) ([405685f](https://github.com/dreamiurg/claude-mountaineering-skills/commit/405685f07d275585a5659353c674c0cdf27ba39c))

## [3.7.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.6.0...v3.7.0) (2026-01-30)

### Features

* add production-ready pre-commit hooks ([#50](https://github.com/dreamiurg/claude-mountaineering-skills/issues/50)) ([685ff40](https://github.com/dreamiurg/claude-mountaineering-skills/commit/685ff40a033840c543911b11205086700f9fb07b))

## [3.6.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.5.1...v3.6.0) (2026-01-30)

### Features

* parallel agent architecture for route-researcher ([#49](https://github.com/dreamiurg/claude-mountaineering-skills/issues/49)) ([b5db7cd](https://github.com/dreamiurg/claude-mountaineering-skills/commit/b5db7cdafcf9b0aa257e6e5e84c05438d9112de2)), closes [#25](https://github.com/dreamiurg/claude-mountaineering-skills/issues/25) [#25](https://github.com/dreamiurg/claude-mountaineering-skills/issues/25) [#25](https://github.com/dreamiurg/claude-mountaineering-skills/issues/25) [#25](https://github.com/dreamiurg/claude-mountaineering-skills/issues/25) [#25](https://github.com/dreamiurg/claude-mountaineering-skills/issues/25) [#25](https://github.com/dreamiurg/claude-mountaineering-skills/issues/25) [#25](https://github.com/dreamiurg/claude-mountaineering-skills/issues/25) [#25](https://github.com/dreamiurg/claude-mountaineering-skills/issues/25) [#25](https://github.com/dreamiurg/claude-mountaineering-skills/issues/25)

## [3.5.1](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.5.0...v3.5.1) (2026-01-30)

### Bug Fixes

* correct Claude Code documentation URLs in README ([#48](https://github.com/dreamiurg/claude-mountaineering-skills/issues/48)) ([f08c20a](https://github.com/dreamiurg/claude-mountaineering-skills/commit/f08c20ae06299a9a0113bf798e003e7abc44f851))

## [3.5.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.4.0...v3.5.0) (2025-11-07)

### Features

* automate CHANGELOG to README synchronization ([#24](https://github.com/dreamiurg/claude-mountaineering-skills/issues/24)) ([5026772](https://github.com/dreamiurg/claude-mountaineering-skills/commit/50267727ccc099669867cd5feb254e1326b1be16))

## [3.4.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.3.0...v3.4.0) (2025-11-07)

### Features

* add automated report review and validation ([#23](https://github.com/dreamiurg/claude-mountaineering-skills/issues/23)) ([d684a63](https://github.com/dreamiurg/claude-mountaineering-skills/commit/d684a636cc12480733caf2d2e039acf3fdf8bb82))

## [3.3.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.2.0...v3.3.0) (2025-11-06)

### Features

* add example route beta reports for Mount Adams and Wolf Peak ([#19](https://github.com/dreamiurg/claude-mountaineering-skills/issues/19)) ([4a91d06](https://github.com/dreamiurg/claude-mountaineering-skills/commit/4a91d067e27ec4aca1de18427dbf115d279db290))

## [3.2.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.1.0...v3.2.0) (2025-10-24)

### Features

* expand geographic scope from Pacific Northwest to North America ([#18](https://github.com/dreamiurg/claude-mountaineering-skills/issues/18)) ([ceb0db0](https://github.com/dreamiurg/claude-mountaineering-skills/commit/ceb0db07a9214ed965c458fb5d7717ea0215974c))

## [3.1.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v3.0.0...v3.1.0) (2025-10-24)

### Features

* upgrade peakbagger-cli to v1.7.0 and restructure skill workflow ([#16](https://github.com/dreamiurg/claude-mountaineering-skills/issues/16)) ([3691723](https://github.com/dreamiurg/claude-mountaineering-skills/commit/3691723bbbf412ddf5d394b28a873d0d4597fcfc))

## [3.0.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v2.1.0...v3.0.0) (2025-10-23)

### ⚠ BREAKING CHANGES

* This major update brings significant new capabilities to the route-researcher skill:

* v1.3.0: New ascent report command for generating peak ascent summaries
* v1.4.0: --dump-html option for debugging and custom HTML extraction
* v1.2.1: Improved reliability with table structure parsing fixes

The skill now leverages the full ascent analysis capabilities including temporal patterns, GPX track availability, and trip report discovery.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-authored-by: Claude <noreply@anthropic.com>

### Features

* upgrade peakbagger-cli to v1.4.0 with ascent analysis capabilities ([#14](https://github.com/dreamiurg/claude-mountaineering-skills/issues/14)) ([6ba6bf0](https://github.com/dreamiurg/claude-mountaineering-skills/commit/6ba6bf067141f3d04bc1f5300733a6375d9719e7))

## [2.1.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v2.0.1...v2.1.0) (2025-10-21)

### Features

* add WTA and Mountaineers trip report extraction via cloudscrape.py ([#13](https://github.com/dreamiurg/claude-mountaineering-skills/issues/13)) ([3532a22](https://github.com/dreamiurg/claude-mountaineering-skills/commit/3532a221c6dffdbbe4a1ebc747cf52a5a362bbea))

## [2.0.1](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v2.0.0...v2.0.1) (2025-10-21)

### Bug Fixes

* post-v2.0.0 report formatting and URL fixes ([#12](https://github.com/dreamiurg/claude-mountaineering-skills/issues/12)) ([47d4aee](https://github.com/dreamiurg/claude-mountaineering-skills/commit/47d4aee3e7f9c3ac97a938c42aba2e680eb09c91))

## [2.0.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v1.2.0...v2.0.0) (2025-10-21)

### ⚠ BREAKING CHANGES

* Update all peakbagger-cli commands to use v1.0.0 with new
resource-action pattern syntax.

**Command Changes:**
* `peakbagger search` → `peakbagger peak search`
* `peakbagger info` → `peakbagger peak show`
* `peakbagger peak-ascents` → `peakbagger peak stats` (statistics)
* `peakbagger peak-ascents --list-ascents` → `peakbagger peak ascents` (listings)

**New Command Structure:**
All commands now follow resource-action pattern (e.g., `peak search`, `peak show`)
with clearer separation of concerns:
* `peak search`: Find peaks by name
* `peak show`: Get detailed peak information
* `peak stats`: Analyze ascent statistics and patterns
* `peak ascents`: List individual ascents with filtering

**Files Updated:**
* skills/route-researcher/SKILL.md:
  * Phase 1: Updated search command
  * Phase 2A: Updated info → show command
  * Phase 2C: Split into stats (Step 1) and ascents (Step 2)
  * Implementation Notes: Document v1.0.0 resource-action pattern
* README.md:
  * Updated version pin from v0.6.2 to v1.0.0
  * Added command structure examples
  * Updated future PyPI constraint to >=1.0,<2.0

**Testing:**
All commands verified working with v1.0.0:
* ✓ peak search returns JSON results
* ✓ peak show returns detailed peak info
* ✓ peak stats returns ascent statistics
* ✓ peak ascents with --within filter works correctly

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>

* perf: optimize Phase 2 with explicit parallel execution strategy

Reorganize Phase 2 data gathering to maximize parallelization and minimize
total execution time by launching all independent tasks simultaneously once
coordinates are available.

**Key Changes:**

1. **Explicit Execution Strategy:**
   * Step 2A (Sequential): Get peak info + coordinates (blocking)
   * Steps 2B-2H (Parallel): Execute ALL simultaneously after 2A completes

2. **Clear Section Marking:**
   * Added "- EXECUTE FIRST" to Step 2A header
   * Added "- PARALLEL" to all Steps 2B-2H headers
   * Added visual separator (---) before parallel section
   * New section: "Steps 2B-2H: Execute in Parallel (After 2A Completes)"

3. **Updated Language:**
   * Changed "Only if coordinates available" → "Requires coordinates from Step 2A"
   * Added explicit instruction: "immediately launch Steps 2B through 2H in parallel"
   * Emphasized with CRITICAL directive

4. **Phase 2 Summary:**
   * Added summary section documenting parallel execution strategy
   * Listed all steps with dependency notes
   * Explained performance benefit formula:
     time(Phase 2) = time(2A) + max(time(2B:2H)) vs sequential sum

**Performance Impact:**

Before: ~60-90 seconds (sequential execution of 8 steps)
After: ~15-20 seconds (2A sequential + parallel 2B-2H)

Estimated 3-4x speedup for Phase 2 data gathering.

**Rationale:**

Weather (2E), daylight (2G), and avalanche (2F) APIs only need coordinates
from 2A, not route descriptions or trip reports. No reason to wait for
WebSearch/WebFetch tasks to complete before fetching location-based data.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>

* chore: add commit and PR templates with contribution guidelines

Add standardized templates and documentation for consistent commit messages
and pull requests, following Conventional Commits specification for
automated semantic versioning.

**Files Added:**

1. `.gitmessage` - Git commit message template
   * Structured format with type, subject, body, footer
   * 10 commit types (feat, fix, docs, style, refactor, perf, test, chore, ci, build)
   * Version bump guidance (feat/fix/perf trigger releases)
   * Breaking change syntax (! or BREAKING CHANGE:)
   * Examples and best practices

2. `.github/pull_request_template.md` - PR template
   * Title format validation guidance
   * Type selection checkboxes
   * Sections: Summary, Type, Changes, Breaking Changes, Testing, Related Issues
   * Matches peakbagger-cli PR template structure

**Files Updated:**

3. `README.md` - Expanded Contributing section
   * Detailed commit message format documentation
   * Types categorized by release impact
   * Git commit template setup instructions
   * PR guidelines and requirements
   * Link to .gitmessage for examples

**Setup Instructions:**

Contributors can enable the commit template locally:

```bash
git config commit.template .gitmessage
```

**Based On:**

Templates and conventions adapted from peakbagger-cli repository to ensure
consistency across related projects.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>

### Features

* integrate peakbagger-cli and optimize data gathering ([#11](https://github.com/dreamiurg/claude-mountaineering-skills/issues/11)) ([f062e71](https://github.com/dreamiurg/claude-mountaineering-skills/commit/f062e71f79ab35217d9be2711416e2b866a85dce))

## [1.2.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v1.1.2...v1.2.0) (2025-10-21)

### Features

* updated report format ([#6](https://github.com/dreamiurg/claude-mountaineering-skills/issues/6)) ([79c591c](https://github.com/dreamiurg/claude-mountaineering-skills/commit/79c591cb5014b5146bd0ab9ffd8e15238f9e7624))

### Bug Fixes

* configure semantic-release to use deploy key for branch protection bypass ([#7](https://github.com/dreamiurg/claude-mountaineering-skills/issues/7)) ([a1640b0](https://github.com/dreamiurg/claude-mountaineering-skills/commit/a1640b00cc31e1192fbb78600bf61f6e3935ef62))
* use SSH remote for semantic-release git operations ([#8](https://github.com/dreamiurg/claude-mountaineering-skills/issues/8)) ([80b6489](https://github.com/dreamiurg/claude-mountaineering-skills/commit/80b6489c891e89c7bb0058bced9fc833596bea25))

## [1.1.2](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v1.1.1...v1.1.2) (2025-10-21)

### Bug Fixes

* correct plugin.json author and skills path format ([#2](https://github.com/dreamiurg/claude-mountaineering-skills/issues/2)) ([eb5be44](https://github.com/dreamiurg/claude-mountaineering-skills/commit/eb5be44b6849e01e905f9c9bde3387efd965f893))

## [1.1.1](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v1.1.0...v1.1.1) (2025-10-21)

### Bug Fixes

* correct marketplace.json source field format ([#1](https://github.com/dreamiurg/claude-mountaineering-skills/issues/1)) ([8df43c8](https://github.com/dreamiurg/claude-mountaineering-skills/commit/8df43c89901f8eb17bc4105e3249c67c0c593c66))

## [1.1.0](https://github.com/dreamiurg/claude-mountaineering-skills/compare/v1.0.0...v1.1.0) (2025-10-21)

### Features

* extract report template to separate file for consistency ([d8ef768](https://github.com/dreamiurg/claude-mountaineering-skills/commit/d8ef768f04b9d116ad712ac8d1660162830117ed))

## 1.0.0 (2025-10-21)

### Features

* Claude Code plugin for Pacific Northwest mountain route research ([0f6087d](https://github.com/dreamiurg/claude-mountaineering-skills/commit/0f6087d1f84c302796bb423cfddc8c5ff567edd4))

### Bug Fixes

* add conventional-changelog-conventionalcommits dependency ([a05ba7b](https://github.com/dreamiurg/claude-mountaineering-skills/commit/a05ba7beb2ff52be621b0cb330e853aea182408a))
* use npm install instead of npm ci in GitHub Actions ([ed19984](https://github.com/dreamiurg/claude-mountaineering-skills/commit/ed199845238f5aea406604bb71e04a70b232d26b))

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
* Claude Code plugin distribution infrastructure
* Self-hosted marketplace configuration
* Automated releases via semantic-release
* GitHub Actions workflow for CI/CD
* Example route-beta reports
* Comprehensive installation documentation

[Unreleased]: https://github.com/dreamiurg/claude-mountaineering-skills/compare/v1.0.0...HEAD
