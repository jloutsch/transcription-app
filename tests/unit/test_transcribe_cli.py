"""
Unit tests for transcribe_cli.py (General transcription - no diarization)

Tests core transcription functions including:
- Simple transcription
- Progress tracking
- Output formatting
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock
from io import StringIO

# Import the module we're testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import transcribe_cli


# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestProgressPrint:
    """Test suite for progress_print() function."""

    def test_progress_print_valid(self, capsys):
        """
        TC-CLI-013: Print valid progress

        Verify progress_print() outputs correct format.
        """
        # Act
        transcribe_cli.progress_print(0.5, "Processing")

        # Assert
        captured = capsys.readouterr()
        assert captured.out == "PROGRESS:0.50:Processing\n"

    def test_progress_print_zero_progress(self, capsys):
        """
        TC-CLI-014a: Progress at zero

        Verify that progress value 0.0 is handled correctly.
        """
        # Act
        transcribe_cli.progress_print(0.0, "Starting")

        # Assert
        captured = capsys.readouterr()
        assert captured.out == "PROGRESS:0.00:Starting\n"

    def test_progress_print_complete(self, capsys):
        """
        TC-CLI-014b: Progress at completion

        Verify that progress value 1.0 is handled correctly.
        """
        # Act
        transcribe_cli.progress_print(1.0, "Complete")

        # Assert
        captured = capsys.readouterr()
        assert captured.out == "PROGRESS:1.00:Complete\n"

    def test_progress_print_special_characters(self, capsys):
        """
        TC-CLI-015: Special characters in message

        Verify that special characters are included in progress messages.
        """
        # Act
        transcribe_cli.progress_print(0.75, "Processing file: test's.mp3")

        # Assert
        captured = capsys.readouterr()
        assert "test's.mp3" in captured.out
        assert "PROGRESS:0.75:" in captured.out

    def test_progress_print_with_colons(self, capsys):
        """
        TC-CLI-015b: Colons in message

        Verify that colons in messages are handled (they're part of the format).
        """
        # Act
        transcribe_cli.progress_print(0.33, "Step 1:3 - Loading")

        # Assert
        captured = capsys.readouterr()
        assert "PROGRESS:0.33:Step 1:3 - Loading\n" == captured.out


class TestOutputPrint:
    """Test suite for output_print() function."""

    def test_output_print_valid_path(self, capsys):
        """
        Verify output_print() outputs correct format with valid path.
        """
        # Act
        transcribe_cli.output_print("/tmp/output.txt")

        # Assert
        captured = capsys.readouterr()
        assert captured.out == "OUTPUT:/tmp/output.txt\n"

    def test_output_print_path_with_spaces(self, capsys):
        """
        Verify output_print() handles paths with spaces.
        """
        # Act
        transcribe_cli.output_print("/tmp/my folder/output.txt")

        # Assert
        captured = capsys.readouterr()
        assert captured.out == "OUTPUT:/tmp/my folder/output.txt\n"


class TestTranscribeSimple:
    """Test suite for transcribe_simple() function (without diarization)."""

    def test_transcribe_simple_creates_output_file(self, mock_whisper_model, temp_output_dir):
        """
        TC-CLI-001: Simple transcription creates output file

        Verify that transcribe_simple() creates an output file.
        """
        # Arrange
        output_path = temp_output_dir / "test_output.txt"
        audio_path = "/fake/path/test.mp3"

        # Mock the transcribe return value
        mock_segment = Mock()
        mock_segment.text = "Hello world"
        mock_info = Mock()
        mock_info.language = "en"
        mock_info.duration = 5.0

        mock_whisper_model.transcribe.return_value = ([mock_segment], mock_info)

        # Act
        result_path = transcribe_cli.transcribe_simple(mock_whisper_model, audio_path, str(output_path))

        # Assert
        assert result_path == str(output_path)
        assert output_path.exists()

        # Verify file contents
        content = output_path.read_text()
        assert "test.mp3" in content
        assert "Language: en" in content
        assert "Duration: 5.00 seconds" in content
        assert "Hello world" in content

    def test_transcribe_simple_calls_model_with_correct_params(self, mock_whisper_model, temp_output_dir):
        """
        TC-CLI-002: Verify transcribe_simple() calls Whisper model correctly

        Ensure the model is called with proper parameters.
        """
        # Arrange
        output_path = temp_output_dir / "output.txt"
        audio_path = "/test/audio.mp3"

        mock_segment = Mock()
        mock_segment.text = "Test"
        mock_info = Mock()
        mock_info.language = "en"
        mock_info.duration = 1.0

        mock_whisper_model.transcribe.return_value = ([mock_segment], mock_info)

        # Act
        transcribe_cli.transcribe_simple(mock_whisper_model, audio_path, str(output_path))

        # Assert
        mock_whisper_model.transcribe.assert_called_once()
        call_args = mock_whisper_model.transcribe.call_args
        assert call_args[0][0] == audio_path  # First positional arg
        assert call_args[1]['language'] is None  # Auto-detect
        assert call_args[1]['vad_filter'] is True


# Example of a minimal working test
def test_pytest_working():
    """Sanity check that pytest is configured correctly."""
    assert True
