#!/usr/bin/env python3
"""
File-based caching for route-researcher tools.

Provides TTL-based caching to avoid redundant API calls and improve performance.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


class Cache:
    """Simple file-based cache with TTL support."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: int = 21600):
        """
        Initialize cache.

        Args:
            cache_dir: Directory for cache files (default: tools/.cache/)
            ttl_seconds: Time-to-live in seconds (default: 6 hours = 21600)
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent / ".cache"

        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, key: str) -> str:
        """Generate cache key from string."""
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            timestamp = cache_data.get("timestamp", 0)
            current_time = time.time()

            # Check if expired
            if current_time - timestamp > self.ttl_seconds:
                # Clean up expired cache file
                cache_path.unlink()
                return None

            return cache_data.get("value")

        except (json.JSONDecodeError, OSError):
            # Corrupted cache file, remove it
            if cache_path.exists():
                cache_path.unlink()
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
        """
        cache_path = self._get_cache_path(key)

        cache_data = {"timestamp": time.time(), "value": value}

        try:
            with open(cache_path, "w") as f:
                json.dump(cache_data, f, indent=2)
        except (TypeError, OSError) as e:
            # Value not serializable or write error - don't fail, just skip caching
            pass

    def clear(self) -> None:
        """Clear all cache files."""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

    def clear_expired(self) -> int:
        """
        Clear expired cache files.

        Returns:
            Number of files removed
        """
        removed_count = 0
        current_time = time.time()

        if not self.cache_dir.exists():
            return 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                timestamp = cache_data.get("timestamp", 0)
                if current_time - timestamp > self.ttl_seconds:
                    cache_file.unlink()
                    removed_count += 1

            except (json.JSONDecodeError, OSError):
                # Corrupted file, remove it
                cache_file.unlink()
                removed_count += 1

        return removed_count


# Convenience functions for different TTL durations

def get_weather_cache() -> Cache:
    """Get cache instance for weather data (6 hour TTL)."""
    return Cache(ttl_seconds=6 * 3600)  # 6 hours


def get_avalanche_cache() -> Cache:
    """Get cache instance for avalanche data (6 hour TTL)."""
    return Cache(ttl_seconds=6 * 3600)  # 6 hours


def get_trip_report_cache() -> Cache:
    """Get cache instance for trip reports (24 hour TTL)."""
    return Cache(ttl_seconds=24 * 3600)  # 24 hours


def get_route_description_cache() -> Cache:
    """Get cache instance for route descriptions (7 day TTL)."""
    return Cache(ttl_seconds=7 * 24 * 3600)  # 7 days


if __name__ == "__main__":
    # Basic usage example
    cache = Cache()

    # Store value
    cache.set("test_key", {"data": "test_value"})

    # Retrieve value
    value = cache.get("test_key")
    print(f"Cached value: {value}")

    # Clear all cache
    cache.clear()
    print("Cache cleared")

    # Example with weather cache
    weather_cache = get_weather_cache()
    weather_cache.set("mt_baker_forecast", {"temp": 45, "conditions": "clear"})
    forecast = weather_cache.get("mt_baker_forecast")
    print(f"Weather forecast: {forecast}")
