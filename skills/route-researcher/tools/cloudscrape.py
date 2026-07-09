#!/usr/bin/env python3
"""Fetch content from protected websites.

Default path: httpx with browser-like headers (handles most sites).
--render path: Patchright (real Chrome when available, bundled Chromium as
fallback; headless by default) for JS-rendered / Cloudflare-challenged pages.
Prefers real Chrome channel for best Cloudflare
bypass; falls back to bundled Chromium. Waits out Cloudflare challenges up to
30 s before returning. Patchright installs its own Chromium lazily on first
--render use via `patchright install chromium`.

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

_CHALLENGE_MARKERS = (
    "just a moment",
    "attention required",
    "checking your browser",
    "verify you are human",
    "enable javascript and cookies",
)


def _looks_like_challenge(title: str, text: str) -> bool:
    """True if the page looks like a Cloudflare/JS interstitial, not real content."""
    blob = f"{title or ''}\n{(text or '')[:800]}".lower()
    return any(marker in blob for marker in _CHALLENGE_MARKERS)


def _launch_browser(p, headed: bool):
    """Launch real Chrome (best Cloudflare bypass); fall back to bundled Chromium."""
    launch_kwargs = {
        "headless": not headed,
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    try:
        return p.chromium.launch(channel="chrome", **launch_kwargs)
    except Exception:
        # Broad by design: any Chrome-channel launch failure (not installed,
        # permissions, lib mismatch) falls back to Patchright's bundled Chromium
        # so the best-effort scraper still runs rather than aborting.
        return p.chromium.launch(**launch_kwargs)


def _fetch_with_render(url: str, timeout: int, headed: bool = False) -> str:
    """Fetch a JS-rendered page using Patchright (real Chrome when available).

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
        browser = _launch_browser(p, headed)
        try:
            page = browser.new_page()
            page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            # Wait out a Cloudflare / JS challenge (capped at 30s of the timeout).
            deadline_ms = min(timeout, 30) * 1000
            waited_ms = 0
            step_ms = 2000
            while waited_ms < deadline_ms:
                info = page.evaluate(
                    "() => ({title: document.title,"
                    " text: document.body ? document.body.innerText : ''})"
                )
                if not _looks_like_challenge(info["title"], info["text"]):
                    break
                page.wait_for_timeout(step_ms)
                waited_ms += step_ms
            html = page.content()
            info = page.evaluate(
                "() => ({title: document.title,"
                " text: document.body ? document.body.innerText : ''})"
            )
            if _looks_like_challenge(info["title"], info["text"]):
                advice = (
                    "page may be inaccessible; document the gap"
                    if headed
                    else "try --render --headed"
                )
                raise RuntimeError(
                    f"Cloudflare challenge not resolved within {min(timeout, 30)}s — {advice}"
                )
            return html
        finally:
            browser.close()


@click.command()
@click.argument("url")
@click.option("--timeout", default=30, help="Request timeout in seconds")
@click.option(
    "--render",
    is_flag=True,
    default=False,
    help="Use a Patchright browser (real Chrome; waits out Cloudflare challenges)",
)
@click.option(
    "--headed",
    is_flag=True,
    default=False,
    help="Run the render browser headed (more reliable vs Cloudflare; needs a display)",
)
def cli(url: str, timeout: int, render: bool, headed: bool):
    """Fetch HTML content from a URL, optionally via browser (headless by default; --headed disables headless mode)."""
    if headed and not render:
        click.echo(json.dumps({"error": "--headed requires --render", "url": url}))
        return
    if render:
        try:
            html = _fetch_with_render(url, timeout, headed)
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
