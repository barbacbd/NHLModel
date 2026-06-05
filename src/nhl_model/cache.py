"""
API response caching module for NHL Model.

This module provides caching functionality to reduce API calls to the NHL API
and avoid rate limiting issues.
"""
import os
from functools import wraps
from hashlib import md5
from json import dumps, loads
from pathlib import Path
from time import time
from typing import Optional, Callable, Any


# Cache directory location
CACHE_DIR = os.getenv('NHL_MODEL_CACHE_DIR',
                      os.path.join(os.path.expanduser('~'), '.nhl_model_cache'))


def get_cache_path(cache_key: str) -> Path:
    """Get the file path for a cache key.

    Args:
        cache_key: Unique identifier for the cached content

    Returns:
        Path object for the cache file
    """
    cache_dir = Path(CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    # Use MD5 hash to create safe filename
    filename = md5(cache_key.encode()).hexdigest() + '.json'
    return cache_dir / filename


def is_cache_valid(cache_file: Path, ttl_seconds: int) -> bool:
    """Check if a cache file exists and is still valid.

    Args:
        cache_file: Path to the cache file
        ttl_seconds: Time-to-live in seconds

    Returns:
        True if cache exists and is not expired
    """
    if not cache_file.exists():
        return False

    # Check if cache has expired
    file_age = time() - cache_file.stat().st_mtime
    return file_age < ttl_seconds


def get_from_cache(cache_key: str, ttl_seconds: int = 3600) -> Optional[Any]:
    """Retrieve data from cache if valid.

    Args:
        cache_key: Unique identifier for the cached content
        ttl_seconds: Time-to-live in seconds (default: 1 hour)

    Returns:
        Cached data if valid, None otherwise
    """
    cache_file = get_cache_path(cache_key)

    if not is_cache_valid(cache_file, ttl_seconds):
        return None

    try:
        with open(cache_file, 'r') as f:
            cached_data = loads(f.read())
            return cached_data.get('data')
    except (IOError, ValueError):
        return None


def save_to_cache(cache_key: str, data: Any) -> None:
    """Save data to cache.

    Args:
        cache_key: Unique identifier for the cached content
        data: Data to cache (must be JSON-serializable)
    """
    cache_file = get_cache_path(cache_key)

    try:
        with open(cache_file, 'w') as f:
            cache_data = {
                'timestamp': time(),
                'data': data
            }
            f.write(dumps(cache_data))
    except (IOError, TypeError):
        # Fail silently - caching is optional
        pass


def clear_cache() -> int:
    """Clear all cached files.

    Returns:
        Number of files removed
    """
    cache_dir = Path(CACHE_DIR)
    if not cache_dir.exists():
        return 0

    count = 0
    for cache_file in cache_dir.glob('*.json'):
        try:
            cache_file.unlink()
            count += 1
        except OSError:
            pass

    return count


def cached_request(ttl_seconds: int = 3600) -> Callable:
    """Decorator to cache function results based on arguments.

    Args:
        ttl_seconds: Time-to-live in seconds (default: 1 hour)

    Returns:
        Decorated function with caching

    Example:
        @cached_request(ttl_seconds=1800)
        def get_game_data(game_id):
            response = requests.get(f"https://api.nhle.com/game/{game_id}")
            return response.json()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{dumps(args)}:{dumps(kwargs, sort_keys=True)}"

            # Try to get from cache
            cached_data = get_from_cache(cache_key, ttl_seconds)
            if cached_data is not None:
                return cached_data

            # Call function and cache result
            result = func(*args, **kwargs)
            save_to_cache(cache_key, result)

            return result

        return wrapper
    return decorator
