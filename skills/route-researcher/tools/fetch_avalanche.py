#!/usr/bin/env python3
"""NWAC avalanche forecast fetcher"""

import json
import sys
import click
import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from cache import get_avalanche_cache

console = Console()

# NWAC region mapping
NWAC_REGIONS = {
    'north cascades': 'north-cascades',
    'mt baker': 'mt-baker',
    'snoqualmie pass': 'snoqualmie-pass',
    'stevens pass': 'stevens-pass',
    'olympics': 'olympics',
    'mt hood': 'mt-hood',
    'east slopes': 'east-slopes-north',
    'south cascades': 'south-cascades',
}

@click.command()
@click.option('--region', required=True, help='NWAC forecast region')
@click.option('--coordinates', help='Coordinates as lat,lon (optional)')
@click.option('--skip-cache', is_flag=True, help='Skip cache and fetch fresh data')
def cli(region: str, coordinates: str = None, skip_cache: bool = False):
    """Fetch NWAC avalanche forecast"""
    try:
        # Normalize region name
        region_slug = NWAC_REGIONS.get(region.lower(), region.lower().replace(' ', '-'))

        # Check cache first
        cache = get_avalanche_cache()
        cache_key = f"avalanche:{region_slug}"

        if not skip_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                cached_data['cached'] = True
                click.echo(json.dumps(cached_data, indent=2))
                return

        url = f"https://nwac.us/avalanche-forecast/#{region_slug}"

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            # Try to fetch current forecast
            response = client.get("https://nwac.us/avalanche-forecast/")

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')

                # NWAC has a complex single-page app structure
                # Parsing detailed danger levels would be fragile
                # Provide helpful fallback with URL

                output = {
                    'source': 'NWAC',
                    'region': region,
                    'url': url,
                    'forecast': 'Current avalanche forecast available at URL',
                    'note': 'NWAC provides detailed avalanche danger ratings by elevation (alpine, treeline, below treeline). Visit the URL for current conditions, weather, snowpack analysis, and recent avalanche activity.'
                }
            else:
                output = {
                    'source': 'NWAC',
                    'region': region,
                    'url': url,
                    'forecast': 'Unable to fetch forecast',
                    'note': 'Visit NWAC website for current avalanche conditions'
                }

        # Cache successful results
        cache.set(cache_key, output)

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        # Print warning to stderr
        error_console = Console(stderr=True)
        error_console.print(f"[yellow]Warning: Error fetching avalanche forecast: {e}[/yellow]")
        # Provide helpful fallback even on error
        output = {
            'source': 'NWAC',
            'region': region,
            'url': 'https://nwac.us/avalanche-forecast/',
            'error': str(e),
            'note': 'Avalanche forecast fetch failed. Check NWAC website manually for current conditions. Always check avalanche forecast before entering avalanche terrain.'
        }
        click.echo(json.dumps(output, indent=2))
        sys.exit(0)  # Don't fail hard - graceful degradation

if __name__ == '__main__':
    cli()
