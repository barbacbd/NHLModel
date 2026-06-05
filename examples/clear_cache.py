#!/usr/bin/env python3
"""
Clear API response cache.

This utility clears the cached NHL API responses.
"""
import os
import sys

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nhl_model.cache import clear_cache, CACHE_DIR


def main():
    """Clear the API cache."""
    print("=" * 60)
    print("NHL Model - Clear Cache Utility")
    print("=" * 60)
    print()

    print(f"Cache directory: {CACHE_DIR}")
    print()

    if not os.path.exists(CACHE_DIR):
        print("Cache directory does not exist. Nothing to clear.")
        return

    # Get cache size
    cache_files = list(os.listdir(CACHE_DIR))
    num_files = len([f for f in cache_files if f.endswith('.json')])

    if num_files == 0:
        print("Cache is already empty.")
        return

    print(f"Found {num_files} cached file(s)")
    print()

    response = input("Clear cache? (y/n): ").strip().lower()

    if response == 'y':
        removed = clear_cache()
        print(f"\nCleared {removed} cached file(s)")
        print("Cache cleared successfully!")
    else:
        print("\nCache not cleared.")


if __name__ == "__main__":
    main()
