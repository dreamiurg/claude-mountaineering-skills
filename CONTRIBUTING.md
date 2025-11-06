# Contributing to Mountaineering Skills

Thank you for your interest in contributing to the Mountaineering Skills plugin for Claude Code! This document provides guidelines and information to help you contribute effectively.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

This project follows a professional and respectful code of conduct. Please be kind and constructive in all interactions.

## Getting Started

### Prerequisites

- [Claude Code](https://docs.claude.com/claude-code) installed
- [uv](https://docs.astral.sh/uv/) for Python package management
- Git configured on your machine
- Python 3.8+ (for working on Python tools)

### Local Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude-mountaineering-skills.git
   cd claude-mountaineering-skills
   ```

2. **Install the Plugin Locally**
   ```bash
   claude
   > /plugin marketplace add YOUR_USERNAME/claude-mountaineering-skills
   > /plugin install mountaineering-skills@YOUR_MARKETPLACE_NAME
   ```

3. **Set Up Python Tools** (if working on tools)
   ```bash
   cd skills/route-researcher/tools
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"
   ```

4. **Configure Git Commit Template**
   ```bash
   git config commit.template .gitmessage
   ```

## How to Contribute

### Reporting Bugs

When reporting bugs, please include:

- **Clear description** of the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Example peak name** that demonstrates the issue
- **Claude Code version** and operating system
- **Relevant logs** or error messages

### Suggesting Features

Feature suggestions are welcome! Please:

- Check existing issues to avoid duplicates
- Clearly describe the use case and benefit
- Provide examples of how it would work
- Consider if it fits the project's scope (North American mountain route research)

### Contributing Code

We welcome contributions including:

- Bug fixes
- New data source integrations
- Improved error handling
- Better route analysis logic
- Documentation improvements
- Test coverage improvements
- Python tool enhancements

## Development Workflow

### Branch Naming

Use descriptive branch names with prefixes:

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements

Examples:
- `feat/add-mountain-project-integration`
- `fix/coordinate-parsing-southern-hemisphere`
- `docs/improve-installation-guide`

### Making Changes

1. **Create a Branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make Your Changes**
   - Write clear, readable code
   - Follow existing code style and patterns
   - Add comments for complex logic
   - Update documentation as needed

3. **Test Your Changes**
   - Test the skill with multiple peaks
   - Verify edge cases (no data, multiple matches, errors)
   - Run Python tests if applicable: `pytest`
   - Check that reports generate correctly

4. **Commit Your Changes**
   - Follow [Commit Message Guidelines](#commit-message-guidelines)
   - Make atomic commits (one logical change per commit)
   - Write clear commit messages

5. **Push and Create PR**
   ```bash
   git push -u origin feat/your-feature-name
   ```
   - Open a pull request on GitHub
   - Fill out the PR template completely
   - Link any related issues

## Commit Message Guidelines

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated semantic versioning.

### Format

```
<type>: <description>

[optional body]

[optional footer]
```

### Types

**Types that trigger releases:**

- `feat:` - New feature (MINOR version bump: 1.0.0 → 1.1.0)
- `fix:` - Bug fix (PATCH version bump: 1.0.0 → 1.0.1)
- `perf:` - Performance improvement (PATCH version bump)

**Types that don't trigger releases:**

- `docs:` - Documentation changes
- `chore:` - Maintenance, dependencies, configs
- `refactor:` - Code restructuring without functionality change
- `test:` - Test changes
- `ci:` - CI/CD changes
- `build:` - Build system changes

**Breaking changes:**

- Add `!` after type: `feat!:` or `fix!:` (MAJOR bump: 1.0.0 → 2.0.0)
- Or add `BREAKING CHANGE:` in footer

### Examples

```bash
# Feature addition (triggers release)
feat: add Mountain Project integration for climbing routes

# Bug fix (triggers release)
fix: correct coordinate parsing for southern hemisphere peaks

# Breaking change (triggers major release)
feat!: restructure skill to use new data source priority system

BREAKING CHANGE: configuration format changed, see migration guide

# Documentation (no release)
docs: update installation instructions with troubleshooting steps

# Maintenance (no release)
chore: update peakbagger-cli dependency to v1.8.0
```

### Commit Message Tips

- Use imperative mood ("add" not "added" or "adds")
- Begin subject line with lowercase (after the colon)
- No period at the end of subject line
- Limit subject line to 50 characters
- Wrap body at 72 characters
- Explain *what* and *why*, not *how*

See [.gitmessage](.gitmessage) for the full template with examples.

## Pull Request Process

### Before Submitting

- [ ] Code follows existing style and patterns
- [ ] All tests pass (if applicable)
- [ ] Documentation updated (README, docstrings, comments)
- [ ] Commit messages follow Conventional Commits format
- [ ] PR title follows format: `type: description`
- [ ] Changes tested with multiple example peaks

### PR Title Format

PR titles must follow the same format as commit messages:

```
feat: add weather alert integration
fix: handle missing trip report data gracefully
docs: improve contributing guidelines
```

A GitHub Action validates the PR title format.

### Review Process

1. **Automated Checks**: GitHub Actions will run on your PR
2. **Code Review**: Maintainers will review your changes
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged
5. **Release**: Changes in `feat:`, `fix:`, and `perf:` PRs trigger automatic releases

### After Merging

- Semantic-release automatically creates a new version
- Release notes are generated from commit messages
- Plugin registry is updated automatically

## Testing Guidelines

### Manual Testing

When testing changes:

1. **Test Multiple Peak Types**
   - Popular peaks (Mount Si, Mount Rainier)
   - Obscure peaks with limited data
   - Peaks in different regions
   - Peaks with special characters in names

2. **Test Edge Cases**
   - No matching peaks found
   - Multiple peaks with same name
   - Data sources unavailable
   - Incomplete data

3. **Verify Report Quality**
   - All sections present
   - Information gaps documented
   - Links work correctly
   - Formatting is clean

### Python Tool Testing

For changes to Python tools in `skills/route-researcher/tools/`:

```bash
cd skills/route-researcher/tools

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_cloudscrape.py -v
```

### Test Writing Guidelines

- Test both success and failure cases
- Use descriptive test names
- Mock external dependencies
- Test graceful degradation
- Verify error messages are helpful

## Documentation

### What to Document

When contributing, update documentation for:

- **README.md**: User-facing features and usage
- **SKILL.md**: Skill behavior and workflow changes
- **Tool README**: Changes to Python tools
- **Code Comments**: Complex logic and algorithms
- **Docstrings**: All functions and classes

### Documentation Style

- Write in clear, concise language
- Use examples to illustrate concepts
- Include code snippets where helpful
- Keep documentation in sync with code
- Use proper Markdown formatting

### Example Documentation

Good:
```python
def calculate_time_estimate(distance_mi: float, elevation_gain_ft: float) -> dict:
    """Calculate hiking time estimates for three pacing levels.

    Uses Naismith's rule: 3 mph + 30 min per 1000 ft elevation gain.
    Returns slower of distance-based or elevation-based estimate.

    Args:
        distance_mi: One-way distance in miles
        elevation_gain_ft: Total elevation gain in feet

    Returns:
        Dict with 'fast', 'moderate', 'leisurely' times in hours
    """
```

## Project Structure

Understanding the project structure helps with contributions:

```
claude-mountaineering-skills/
├── .claude-plugin/          # Plugin metadata
│   ├── plugin.json         # Plugin configuration
│   └── marketplace.json    # Marketplace listing
├── skills/
│   └── route-researcher/   # Main skill
│       ├── SKILL.md        # Skill instructions
│       ├── examples/       # Example generated reports
│       └── tools/          # Python utilities
│           ├── src/        # Tool source code
│           ├── tests/      # Test suite
│           └── README.md   # Tool documentation
├── .github/
│   ├── workflows/          # CI/CD configuration
│   └── pull_request_template.md
├── .gitmessage             # Commit template
├── .releaserc.json         # Semantic-release config
├── CONTRIBUTING.md         # This file
└── README.md               # Main documentation
```

## Getting Help

If you need help:

- Check existing [Issues](https://github.com/dreamiurg/claude-mountaineering-skills/issues)
- Review [Claude Code documentation](https://docs.claude.com/claude-code)
- Look at [example reports](skills/route-researcher/examples/)
- Read the [skill documentation](skills/route-researcher/SKILL.md)

## Recognition

Contributors are recognized in:

- Git commit history
- Release notes (via Conventional Commits)
- Future contributors section (planned)

Thank you for contributing to make mountain route research faster and safer!
