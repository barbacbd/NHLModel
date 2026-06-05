# Contributing to NHL Model

Thank you for your interest in contributing to the NHL Model project!

## Development Setup

### Prerequisites

- Python 3.8 - 3.12
- pip (Python package manager)
- git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/barbacbd/NHLModel.git
cd NHLModel
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode with test dependencies:
```bash
pip install -e '.[tests,lint]'
```

## Configuration

### Data Directory

By default, the model saves data to your system's temp directory. You can configure this:

```bash
# Set custom data directory
export NHL_MODEL_DIR=/path/to/your/nhl_data

# Run the model
nhl-predict ann
```

This is especially useful if you want to:
- Persist data across system restarts
- Use a specific location for easier access
- Share data across multiple environments

## Running Tests

### Run all tests:
```bash
make test
pytest tests/
```

### Run specific test file:
```bash
pytest tests/test_ann.py -v
```

### Run with coverage:
```bash
pytest tests/ --cov=nhl_model --cov-report=html
```

Coverage reports will be in `htmlcov/index.html`.

## Code Quality

### Linting

We use pylint for code quality checks:

```bash
make lint
# Or manually:
pylint src/nhl_model/ --rcfile .pylintrc
```

### Code Style Guidelines

- Follow PEP 8 style guidelines
- Add type hints to new functions
- Write comprehensive docstrings for public functions
- Use specific exception types (never bare `except:`)
- Add unit tests for new features

## Project Structure

```
NHLModel/
├── src/nhl_model/          # Main package code
│   ├── ann.py              # Artificial Neural Network implementation
│   ├── dataset.py          # Data fetching and parsing
│   ├── poisson.py          # Poisson distribution predictions
│   ├── features.py         # Feature selection algorithms
│   ├── playoffs.py         # Playoff prediction logic
│   ├── event.py            # Game event classes
│   ├── team.py             # Team data structures
│   ├── standings.py        # NHL standings fetcher
│   ├── enums.py            # Enumerations
│   └── exec.py             # CLI entry point
├── tests/                  # Test files
├── pyproject.toml          # Package configuration
├── Makefile               # Common tasks
└── README.md              # Main documentation
```

## Making Changes

### Workflow

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and add tests

3. Run tests and linting:
```bash
make test
make lint
```

4. Commit your changes:
```bash
git add .
git commit -m "Description of changes"
```

5. Push and create a pull request:
```bash
git push origin feature/your-feature-name
```

### Commit Message Guidelines

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Keep the first line under 72 characters
- Reference issue numbers when applicable

Examples:
- `Fix exception handling in dataset.py`
- `Add type hints to poisson module`
- `Update dependencies to fix security issue #123`

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_<module>.py`
- Use descriptive test method names: `test_<functionality>_<scenario>`
- Use mock data from `tests/MockData.json` when possible
- Test both success and failure cases

Example:
```python
def test_parse_power_play_data_valid(self):
    """Test parsing valid power play data."""
    result = _parsePPDataNew("2/5")
    self.assertEqual(result["powerPlayGoals"], 2)
    self.assertEqual(result["powerPlayOpportunities"], 5)

def test_parse_power_play_data_invalid(self):
    """Test parsing invalid power play data."""
    result = _parsePPDataNew("invalid")
    self.assertEqual(result["powerPlayGoals"], 0)
```

## Common Issues

### Tests Failing

If tests fail after your changes:
1. Check if the failure is related to your changes
2. Review the test output carefully
3. Run individual tests for debugging: `pytest tests/test_file.py::TestClass::test_method -v`

### Import Errors

If you get import errors:
1. Make sure you installed in editable mode: `pip install -e .`
2. Verify your virtual environment is activated
3. Check that all dependencies are installed: `pip install -e '.[tests]'`

### API Rate Limiting

The NHL API may rate limit requests. If you encounter this:
- Wait a few minutes between requests
- Use cached data when testing
- Consider implementing request throttling for new features

## Need Help?

- Create an issue on GitHub: https://github.com/barbacbd/NHLModel/issues
- Check existing issues for similar problems
- Review the main README.md for usage instructions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
