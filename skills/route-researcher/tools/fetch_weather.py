#!/usr/bin/env python3
"""Mountain weather forecast fetcher"""

import json
import sys
import click
import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from cache import get_weather_cache

console = Console()

@click.command()
@click.option('--peak-name', required=True, help='Peak name for weather lookup')
@click.option('--coordinates', required=True, help='Coordinates as lat,lon')
@click.option('--skip-cache', is_flag=True, help='Skip cache and fetch fresh data')
def cli(peak_name: str, coordinates: str, skip_cache: bool = False):
    """Fetch mountain weather forecast"""
    try:
        lat, lon = coordinates.split(',')

        # Check cache first
        cache = get_weather_cache()
        cache_key = f"weather:{peak_name}:{lat},{lon}"

        if not skip_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                # Add cache hit indicator
                cached_data['cached'] = True
                click.echo(json.dumps(cached_data, indent=2))
                return

        # Try Mountain-Forecast.com
        # Format: mountain-forecast.com/peaks/Peak-Name
        peak_slug = peak_name.lower().replace(' ', '-').replace('.', '').replace('mt', 'mount')
        url = f"https://www.mountain-forecast.com/peaks/{peak_slug}"

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')

                # Try to extract forecast data
                # Mountain-Forecast has complex HTML, so we'll provide a helpful fallback
                forecast_summary = []

                # Look for forecast table or summary text
                # The site uses JavaScript-heavy rendering, so parsing may be limited
                forecast_headers = soup.select('.forecast__table-days-name')
                if forecast_headers:
                    for header in forecast_headers[:5]:  # Next 5 days
                        day_text = header.get_text(strip=True)
                        if day_text:
                            forecast_summary.append(day_text)

                # If we got some data, great; otherwise provide helpful fallback
                if forecast_summary:
                    output = {
                        'source': 'Mountain-Forecast.com',
                        'url': url,
                        'forecast': forecast_summary,
                        'note': 'Visit URL for detailed multi-day forecast with temperatures, wind, and precipitation'
                    }
                else:
                    # Fallback - still success but direct user to URL
                    output = {
                        'source': 'Mountain-Forecast.com',
                        'url': url,
                        'forecast': ['Detailed forecast available at URL'],
                        'note': 'Mountain-Forecast provides comprehensive forecasts at summit, mid-mountain, and base elevations. Visit the URL for full details.'
                    }
            else:
                # Peak not found or error - provide fallback
                output = {
                    'source': 'Mountain-Forecast.com',
                    'url': url,
                    'forecast': ['Peak may not be in Mountain-Forecast database'],
                    'note': f'Try searching Mountain-Forecast.com manually for "{peak_name}" or check alternative weather sources'
                }

        # Cache successful results
        cache.set(cache_key, output)

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        # Print warning to stderr using Console's stderr parameter at init
        error_console = Console(stderr=True)
        error_console.print(f"[yellow]Warning: Error fetching weather: {e}[/yellow]")
        # Provide helpful fallback even on error
        output = {
            'source': 'Mountain-Forecast.com',
            'url': f'https://www.mountain-forecast.com/peaks/{peak_name.lower().replace(" ", "-")}',
            'forecast': [],
            'error': str(e),
            'note': 'Weather fetch failed. Check Mountain-Forecast.com or NOAA point forecast manually.'
        }
        click.echo(json.dumps(output, indent=2))
        sys.exit(0)  # Don't fail hard on weather errors - graceful degradation

if __name__ == '__main__':
    cli()
