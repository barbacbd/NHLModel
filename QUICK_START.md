# Quick Start Guide - NHL Model (Updated)

Welcome to the improved NHL Model! This guide will help you get started quickly.

## What's New? 🎉

- ✅ **API Caching** - No more rate limiting issues!
- ✅ **Cross-platform** - Works on Windows, macOS, and Linux
- ✅ **Example Scripts** - Learn by example
- ✅ **Better Error Handling** - Clear error messages
- ✅ **Pre-commit Hooks** - Maintain code quality automatically
- ✅ **100% Tests Passing** - Reliable and tested code

## Installation

### Basic Installation
```bash
pip install nhl_model
```

### Development Installation
```bash
git clone https://github.com/barbacbd/NHLModel.git
cd NHLModel
pip install -e '.[dev,tests]'
```

### Setup Pre-commit Hooks (Recommended for Contributors)
```bash
pre-commit install
```

## Configuration (Optional)

### Set Custom Data Directory
```bash
# Add to your ~/.bashrc or ~/.zshrc
export NHL_MODEL_DIR=~/nhl_data
```

### Set Custom Cache Directory
```bash
export NHL_MODEL_CACHE_DIR=~/.nhl_cache
```

## Quick Usage Examples

### 1. Predict Today's Games
```bash
nhl-predict ann
```

### 2. Predict Specific Date
```bash
nhl-predict date -d 15 -m 10 -y 2023
```

### 3. Use Poisson Distribution
```bash
nhl-predict poisson -y 2023
```

### 4. Predict Playoffs
```bash
# Specific round
nhl-predict playoffs -r 1 -y 2024

# Full playoffs
nhl-predict playoffs -r 0 -y 2024
```

### 5. Generate Dataset
```bash
nhl-predict generate -s 2020 -e 2023 -v new
```

## Running Examples

We've included several example scripts to help you learn:

### View Today's Games
```bash
python examples/basic_prediction.py
```

### Train Custom Model
```bash
python examples/train_custom_model.py
```

### Use Poisson Method
```bash
python examples/poisson_example.py
```

### Clear API Cache
```bash
python examples/clear_cache.py
```

## Common Tasks

### Clear Cache
If you're getting old data or want to free up space:
```bash
python examples/clear_cache.py
```

Or manually:
```bash
rm -rf ~/.nhl_model_cache/*
```

### Run Tests
```bash
pytest tests/
```

### Check Code Quality
```bash
make lint
```

## Troubleshooting

### Issue: "No module named 'nhl_model'"
**Solution**: Install the package
```bash
pip install -e .
```

### Issue: Rate limiting errors
**Solution**: The caching system should prevent this, but if you encounter it:
```bash
python examples/clear_cache.py  # Clear old cache
# Wait a few minutes
# Try again
```

### Issue: Permission denied on /tmp/nhl_model
**Solution**: Set a custom directory
```bash
export NHL_MODEL_DIR=~/nhl_data
```

### Issue: Tests failing
**Solution**: Ensure all dependencies are installed
```bash
pip install -e '.[tests]'
pytest tests/
```

## Documentation

- **Full Documentation**: See [README.md](README.md)
- **Contributor Guide**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **All Improvements**: See [IMPROVEMENTS.md](IMPROVEMENTS.md)
- **Quick Summary**: See [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)
- **Final Report**: See [FINAL_SUMMARY.md](FINAL_SUMMARY.md)

## API Caching Details

The model now caches API responses to prevent rate limiting:

- **Game data**: 30 minutes
- **Season data**: 1 hour
- **Standings**: 1 hour
- **Playoff data**: 1 hour

Cache location: `~/.nhl_model_cache/` (configurable via `NHL_MODEL_CACHE_DIR`)

## Model Performance

### Artificial Neural Network (ANN)
- **Training accuracy**: 92-98.5%
- **Prediction accuracy**: Varies by model configuration
- **Best for**: Detailed predictions with extensive training data

### Poisson Distribution
- **Accuracy**: ~55% (similar to coin flip)
- **Best for**: Quick predictions, probability distributions, score estimates
- **Advantage**: No training required

## Support

- **Issues**: [GitHub Issues](https://github.com/barbacbd/NHLModel/issues)
- **Discussions**: [GitHub Discussions](https://github.com/barbacbd/NHLModel/discussions)
- **Examples**: See `examples/` directory

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Run lint: `make lint`
6. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

**Enjoy predicting NHL games!** 🏒
