# NHL Model Examples

This directory contains example scripts demonstrating how to use the NHL Model package.

## Examples

### 1. Basic Prediction (`basic_prediction.py`)
Demonstrates how to make basic game predictions using the pre-trained model.

```bash
python examples/basic_prediction.py
```

### 2. Train Custom Model (`train_custom_model.py`)
Shows how to train a custom model with your own parameters.

```bash
python examples/train_custom_model.py
```

### 3. Analyze Results (`analyze_results.py`)
Demonstrates how to analyze prediction results and calculate accuracy.

```bash
python examples/analyze_results.py
```

### 4. Poisson Distribution (`poisson_example.py`)
Shows how to use the Poisson distribution method for score prediction.

```bash
python examples/poisson_example.py
```

### 5. Clear Cache (`clear_cache.py`)
Utility to clear the API response cache.

```bash
python examples/clear_cache.py
```

## Prerequisites

Make sure you have installed the package:

```bash
pip install nhl_model
# Or in development mode:
pip install -e .
```

## Configuration

By default, model data is saved to your system's temp directory. You can configure this:

```bash
export NHL_MODEL_DIR=/path/to/your/data
```

For caching, the default cache directory is `~/.nhl_model_cache`. You can change this:

```bash
export NHL_MODEL_CACHE_DIR=/path/to/cache
```

## Notes

- Examples use cached API responses to avoid rate limiting
- Some examples require historical data to be downloaded first
- Prediction accuracy depends on the quality and recency of training data
