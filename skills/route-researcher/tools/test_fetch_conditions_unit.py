"""Unit tests for fetch_conditions constants/helpers (no network access)."""

from fetch_conditions import PEAKBAGGER_CMD


def test_peakbagger_cmd_bundles_patchright():
    """peakbagger-cli runs in its own uvx env and needs patchright to bypass
    Cloudflare; the command must request it with --with patchright."""
    assert "--with" in PEAKBAGGER_CMD, "PEAKBAGGER_CMD must pass --with patchright"
    assert PEAKBAGGER_CMD[PEAKBAGGER_CMD.index("--with") + 1] == "patchright"
    assert PEAKBAGGER_CMD.index("--with") < PEAKBAGGER_CMD.index("--from")
