# EntraSim Test Suite

This directory contains comprehensive tests for the EntraSim project, including unit tests, integration tests, and end-to-end scenarios that exercise all functionality described in the EntraSim End-to-End Demo Guide.

## Test Structure

```
tests/
├── __init__.py                    # Test package initialization
├── conftest.py                    # Pytest configuration and shared fixtures
├── utils.py                       # Test utility functions and helpers
├── README.md                      # This file
├── fixtures/                      # Test data and fixtures
│   ├── __init__.py
│   ├── test_company.json         # Small test company for faster testing
│   ├── minimal_company.json      # Minimal valid company configuration
│   └── invalid_company.json      # Invalid data for error testing
├── unit/                          # Unit tests for individual modules
│   ├── __init__.py
│   ├── test_config.py            # Configuration management tests
│   ├── test_models.py            # Pydantic model validation tests
│   ├── test_core.py              # Core business logic tests
│   ├── test_cli.py               # CLI interface tests
│   └── test_azure_client.py      # Azure client tests with mocking
└── integration/                   # Integration tests
    ├── __init__.py
    └── test_end_to_end.py         # End-to-end workflow tests
```

## Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests that don't require external dependencies:

- **Configuration Tests** (`test_config.py`): Test environment variable loading, credential validation, and configuration management
- **Model Tests** (`test_models.py`): Test Pydantic model validation, company description parsing, and simulation plan generation
- **Core Logic Tests** (`test_core.py`): Test business logic, file parsing, plan generation, and error handling
- **CLI Tests** (`test_cli.py`): Test command-line interface, argument parsing, and user interactions
- **Azure Client Tests** (`test_azure_client.py`): Test Azure client with comprehensive mocking of Graph API calls

### Integration Tests (`tests/integration/`)

End-to-end tests that exercise complete workflows:

- **End-to-End Workflow Tests** (`test_end_to_end.py`): Test complete workflows from the demo guide including validate → create → cleanup sequences

## Test Fixtures

### Test Company Configurations

- **`test_company.json`**: Small test company (6 users, 2 departments) for faster testing
- **`minimal_company.json`**: Minimal valid configuration (1 user, 1 department)
- **`invalid_company.json`**: Invalid data for testing error handling

## Running Tests

### Using the Test Runner Script

The project includes a comprehensive test runner script (`run_tests.py`) that provides various testing options:

```bash
# Install test dependencies and run all tests
./run_tests.py all --install-deps --verbose

# Run only unit tests
./run_tests.py unit --verbose

# Run only integration tests
./run_tests.py integration --verbose

# Run tests with coverage report
./run_tests.py all --coverage

# Run tests in parallel (faster)
./run_tests.py all --parallel

# Run a specific test file
./run_tests.py specific --test-path tests/unit/test_config.py

# Generate coverage report only
./run_tests.py coverage

# Run code linting
./run_tests.py lint

# Run type checking
./run_tests.py type-check

# Validate test fixtures
./run_tests.py fixtures
```

### Using pytest Directly

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run unit tests only
pytest tests/unit/ -m unit

# Run integration tests only
pytest tests/integration/ -m integration

# Run with coverage
pytest --cov=entrasim --cov-report=html --cov-report=term-missing

# Run specific test
pytest tests/unit/test_config.py::TestConfig::test_valid_config_creation

# Run tests matching a pattern
pytest -k "test_config"

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

## Test Markers

Tests are marked with pytest markers for selective running:

- `@pytest.mark.unit`: Unit tests that don't require external dependencies
- `@pytest.mark.integration`: Integration tests with mocked Azure services
- `@pytest.mark.azure`: Tests that interact with Azure services (mocked)
- `@pytest.mark.slow`: Tests that take longer to run

