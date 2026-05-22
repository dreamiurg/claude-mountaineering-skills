#!/usr/bin/env python3
"""Fetch content from protected websites.

Default path: httpx with browser-like headers (handles most sites).
--render path: Patchright (stealth headless Chromium) for JS-rendered /
Cloudflare-challenged pages. Patchright installs its own Chromium lazily on
first --render use via `patchright install chromium`.

CLI contract (preserved):
  positional URL, --timeout seconds, HTML to stdout, exit 0 on failure.

# TODO: escalation ladder — nodriver (system Chrome, no download) or hosted
# Cloudflare-bypass API — add here if Patchright gets blocked.
"""

import json

import click
import httpx

_CHROMIUM_INSTALLED = False

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _fetch_with_render(url: str, timeout: int) -> str:
    """Fetch a JS-rendered page using Patchright (stealth Chromium).

    Installs Chromium on first call if not already installed.
    Raises on any failure — caller must handle gracefully.
    """
    try:
        from patchright.sync_api import sync_playwright
    except ImportError as e:
        raise ImportError("patchright is not installed. Run: uv sync") from e

    global _CHROMIUM_INSTALLED
    if not _CHROMIUM_INSTALLED:
        import subprocess

        proc = subprocess.run(
            ["patchright", "install", "chromium"],
            check=False,
            capture_output=True,
        )
        if proc.returncode == 0:
            _CHROMIUM_INSTALLED = True

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            return page.content()
        finally:
            browser.close()


@click.command()
@click.argument("url")
@click.option("--timeout", default=30, help="Request timeout in seconds")
@click.option("--render", is_flag=True, default=False, help="Use Patchright headless browser")
def cli(url: str, timeout: int, render: bool):
    """Fetch HTML content from a URL, optionally via headless browser."""
    if render:
        try:
            html = _fetch_with_render(url, timeout)
            click.echo(html, nl=False)
        except Exception as e:
            error_note = {
                "error": str(e),
                "note": f"Render fetch failed for {url}. Check the URL manually.",
                "url": url,
            }
            click.echo(json.dumps(error_note))
        return

    # Default: httpx with browser-like headers
    try:
        with httpx.Client(
            timeout=float(timeout), headers=_HEADERS, follow_redirects=True
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            click.echo(response.text, nl=False)
    except Exception as e:
        error_note = {
            "error": str(e),
            "note": f"HTTP fetch failed for {url}. Try --render for Cloudflare-protected pages.",
            "url": url,
        }
        click.echo(json.dumps(error_note))


if __name__ == "__main__":
    cli()
