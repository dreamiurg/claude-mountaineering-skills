# Contributing to Mountaineering Skills

Thank you for your interest in contributing! This guide will help you get started.

## Quick Links

- [Report a bug](https://github.com/dreamiurg/claude-mountaineering-skills/issues/new)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [Semantic Versioning](https://semver.org/)

## Local Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude-mountaineering-skills.git
   cd claude-mountaineering-skills
   ```

2. **Symlink to Claude Plugins Directory**
   ```bash
   mkdir -p ~/.claude/plugins
   ln -s /path/to/claude-mountaineering-skills ~/.claude/plugins/mountaineering-skills

   # Verify
   ls -la ~/.claude/plugins/mountaineering-skills
   ```

3. **Restart Claude Code**
   ```bash
   # Close and restart Claude, then verify:
   claude
   > /plugin list
   ```

4. **Set Up Python Tools** (optional, for tool development)
   ```bash
   cd skills/route-researcher/tools
   uv venv && source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

5. **Configure Commit Template**
   ```bash
   git config commit.template .gitmessage
   ```

## Development Workflow

1. Create a branch: `git checkout -b your-feature-name`
2. Make changes (follow existing code style)
3. Test with multiple peaks and edge cases
4. Commit using [Conventional Commits](https://www.conventionalcommits.org/)
5. Push and create PR

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/). See [.gitmessage](.gitmessage) for examples.

**Triggers release:**
- `feat:` - New feature (minor bump)
- `fix:` - Bug fix (patch bump)
- `perf:` - Performance improvement (patch bump)
- `feat!:` or `fix!:` - Breaking change (major bump)

**No release:**
- `docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `build:`

**Format:**
```
<type>: <description>

[optional body]

[optional footer]
```

## Pull Requests

**Before submitting:**
- [ ] Code follows existing patterns
- [ ] Tests pass (run `pytest` if changing tools)
- [ ] Documentation updated
- [ ] PR title follows format: `type: description`
- [ ] Tested with multiple peaks

**PR title must use Conventional Commits format** - GitHub Action validates this.

See [.github/pull_request_template.md](.github/pull_request_template.md) for the PR template.

## Testing

**Manual testing:**
- Test multiple peak types (popular, obscure, different regions)
- Test edge cases (no matches, multiple matches, missing data)
- Verify report quality (all sections, working links, clean formatting)

**Python tools:**
```bash
cd skills/route-researcher/tools
pytest                                      # Run all tests
pytest --cov=src --cov-report=term-missing  # With coverage
pytest tests/test_cloudscrape.py -v         # Specific test
```

## Project Structure

```
claude-mountaineering-skills/
├── .claude-plugin/          # Plugin metadata
├── skills/route-researcher/ # Main skill
│   ├── SKILL.md            # Skill instructions
│   ├── examples/           # Example reports
│   └── tools/              # Python utilities
├── .github/workflows/      # CI/CD
├── .gitmessage             # Commit template
└── README.md               # Main docs
```

## Getting Help

- [Issues](https://github.com/dreamiurg/claude-mountaineering-skills/issues)
- [Example Reports](skills/route-researcher/examples/)
- [Skill Documentation](skills/route-researcher/SKILL.md)
- [Claude Code Docs](https://docs.claude.com/claude-code)

## What to Contribute

We welcome:
- Bug fixes
- New data source integrations
- Better error handling
- Route analysis improvements
- Documentation improvements
- Test coverage
- Python tool enhancements

Thank you for contributing!