Example usage:
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run Azure-related tests
pytest -m azure
```

## Test Features

### Comprehensive Mocking

All tests use comprehensive mocking to avoid real Azure API calls:

- **Azure Authentication**: Mocked credential creation and authentication
- **Graph API Calls**: Mocked user and group creation, deletion, and management
- **Network Operations**: Mocked HTTP requests and responses
- **File Operations**: Temporary files and directories for safe testing

### Fixtures and Test Data

The test suite includes extensive fixtures:

- **Configuration Fixtures**: Mock Azure credentials and config objects
- **Company Data Fixtures**: Various company configurations for testing
- **File Fixtures**: Temporary JSON/YAML files with test data
- **Azure Client Fixtures**: Mock Azure clients with predictable responses

### Error Scenario Testing

Tests cover all error scenarios from the demo guide:

- Missing or invalid Azure credentials
- Network connectivity failures
- Invalid file formats (JSON/YAML)
- Invalid company data
- Azure API errors and rate limiting
- File not found errors
- Authentication failures

## Test Coverage

The test suite aims for comprehensive coverage of:

- All CLI commands (`validate`, `create`, `cleanup`)
- All configuration scenarios (environment variables, .env files)
- All file formats (JSON, YAML, .yml)
- All Azure operations (authentication, resource creation, cleanup)
- All error conditions and edge cases
- All workflows described in the demo guide

### Coverage Reports

Generate coverage reports with:

```bash
# HTML report (detailed)
pytest --cov=entrasim --cov-report=html
# View at: htmlcov/index.html

# Terminal report
pytest --cov=entrasim --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=entrasim --cov-report=xml
```

## Continuous Integration

The test suite is designed to work with CI/CD systems:

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -e ".[test]"
      - name: Run tests
        run: |
          pytest --cov=entrasim --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Environment

### Required Dependencies

- Python 3.10+
- pytest 7.0+
- pytest-asyncio 0.21+
- pytest-mock 3.10+
- pytest-cov 4.0+
- pytest-xdist 3.0+ (for parallel testing)

### Environment Variables

Tests use mock environment variables and don't require real Azure credentials. However, you can set these for configuration testing:

```bash
# Not required for tests, but used for configuration validation testing
AZURE_TENANT_ID=test-tenant-id
AZURE_CLIENT_ID=test-client-id
AZURE_CLIENT_SECRET=test-secret
AZURE_SUBSCRIPTION_ID=test-subscription-id
```

## Writing New Tests

### Test Organization

- **Unit tests**: Place in `tests/unit/test_<module_name>.py`
- **Integration tests**: Place in `tests/integration/test_<feature_name>.py`
- **Use descriptive test names**: `test_<what_is_being_tested>_<expected_outcome>`

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestFeatureName:
    """Test a specific feature or class."""
    
    @pytest.mark.unit
    def test_specific_functionality(self, fixture_name):
        """Test specific functionality with expected outcome."""
        # Arrange
        # Act
        # Assert
```

### Using Fixtures

```python
def test_something(self, mock_config, temp_dir, sample_company_data):
    """Test using multiple fixtures."""
    # mock_config: Mock Azure configuration
    # temp_dir: Temporary directory for file operations
    # sample_company_data: Sample company JSON data
```

### Mocking Azure Operations

```python
@pytest.mark.asyncio
async def test_azure_operation(self, mock_config):
    """Test Azure operation with mocking."""
    mock_client = Mock()
    mock_client.some_method = AsyncMock(return_value="expected_result")
    
    with patch('module.create_azure_client', return_value=mock_client):
        # Test your code
        pass
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure EntraSim is installed in development mode: `pip install -e .`
2. **Missing Dependencies**: Install test dependencies: `pip install -e ".[test]"`
3. **Async Test Issues**: Make sure to use `@pytest.mark.asyncio` for async tests
4. **Fixture Conflicts**: Check `conftest.py` for fixture definitions and scopes

### Debug Mode

Run tests with additional debugging:

```bash
# Verbose output with debug logging
pytest -v -s --log-cli-level=DEBUG

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb
```

## Contributing

When adding new functionality to EntraSim:

1. **Write tests first** (TDD approach recommended)
2. **Add unit tests** for new functions/classes
3. **Add integration tests** for new workflows
4. **Update fixtures** if new test data is needed
5. **Run the full test suite** before submitting changes
6. **Update test documentation** for new test patterns or fixtures

The test suite is a critical part of ensuring EntraSim works reliably and safely when interacting with Azure resources.