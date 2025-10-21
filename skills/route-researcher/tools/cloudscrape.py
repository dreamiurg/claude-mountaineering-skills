#!/usr/bin/env python3
"""Fetch content from Cloudflare-protected websites using cloudscraper"""

import sys
import click
import cloudscraper
from rich.console import Console

console = Console(stderr=True)

@click.command()
@click.argument('url')
@click.option('--timeout', default=30, help='Request timeout in seconds')
def cli(url: str, timeout: int):
    """Fetch HTML content from Cloudflare-protected URL"""
    try:
        # Create scraper instance
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'darwin',
                'desktop': True
            }
        )
        
        # Fetch the page
        response = scraper.get(url, timeout=timeout)
        response.raise_for_status()
        
        # Output HTML to stdout
        print(response.text)
        
    except Exception as e:
        console.print(f"[red]Error fetching URL: {e}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    cli()
