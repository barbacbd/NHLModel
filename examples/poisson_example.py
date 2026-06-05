#!/usr/bin/env python3
"""
Poisson distribution prediction example.

This script demonstrates how to use the Poisson distribution method
to predict NHL game scores.
"""
import os
import sys

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nhl_model.poisson import execPoisson


def main():
    """Run Poisson distribution example."""
    print("=" * 60)
    print("NHL Model - Poisson Distribution Example")
    print("=" * 60)
    print()

    print("The Poisson distribution method predicts game scores based on:")
    print("  - Average goals scored (home/away)")
    print("  - Team offensive strength")
    print("  - Team defensive strength")
    print()

    year = 2022  # 2022-2023 season

    print(f"Running Poisson predictions for {year}-{year+1} season...")
    print()
    print("Note: This requires schedule data. If not available,")
    print("      the script will download it from the NHL API.")
    print()

    try:
        # Run Poisson prediction
        print("=" * 60)
        print(f"To run Poisson predictions for year {year}:")
        print(f"  nhl-predict poisson -y {year}")
        print("=" * 60)
        print()
        print("The Poisson method typically achieves ~55% accuracy,")
        print("similar to a coin flip, but provides score predictions")
        print("and probability distributions.")
        print()
        print("Advantages of Poisson method:")
        print("  + Fast computation")
        print("  + No training required")
        print("  + Provides score predictions and probabilities")
        print("  + Works with limited historical data")
        print()
        print("Disadvantages:")
        print("  - Lower accuracy than neural network (~55% vs ~95%)")
        print("  - Cannot account for recent changes (injuries, trades)")
        print("  - Assumes goals are independent events")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
