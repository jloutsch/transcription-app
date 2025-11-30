# Test Suite for Transcription Application

This directory contains the automated test suite for the basic transcription application (without speaker diarization).

**Note:** For speaker diarization tests, see the `diarization` branch.

## Test Framework Setup

The test framework uses **pytest** with the following plugins:
- `pytest-cov` - Code coverage reporting
- `pytest-mock` - Mocking and patching
- `pytest-timeout` - Test timeout handling

## Installation

All test dependencies are already installed in the virtual environment. To verify:

```bash
source venv/bin/activate
pytest --version
```

## Running Tests

### Run all tests
```bash
source venv/bin/activate
pytest
```

### Run specific test categories
```bash
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests only
pytest -m unit                           # Run tests marked as 'unit'
```

### Run with coverage report
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html  # View coverage in browser
```

## Test Structure

```
tests/
├── README.md                          # This file
├── conftest.py                        # Shared fixtures and configuration
├── __init__.py
├── unit/                              # Unit tests
│   └── test_transcribe_cli.py        # Tests for transcribe_cli.py
├── integration/                       # Integration tests
│   └── test_workflows.py             # End-to-end workflow tests
├── functional/                        # Functional tests
│   └── test_features.py              # Feature validation tests
└── fixtures/                          # Test data
    └── audio/                         # Sample audio files
```

## Current Status

**Total Tests:** 10 passing
**Coverage:** ~20% (general transcription functions only)
**Branch:** main (no diarization)

### Implemented Tests

**Unit Tests (10 passing):**
- `progress_print()` - 5 tests
- `output_print()` - 2 tests
- `transcribe_simple()` - 2 tests
- Sanity check - 1 test

## Test Markers

Tests can be marked with:
- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.functional` - Functional tests
- `@pytest.mark.slow` - Tests that take significant time
- `@pytest.mark.requires_audio` - Tests requiring audio fixtures

### Filter by markers
```bash
pytest -m "unit and not slow"           # Fast unit tests only
```

## Writing Tests

### Example Test

```python
import pytest

@pytest.mark.unit
def test_example_function(mock_whisper_model, temp_output_dir):
    """Test description."""
    # Arrange
    input_data = "test.mp3"

    # Act
    result = some_function(input_data)

    # Assert
    assert result is not None
```

### Available Fixtures

See `conftest.py` for all available fixtures:
- `temp_output_dir` - Temporary directory for test outputs
- `sample_audio_path` - Path to sample audio file
- `mock_whisper_model` - Mocked Whisper model
- `default_config` - Default configuration dict

## Diarization Tests

Speaker diarization tests are located on the **diarization** branch. This branch contains only general transcription tests.

To work with diarization tests:
```bash
git checkout diarization
pytest  # Run all tests including diarization
```

---

**Last Updated:** 2025-11-30
**Branch:** main
**Status:** Basic test suite operational
