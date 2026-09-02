"""
Cache configuration for the Badminton360 API.
Defines cache categories with TTL and size limits.
"""

from typing import TypedDict


class CacheConfig(TypedDict):
    """Configuration for a cache category."""
    ttl: int
    maxsize: int
    description: str


# Cache configurations by category
# TTL values can be overridden via environment variables
CACHE_CONFIGS: dict[str, CacheConfig] = {
    # HIGH VOLATILITY - Short TTL (1 minute)
    # For real-time data that updates frequently during matches
    "live_data": {
        "ttl": 60,  # 1 minute
        "maxsize": 100,
        "description": "Live match data, real-time rally statistics",
    },

    # MEDIUM VOLATILITY - Medium TTL (5 minutes)
    # For tournament data that updates during active tournaments
    "tournament_data": {
        "ttl": 300,  # 5 minutes
        "maxsize": 500,
        "description": "Tournament stats, standings, matches during active tournaments",
    },

    # LOW VOLATILITY - Long TTL (1 hour)
    # For data that rarely changes
    "static_data": {
        "ttl": 3600,  # 1 hour
        "maxsize": 1000,
        "description": "Player lists, club lists, tournament details, team rosters",
    },

    # VERY LOW VOLATILITY - Very Long TTL (6 hours)
    # For historical and reference data
    "reference_data": {
        "ttl": 21600,  # 6 hours
        "maxsize": 2000,
        "description": "Historical data, rankings, completed tournament information",
    },
}


def get_cache_ttl(category: str, settings) -> int:
    """
    Get the TTL for a cache category, with environment variable override.

    Args:
        category: Cache category name (live_data, tournament_data, static_data, reference_data)
        settings: Application settings object

    Returns:
        TTL in seconds
    """
    # Map category to settings field
    ttl_map = {
        "live_data": getattr(settings, "cache_live_data_ttl", CACHE_CONFIGS["live_data"]["ttl"]),
        "tournament_data": getattr(settings, "cache_tournament_data_ttl", CACHE_CONFIGS["tournament_data"]["ttl"]),
        "static_data": getattr(settings, "cache_static_data_ttl", CACHE_CONFIGS["static_data"]["ttl"]),
        "reference_data": getattr(settings, "cache_reference_data_ttl", CACHE_CONFIGS["reference_data"]["ttl"]),
    }

    return ttl_map.get(category, CACHE_CONFIGS.get(category, {}).get("ttl", 3600))


def get_cache_maxsize(category: str) -> int:
    """
    Get the maximum size for a cache category.

    Args:
        category: Cache category name

    Returns:
        Maximum number of items in cache
    """
    return CACHE_CONFIGS.get(category, {}).get("maxsize", 1000)
