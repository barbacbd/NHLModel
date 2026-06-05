#!/usr/bin/env python3
"""
Train a custom NHL prediction model example.

This script demonstrates how to generate a dataset and train a custom model.
"""
import os
import sys

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nhl_model.dataset import generateDataset
from nhl_model.ann import findFiles


def main():
    """Run custom model training example."""
    print("=" * 60)
    print("NHL Model - Custom Training Example")
    print("=" * 60)
    print()

    # Configuration
    start_year = 2020
    end_year = 2023
    api_version = 'new'

    print("Training Configuration:")
    print(f"  Years: {start_year} - {end_year}")
    print(f"  API Version: {api_version}")
    print()

    # Step 1: Generate dataset
    print("Step 1: Generating dataset...")
    print(f"This will download game data from {start_year} to {end_year}")
    print("Note: This may take several minutes depending on the year range.")
    print()

    try:
        # Find and generate files
        valid_files = findFiles(api_version, start_year, end_year, playoffs=False)

        if not valid_files:
            print("No files found. Generating new dataset...")
            generateDataset(
                api_version,
                start_year,
                end_year,
                validFiles=[],
                dropScoreData=False,
                playoffs=False
            )
            print("Dataset generated successfully!")
        else:
            print(f"Found {len(valid_files)} existing file(s)")
            print("Using existing dataset.")

        print()
        print("=" * 60)
        print("Dataset ready!")
        print()
        print("Step 2: To train the model, run:")
        print("  nhl-predict ann")
        print()
        print("You will be prompted for:")
        print("  - Dataset file to use")
        print("  - Comparison function (DIRECT or AVERAGES)")
        print("  - Batch size (recommended: 32)")
        print("  - Number of epochs (recommended: 50-100)")
        print("  - Feature selection method (mRMR or F1 Scores)")
        print()
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have internet connection for API access.")
        sys.exit(1)


if __name__ == "__main__":
    main()
