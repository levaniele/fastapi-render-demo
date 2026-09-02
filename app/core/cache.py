"""
In-memory caching infrastructure for the Badminton360 API.
Provides decorator-based caching with TTL and automatic invalidation.
"""

import hashlib
import logging
import threading
from functools import wraps
from typing import Any, Callable, Optional

from cachetools import TTLCache

from app.core.cache_config import CACHE_CONFIGS, get_cache_maxsize, get_cache_ttl

logger = logging.getLogger(__name__)

# Thread-safe lock for cache operations
_cache_lock = threading.RLock()

# Cache instances by category
# These will be initialized after settings are available
CACHES: dict[str, TTLCache] = {}

# Cache statistics
CACHE_STATS = {
    "hits": 0,
    "misses": 0,
    "evictions": 0,
}


def initialize_caches(settings) -> None:
    """
    Initialize cache instances with settings from environment.
    Should be called once on application startup.

    Args:
        settings: Application settings object
    """
    global CACHES

    if CACHES:
        # Already initialized
        return

    for category in CACHE_CONFIGS.keys():
        ttl = get_cache_ttl(category, settings)
        maxsize = get_cache_maxsize(category)
        CACHES[category] = TTLCache(maxsize=maxsize, ttl=ttl)
        logger.info(f"Initialized cache '{category}': maxsize={maxsize}, ttl={ttl}s")


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate deterministic cache key from function name and arguments.

    Args:
        func_name: Name of the function being cached
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Build key parts
    key_parts = [func_name]

    # Add positional args (skip database session objects)
    for arg in args:
        # Skip SQLAlchemy Session objects
        if hasattr(arg, '__class__') and arg.__class__.__name__ == 'Session':
            continue
        key_parts.append(str(arg))

    # Add keyword args (sorted for consistency)
    for k, v in sorted(kwargs.items()):
        if k == 'db':
            # Skip db session
            continue
        key_parts.append(f"{k}={v}")

    # Join and hash if too long
    key = ":".join(key_parts)
    if len(key) > 200:
        key_hash = hashlib.md5(key.encode()).hexdigest()
        key = f"{func_name}:{key_hash}"

    return key


def cached(category: str = "static_data"):
    """
    Decorator for caching function results with TTL.

    Args:
        category: Cache category (live_data, tournament_data, static_data, reference_data)

    Usage:
        @cached(category="tournament_data")
        def get_tournament_stats(db: Session, slug: str):
            # ... expensive query ...

    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Import here to avoid circular dependency
            from app.core.config import get_settings
            settings = get_settings()

            # Check if caching is enabled
            if not settings.cache_enabled:
                return func(*args, **kwargs)

            # Ensure caches are initialized
            if not CACHES:
                initialize_caches(settings)

            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, args, kwargs)

            # Get cache instance
            cache = CACHES.get(category)
            if cache is None:
                logger.warning(f"Unknown cache category: {category}. Available: {list(CACHES.keys())}")
                return func(*args, **kwargs)

            # Try to get from cache
            with _cache_lock:
                if cache_key in cache:
                    CACHE_STATS["hits"] += 1
                    logger.debug(f"Cache HIT: {cache_key}")
                    return cache[cache_key]

            # Cache miss - execute function
            CACHE_STATS["misses"] += 1
            logger.debug(f"Cache MISS: {cache_key}")

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error executing {func.__name__}: {e}")
                raise

            # Store in cache
            with _cache_lock:
                cache[cache_key] = result

            return result

        return wrapper
    return decorator


def invalidate_by_pattern(pattern: str) -> int:
    """
    Invalidate cache keys matching pattern.

    Args:
        pattern: Pattern to match in cache keys

    Returns:
        Number of cache entries invalidated
    """
    count = 0
    with _cache_lock:
        for cache in CACHES.values():
            keys_to_remove = [k for k in cache.keys() if pattern in k]
            for key in keys_to_remove:
                del cache[key]
                count += 1

    logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
    return count


def invalidate_tournament_cache(slug: str) -> None:
    """
    Invalidate all tournament-related caches for a specific slug.

    Args:
        slug: Tournament slug
    """
    patterns = [
        "get_tournament_by_id:",
        f"get_tournament_stats:{slug}",
        f"get_tournament_matches:{slug}",
        f"get_tournament_standings:{slug}",
        f"get_tournament_teams:{slug}",
        f"get_tournament_players:{slug}",
        f"get_tournament_staff:{slug}",
        f"get_tournament_winners:{slug}",
    ]
    total = 0
    for pattern in patterns:
        total += invalidate_by_pattern(pattern)

    # Also invalidate tournament list
    total += invalidate_by_pattern("get_all_tournaments")
    total += invalidate_by_pattern("search_tournaments")

    logger.info(f"Invalidated {total} tournament cache entries for slug: {slug}")


def invalidate_player_cache(player_id: Optional[int] = None, slug: Optional[str] = None) -> None:
    """
    Invalidate player-related caches.

    Args:
        player_id: Player ID (optional)
        slug: Player slug (optional)
    """
    if player_id:
        invalidate_by_pattern(f"player_id={player_id}")
        invalidate_by_pattern(f":{player_id}")

    if slug:
        invalidate_by_pattern(f"get_player_by_slug:{slug}")

    # Invalidate player lists
    invalidate_by_pattern("get_all_players")
    invalidate_by_pattern("get_players_by_gender")


def invalidate_club_cache(club_id: Optional[int] = None, slug: Optional[str] = None) -> None:
    """
    Invalidate club-related caches.

    Args:
        club_id: Club ID (optional)
        slug: Club slug (optional)
    """
    if club_id:
        invalidate_by_pattern(f"club_id={club_id}")
        invalidate_by_pattern(f":{club_id}")

    if slug:
        invalidate_by_pattern(f"get_club_by_slug:{slug}")

    # Invalidate club lists
    invalidate_by_pattern("get_all_clubs")


def invalidate_rankings_cache() -> None:
    """
    Invalidate all rankings-related caches.
    Should be called after rankings recalculation.
    """
    patterns = [
        "get_global_rankings",
        "get_rankings_by_category",
        "get_player_rankings",
        "get_tournament_rankings",
        "get_top_players",
    ]
    total = 0
    for pattern in patterns:
        total += invalidate_by_pattern(pattern)

    logger.info(f"Invalidated {total} rankings cache entries")


def clear_all_caches() -> None:
    """
    Clear all caches (nuclear option).
    Should only be used for manual cache clearing or emergencies.
    """
    with _cache_lock:
        for cache in CACHES.values():
            cache.clear()
        CACHE_STATS["hits"] = 0
        CACHE_STATS["misses"] = 0
        CACHE_STATS["evictions"] = 0

    logger.warning("All caches cleared")


def get_cache_stats() -> dict:
    """
    Get cache statistics for monitoring.

    Returns:
        Dictionary with cache statistics
    """
    with _cache_lock:
        total_keys = sum(len(cache) for cache in CACHES.values())
        total_requests = CACHE_STATS["hits"] + CACHE_STATS["misses"]
        hit_rate = (CACHE_STATS["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": CACHE_STATS["hits"],
            "misses": CACHE_STATS["misses"],
            "total_keys": total_keys,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "caches": {
                category: {
                    "keys": len(cache),
                    "maxsize": cache.maxsize,
                    "ttl": cache.ttl if hasattr(cache, 'ttl') else None,
                }
                for category, cache in CACHES.items()
            }
        }
