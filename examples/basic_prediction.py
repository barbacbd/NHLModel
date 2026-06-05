#!/usr/bin/env python3
"""
Basic NHL game prediction example.

This script demonstrates how to use the NHL Model to predict today's games.
"""
import os
import sys
from datetime import datetime

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nhl_model.ann import findTodaysGames, execAnn


def main():
    """Run basic prediction example."""
    print("=" * 60)
    print("NHL Model - Basic Prediction Example")
    print("=" * 60)
    print()

    # Find today's games
    print(f"Looking for games on {datetime.now().strftime('%Y-%m-%d')}...")
    games = findTodaysGames()

    if not games:
        print("No games scheduled for today.")
        print("\nTry running predictions for a specific date:")
        print("  nhl-predict date -d 15 -m 10 -y 2023")
        return

    print(f"\nFound {len(games['games'])} game(s):\n")

    for game in games['games']:
        home_team = game.get('homeTeam', {}).get('name', {}).get('default', 'Unknown')
        away_team = game.get('awayTeam', {}).get('name', {}).get('default', 'Unknown')
        print(f"  {away_team} @ {home_team}")

    print("\n" + "=" * 60)
    print("To make predictions, run:")
    print("  nhl-predict ann")
    print("=" * 60)
    print("\nNote: This requires a trained model in your NHL_MODEL_DIR")
    print(f"Current model directory: {os.getenv('NHL_MODEL_DIR', 'System temp directory')}")


if __name__ == "__main__":
    main()
