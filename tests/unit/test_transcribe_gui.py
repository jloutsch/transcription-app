"""
Unit tests for transcribe_gui.py (business logic only)

Tests GUI application business logic including:
- Configuration management
- File queue operations
- Input validation
- Timestamp formatting
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the module we're testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import transcribe_gui


# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestConfigurationManagement:
    """Test suite for config loading and saving."""

    @patch('transcribe_gui.CONFIG_FILE')
    @patch('transcribe_gui.Tk')
    def test_load_valid_config(self, mock_tk, mock_config_file_path,
                              sample_config_file, default_config):
        """
        TC-GUI-005: Load valid config file

        Verify that a valid config file is loaded correctly.
        """
        # Arrange
        mock_config_file_path.__truediv__ = Mock(return_value=sample_config_file)
        mock_config_file_path.exists.return_value = True

        # Create minimal app instance
        with patch('transcribe_gui.HAS_DND', False):
            with patch('transcribe_gui.multiprocessing.cpu_count', return_value=4):
                app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)

                # Initialize minimal required attributes
                app.output_folder = None
                app.cpu_cores = 4  # Add cpu_cores attribute
                app.remember_folder = Mock()
                app.remember_folder.set = Mock()
                app.remember_folder.get = Mock(return_value=False)
                app.cpu_threads = Mock()
                app.cpu_threads.set = Mock()
                app.cpu_threads.get = Mock(return_value=4)
                app.output_format = Mock()
                app.output_format.set = Mock()
                app.enable_diarization = Mock()
                app.enable_diarization.set = Mock()
                app.hf_token = Mock()
                app.hf_token.set = Mock()
                app.num_speakers = Mock()
                app.num_speakers.set = Mock()

        # Mock CONFIG_FILE to point to our test file
        with patch('transcribe_gui.CONFIG_FILE', sample_config_file):
            # Act
            app.load_config()

            # Assert - verify set methods were called with config values
            app.remember_folder.set.assert_called()
            app.cpu_threads.set.assert_called()

    @patch('transcribe_gui.CONFIG_FILE')
    @patch('transcribe_gui.Tk')
    def test_load_corrupted_config(self, mock_tk, mock_config_file_path, invalid_config_file):
        """
        TC-GUI-006: Load corrupted config

        Verify that corrupted config falls back to defaults with warning.
        """
        # Arrange
        with patch('transcribe_gui.HAS_DND', False):
            with patch('transcribe_gui.multiprocessing.cpu_count', return_value=4):
                app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)

                # Initialize minimal required attributes
                app.output_folder = None
                app.cpu_cores = 4  # Add cpu_cores attribute
                app.remember_folder = Mock()
                app.cpu_threads = Mock()
                app.output_format = Mock()
                app.enable_diarization = Mock()
                app.hf_token = Mock()
                app.num_speakers = Mock()

        # Mock CONFIG_FILE to point to invalid file
        with patch('transcribe_gui.CONFIG_FILE', invalid_config_file):
            # Act - should not crash
            app.load_config()

            # Assert - app should still have default state (no crash)
            assert app.output_folder is None  # Should remain None (not set from corrupt file)

    @patch('transcribe_gui.Tk')
    def test_save_config_to_disk(self, mock_tk, temp_output_dir):
        """
        TC-GUI-007: Save config to disk

        Verify that configuration is saved to JSON file correctly.
        """
        # Arrange
        config_path = temp_output_dir / "test_config.json"

        with patch('transcribe_gui.HAS_DND', False):
            with patch('transcribe_gui.multiprocessing.cpu_count', return_value=4):
                app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)

                # Set up config values
                app.output_folder = "/tmp/output"
                app.remember_folder = Mock()
                app.remember_folder.get = Mock(return_value=True)
                app.cpu_threads = Mock()
                app.cpu_threads.get = Mock(return_value=8)
                app.output_format = Mock()
                app.output_format.get = Mock(return_value="with_timestamps")
                app.enable_diarization = Mock()
                app.enable_diarization.get = Mock(return_value=False)
                app.hf_token = Mock()
                app.hf_token.get = Mock(return_value="")
                app.num_speakers = Mock()
                app.num_speakers.get = Mock(return_value=2)

        # Mock CONFIG_FILE to point to our test path
        with patch('transcribe_gui.CONFIG_FILE', config_path):
            # Act
            app.save_config()

            # Assert
            assert config_path.exists()

            # Verify JSON content
            content = json.loads(config_path.read_text())
            assert content['output_folder'] == "/tmp/output"
            assert content['remember_folder'] is True
            assert content['cpu_threads'] == 8
            assert content['num_speakers'] == 2


class TestFileQueueOperations:
    """Test suite for file queue management."""

    @patch('transcribe_gui.Tk')
    def test_add_file_to_queue(self, mock_tk, temp_output_dir):
        """
        TC-GUI-008: Add file to queue

        Verify that a file can be added to the processing queue.
        """
        # Arrange
        test_audio = temp_output_dir / "test.mp3"
        test_audio.touch()  # Create the file

        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.file_queue = []
            app.update_file_list = Mock()
            app.update_start_button = Mock()

        # Act
        app.add_files_to_queue([str(test_audio)])

        # Assert
        assert len(app.file_queue) == 1
        assert app.file_queue[0] == test_audio
        app.update_file_list.assert_called_once()
        app.update_start_button.assert_called_once()

    @patch('transcribe_gui.Tk')
    def test_add_duplicate_file_to_queue(self, mock_tk, temp_output_dir):
        """
        TC-GUI-008b: Adding duplicate file to queue

        Verify that duplicate files are not added twice.
        """
        # Arrange
        test_audio = temp_output_dir / "test.mp3"
        test_audio.touch()

        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.file_queue = [test_audio]  # Already in queue
            app.update_file_list = Mock()
            app.update_start_button = Mock()

        # Act
        app.add_files_to_queue([str(test_audio)])

        # Assert - queue length should still be 1
        assert len(app.file_queue) == 1

    @patch('transcribe_gui.Tk')
    def test_remove_file_from_queue(self, mock_tk, temp_output_dir):
        """
        TC-GUI-009: Remove file from queue

        Verify that a file can be removed from the queue.
        """
        # Arrange
        test_audio = temp_output_dir / "test.mp3"

        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.file_queue = [test_audio]
            app.selected_file_index = 0
            app.is_processing = False
            app.update_file_list = Mock()
            app.update_start_button = Mock()

        # Act
        app.remove_selected_file()

        # Assert
        assert len(app.file_queue) == 0
        assert app.selected_file_index is None
        app.update_file_list.assert_called_once()
        app.update_start_button.assert_called_once()

    @patch('transcribe_gui.Tk')
    def test_remove_file_while_processing(self, mock_tk, temp_output_dir):
        """
        TC-GUI-009b: Cannot remove file while processing

        Verify that files cannot be removed during processing.
        """
        # Arrange
        test_audio = temp_output_dir / "test.mp3"

        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.file_queue = [test_audio]
            app.selected_file_index = 0
            app.is_processing = True  # Currently processing
            app.update_file_list = Mock()
            app.update_start_button = Mock()

        # Act
        app.remove_selected_file()

        # Assert - file should still be in queue
        assert len(app.file_queue) == 1
        app.update_file_list.assert_not_called()

    @patch('transcribe_gui.Tk')
    def test_detect_unsupported_file_type(self, mock_tk, temp_output_dir):
        """
        TC-GUI-012: Detect unsupported file type

        Verify that unsupported file types are rejected with warning.
        """
        # Arrange
        unsupported_file = temp_output_dir / "test.xyz"
        unsupported_file.touch()  # Create unsupported file

        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.file_queue = []
            app.update_file_list = Mock()
            app.update_start_button = Mock()

        # Act
        app.add_files_to_queue([str(unsupported_file)])

        # Assert - file should NOT be added to queue
        assert len(app.file_queue) == 0


class TestStartButtonLogic:
    """Test suite for start button enable/disable logic."""

    @patch('transcribe_gui.Tk')
    def test_update_start_button_enabled(self, mock_tk, temp_output_dir):
        """
        TC-GUI-013: Start button enabled when conditions met

        Verify start button is enabled when files and output folder are set.
        """
        # Arrange
        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.file_queue = [Path("/test/file.mp3")]
            app.output_folder = str(temp_output_dir)
            app.is_processing = False
            app.start_button = Mock()

        # Act
        app.update_start_button()

        # Assert
        app.start_button.config.assert_called_once_with(state='normal')

    @patch('transcribe_gui.Tk')
    def test_update_start_button_disabled_no_files(self, mock_tk, temp_output_dir):
        """
        TC-GUI-014: Start button disabled without files

        Verify start button is disabled when no files in queue.
        """
        # Arrange
        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.file_queue = []  # Empty queue
            app.output_folder = str(temp_output_dir)
            app.is_processing = False
            app.start_button = Mock()

        # Act
        app.update_start_button()

        # Assert
        app.start_button.config.assert_called_once_with(state='disabled')

    @patch('transcribe_gui.Tk')
    def test_update_start_button_disabled_no_output(self, mock_tk):
        """
        TC-GUI-015: Start button disabled without output folder

        Verify start button is disabled when no output folder set.
        """
        # Arrange
        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.file_queue = [Path("/test/file.mp3")]
            app.output_folder = None  # No output folder
            app.is_processing = False
            app.start_button = Mock()

        # Act
        app.update_start_button()

        # Assert
        app.start_button.config.assert_called_once_with(state='disabled')

    @patch('transcribe_gui.Tk')
    def test_update_start_button_disabled_processing(self, mock_tk, temp_output_dir):
        """
        TC-GUI-016: Start button disabled during processing

        Verify start button is disabled when currently processing.
        """
        # Arrange
        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.file_queue = [Path("/test/file.mp3")]
            app.output_folder = str(temp_output_dir)
            app.is_processing = True  # Currently processing
            app.start_button = Mock()

        # Act
        app.update_start_button()

        # Assert
        app.start_button.config.assert_called_once_with(state='disabled')


class TestRemoveButtonLogic:
    """Test suite for remove button enable/disable logic."""

    @patch('transcribe_gui.Tk')
    def test_update_remove_button_enabled(self, mock_tk):
        """
        TC-GUI-017: Remove button enabled when file selected

        Verify remove button is enabled when a file is selected.
        """
        # Arrange
        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.selected_file_index = 0  # File selected
            app.is_processing = False
            app.remove_btn = Mock()

        # Act
        app.update_remove_button()

        # Assert
        app.remove_btn.config.assert_called_once_with(state='normal')

    @patch('transcribe_gui.Tk')
    def test_update_remove_button_disabled_no_selection(self, mock_tk):
        """
        TC-GUI-018: Remove button disabled without selection

        Verify remove button is disabled when no file is selected.
        """
        # Arrange
        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.selected_file_index = None  # No selection
            app.is_processing = False
            app.remove_btn = Mock()

        # Act
        app.update_remove_button()

        # Assert
        app.remove_btn.config.assert_called_once_with(state='disabled')

    @patch('transcribe_gui.Tk')
    def test_update_remove_button_disabled_processing(self, mock_tk):
        """
        TC-GUI-019: Remove button disabled during processing

        Verify remove button is disabled when currently processing.
        """
        # Arrange
        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.selected_file_index = 0  # File selected
            app.is_processing = True  # Currently processing
            app.remove_btn = Mock()

        # Act
        app.update_remove_button()

        # Assert
        app.remove_btn.config.assert_called_once_with(state='disabled')


class TestOutputFolderValidation:
    """Test suite for output folder validation."""

    @patch('transcribe_gui.Tk')
    @patch('transcribe_gui.filedialog.askdirectory')
    def test_choose_output_folder_valid_path(self, mock_askdir, mock_tk, temp_output_dir):
        """
        TC-GUI-010: Choose output folder with valid path

        Verify that choosing a valid directory updates the output folder.
        """
        # Arrange
        mock_askdir.return_value = str(temp_output_dir)

        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.output_folder = None
            app.folder_var = Mock()
            app.save_config = Mock()
            app.update_start_button = Mock()

        # Act
        app.choose_output_folder()

        # Assert
        assert app.output_folder == str(temp_output_dir)
        app.folder_var.set.assert_called_once()
        app.save_config.assert_called_once()
        app.update_start_button.assert_called_once()

    @patch('transcribe_gui.Tk')
    @patch('transcribe_gui.filedialog.askdirectory')
    def test_choose_output_folder_cancel(self, mock_askdir, mock_tk):
        """
        TC-GUI-011: Choose output folder cancelled

        Verify that canceling folder selection doesn't change output folder.
        """
        # Arrange
        mock_askdir.return_value = ""  # User cancelled

        with patch('transcribe_gui.HAS_DND', False):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)
            app.output_folder = "/original/path"
            app.folder_var = Mock()
            app.save_config = Mock()
            app.update_start_button = Mock()

        # Act
        app.choose_output_folder()

        # Assert
        assert app.output_folder == "/original/path"  # Unchanged
        app.folder_var.set.assert_not_called()
        app.save_config.assert_not_called()


class TestFormatTimestamp:
    """Test suite for timestamp formatting."""

    def test_format_timestamp_minutes_seconds(self):
        """
        TC-GUI-001: Format seconds to HH:MM:SS

        Verify that 125 seconds formats to "00:02:05".
        """
        # Arrange - Create a minimal mock app instance
        with patch('transcribe_gui.Tk'):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)

            # Act
            result = app.format_timestamp(125)

            # Assert
            assert result == "00:02:05"

    def test_format_timestamp_zero(self):
        """
        TC-GUI-002: Format zero seconds

        Verify that 0.0 seconds formats to "00:00:00".
        """
        # Arrange
        with patch('transcribe_gui.Tk'):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)

            # Act
            result = app.format_timestamp(0)

            # Assert
            assert result == "00:00:00"

    def test_format_timestamp_hours(self):
        """
        TC-GUI-003: Format hours

        Verify that 3665 seconds formats to "01:01:05".
        """
        # Arrange
        with patch('transcribe_gui.Tk'):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)

            # Act
            result = app.format_timestamp(3665)

            # Assert
            assert result == "01:01:05"

    def test_format_timestamp_with_float(self):
        """
        TC-GUI-004: Handle fractional seconds

        Verify that fractional seconds are truncated.
        """
        # Arrange
        with patch('transcribe_gui.Tk'):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)

            # Act
            result = app.format_timestamp(125.7)

            # Assert
            assert result == "00:02:05"

    def test_format_timestamp_exactly_one_hour(self):
        """
        TC-GUI-005: Format exactly one hour

        Verify that 3600 seconds formats to "01:00:00".
        """
        # Arrange
        with patch('transcribe_gui.Tk'):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)

            # Act
            result = app.format_timestamp(3600)

            # Assert
            assert result == "01:00:00"

    def test_format_timestamp_large_value(self):
        """
        TC-GUI-006: Format large timestamp

        Verify that large values (> 10 hours) are handled correctly.
        """
        # Arrange
        with patch('transcribe_gui.Tk'):
            app = transcribe_gui.TranscriptionApp.__new__(transcribe_gui.TranscriptionApp)

            # Act
            result = app.format_timestamp(36000)  # 10 hours

            # Assert
            assert result == "10:00:00"


class TestMediaExtensions:
    """Test suite for media file extensions validation."""

    def test_media_extensions_includes_common_formats(self):
        """
        Verify that MEDIA_EXTENSIONS includes common audio/video formats.
        """
        # Assert
        assert ".mp3" in transcribe_gui.MEDIA_EXTENSIONS
        assert ".wav" in transcribe_gui.MEDIA_EXTENSIONS
        assert ".mp4" in transcribe_gui.MEDIA_EXTENSIONS
        assert ".mov" in transcribe_gui.MEDIA_EXTENSIONS
        assert ".m4a" in transcribe_gui.MEDIA_EXTENSIONS

    def test_media_extensions_includes_uppercase(self):
        """
        Verify that MEDIA_EXTENSIONS includes uppercase variants.
        """
        # Assert
        assert ".MP3" in transcribe_gui.MEDIA_EXTENSIONS
        assert ".WAV" in transcribe_gui.MEDIA_EXTENSIONS
        assert ".MP4" in transcribe_gui.MEDIA_EXTENSIONS


# Example working test
def test_pytest_gui_working():
    """Sanity check for GUI test module."""
    assert True
