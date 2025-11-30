"""
Shared pytest fixtures for the transcription application test suite.

This module provides common fixtures used across all test categories.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture
def temp_output_dir():
    """
    Create a temporary output directory for tests.

    Yields:
        Path: Path to temporary directory

    Cleanup:
        Automatically removes directory after test completes
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_audio_path():
    """
    Path to a sample audio file for testing.

    Returns:
        Path: Path to sample audio file (if exists)

    Note:
        This fixture assumes test audio files are in tests/fixtures/audio/
        If the file doesn't exist, tests should skip or generate synthetic audio
    """
    audio_file = Path(__file__).parent / "fixtures/audio/short_mono_5sec.mp3"
    return audio_file


@pytest.fixture
def mock_whisper_model(mocker):
    """
    Mock faster-whisper model to avoid actual model loading.

    Args:
        mocker: pytest-mock fixture

    Returns:
        Mock: Mocked WhisperModel with transcribe method

    Example:
        def test_transcription(mock_whisper_model):
            result = mock_whisper_model.transcribe("audio.mp3")
            # Returns mock segments
    """
    mock_model = mocker.Mock()

    # Mock transcribe method to return sample segments
    mock_segment = Mock()
    mock_segment.text = "Hello world"
    mock_segment.start = 0.0
    mock_segment.end = 1.5

    mock_word = Mock()
    mock_word.word = "Hello"
    mock_word.start = 0.0
    mock_word.end = 0.5

    mock_segment.words = [mock_word]

    # Return tuple of (segments, info)
    mock_info = Mock()
    mock_info.language = "en"
    mock_info.duration = 5.0

    mock_model.transcribe.return_value = ([mock_segment], mock_info)

    return mock_model


@pytest.fixture
def default_config():
    """
    Default configuration dictionary for testing.

    Returns:
        dict: Default configuration matching app defaults
    """
    return {
        "output_folder": "/tmp/test_output",
        "remember_folder": False,
        "cpu_threads": 4,
        "output_format": "with_timestamps"
    }


@pytest.fixture
def sample_config_file(temp_output_dir, default_config):
    """
    Create a temporary config file for testing.

    Args:
        temp_output_dir: Temporary directory fixture
        default_config: Default config fixture

    Returns:
        Path: Path to temporary config file
    """
    config_path = temp_output_dir / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(default_config, f)
    return config_path


@pytest.fixture
def invalid_config_file(temp_output_dir):
    """
    Create an invalid/corrupted config file for error testing.

    Args:
        temp_output_dir: Temporary directory fixture

    Returns:
        Path: Path to invalid config file
    """
    config_path = temp_output_dir / "invalid_config.json"
    with open(config_path, 'w') as f:
        f.write("{invalid json content")
    return config_path


@pytest.fixture
def sample_transcript_segments():
    """
    Sample transcript segments for testing output formatting.

    Returns:
        list: List of mock segment objects
    """
    segments = []

    segment1 = Mock()
    segment1.text = "Hello, how are you?"
    segment1.start = 0.0
    segment1.end = 2.0
    segments.append(segment1)

    segment2 = Mock()
    segment2.text = "I'm doing well, thank you."
    segment2.start = 2.5
    segment2.end = 5.0
    segments.append(segment2)

    return segments


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """
    Reset environment variables for each test.

    Args:
        monkeypatch: pytest fixture for modifying environment

    Note:
        This fixture runs automatically before each test
    """
    # Set test-specific environment variables
    monkeypatch.setenv("PYTEST_RUNNING", "1")


# Markers for skipping tests based on conditions

def pytest_configure(config):
    """
    Configure custom pytest settings.

    Args:
        config: pytest configuration object
    """
    config.addinivalue_line(
        "markers", "requires_audio: mark test as requiring audio test files"
    )
    config.addinivalue_line(
        "markers", "requires_models: mark test as requiring downloaded models"
    )


@pytest.fixture
def skip_if_no_audio_files():
    """
    Skip test if audio fixtures are not available.

    Example:
        @pytest.mark.requires_audio
        def test_with_audio(skip_if_no_audio_files):
            # Test will skip if no audio files
    """
    audio_dir = Path(__file__).parent / "fixtures/audio"
    if not audio_dir.exists() or not any(audio_dir.iterdir()):
        pytest.skip("Audio test files not available")


@pytest.fixture
def skip_if_no_models():
    """
    Skip test if models are not downloaded.

    Example:
        @pytest.mark.requires_models
        def test_with_models(skip_if_no_models):
            # Test will skip if models not downloaded
    """
    # Check if models are cached
    model_cache = Path.home() / ".cache/huggingface/hub"
    if not model_cache.exists():
        pytest.skip("Models not downloaded")
