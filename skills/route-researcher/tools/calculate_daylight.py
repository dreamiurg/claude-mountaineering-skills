#!/usr/bin/env python3
"""Sunrise/sunset daylight calculator"""

import json
import sys
from datetime import datetime
import click
from astral import LocationInfo
from astral.sun import sun
from rich.console import Console

console = Console()

@click.command()
@click.option('--date', required=True, help='Date as YYYY-MM-DD')
@click.option('--coordinates', required=True, help='Coordinates as lat,lon')
def cli(date: str, coordinates: str):
    """Calculate sunrise, sunset, and daylight hours"""
    try:
        lat, lon = map(float, coordinates.split(','))
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        # Create location
        location = LocationInfo(latitude=lat, longitude=lon)

        # Calculate sun times
        s = sun(location.observer, date=date_obj, tzinfo='America/Los_Angeles')

        sunrise_time = s['sunrise']
        sunset_time = s['sunset']

        # Calculate daylight hours
        daylight = sunset_time - sunrise_time
        daylight_hours = daylight.total_seconds() / 3600

        output = {
            'date': date,
            'coordinates': {'latitude': lat, 'longitude': lon},
            'sunrise': sunrise_time.strftime('%H:%M'),
            'sunset': sunset_time.strftime('%H:%M'),
            'daylight_hours': round(daylight_hours, 2),
            'note': 'Times in Pacific timezone'
        }

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        error_console = Console(stderr=True)
        error_console.print(f"[red]Error calculating daylight: {e}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    cli()
