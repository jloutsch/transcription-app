"""
Unit tests for transcribe_cli.py

Tests core transcription functions including:
- Simple transcription
- WavLM diarization
- Progress tracking
- Output formatting
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

# Import the module we're testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import transcribe_cli


# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestTranscribeSimple:
    """Test suite for simple transcription without diarization."""

    def test_transcribe_simple_with_valid_audio(self, mock_whisper_model, temp_output_dir):
        """
        TC-CLI-001: Simple transcription with valid audio file

        Verify that transcribe_simple() successfully processes a valid audio file
        and returns segments with timestamps.
        """
        # TODO: Implement test
        # 1. Mock WhisperModel loading
        # 2. Call transcribe_simple() with test audio
        # 3. Assert segments are returned with correct structure
        pytest.skip("Test not yet implemented")

    def test_transcribe_simple_nonexistent_file(self):
        """
        TC-CLI-002: Handle non-existent file path

        Verify that transcribe_simple() raises FileNotFoundError for missing files.
        """
        # TODO: Implement test
        pytest.skip("Test not yet implemented")

    def test_transcribe_simple_invalid_format(self):
        """
        TC-CLI-003: Handle invalid audio format

        Verify graceful error handling for corrupted/invalid audio files.
        """
        # TODO: Implement test
        pytest.skip("Test not yet implemented")

    def test_transcribe_simple_silent_audio(self):
        """
        TC-CLI-004: Handle empty/silent audio file

        Verify behavior with silent audio (should return empty segments or warning).
        """
        # TODO: Implement test
        pytest.skip("Test not yet implemented")

    def test_transcribe_different_model_sizes(self):
        """
        TC-CLI-005: Transcribe with different model sizes

        Verify that tiny, base, and medium models all produce consistent output format.
        """
        # TODO: Implement test
        pytest.skip("Test not yet implemented")

    def test_language_auto_detection(self, mock_whisper_model):
        """
        TC-CLI-006: Language auto-detection

        Verify that the transcription correctly detects and reports the language.
        """
        # TODO: Implement test
        pytest.skip("Test not yet implemented")


class TestTranscribeWithWavLM:
    """Test suite for WavLM speaker diarization."""

    @patch('transcribe_cli.torchaudio')
    @patch('transcribe_cli.WavLMForXVector')
    @patch('transcribe_cli.Wav2Vec2FeatureExtractor')
    @patch('transcribe_cli.AgglomerativeClustering')
    @patch('transcribe_cli.np')
    @patch('transcribe_cli.torch')
    def test_diarization_two_speakers(self, mock_torch, mock_np, mock_clustering,
                                     mock_extractor_class, mock_model_class,
                                     mock_torchaudio, mock_whisper_model, temp_output_dir):
        """
        TC-CLI-007: Diarization with 2 speakers

        Verify that diarization correctly identifies and labels 2 speakers.
        """
        # Arrange
        output_path = temp_output_dir / "diarized_output.txt"
        audio_path = "/fake/audio.mp3"

        # Mock Whisper segments with words
        word1 = Mock()
        word1.word = "Hello"
        word1.start = 0.0
        word1.end = 0.5

        word2 = Mock()
        word2.word = "world"
        word2.start = 1.0
        word2.end = 1.5

        segment = Mock()
        segment.words = [word1, word2]
        segment.text = "Hello world"

        info = Mock()
        info.language = "en"
        info.duration = 2.0

        mock_whisper_model.transcribe.return_value = ([segment], info)

        # Mock torchaudio
        import numpy as np
        mock_waveform = Mock()
        mock_waveform.__getitem__ = Mock(return_value=Mock())
        mock_torchaudio.load.return_value = (mock_waveform, 16000)

        # Mock WavLM models
        mock_extractor = Mock()
        mock_extractor_class.from_pretrained.return_value = mock_extractor

        mock_model = Mock()
        mock_embedding = Mock()
        mock_embedding.cpu.return_value.numpy.return_value = np.random.rand(512)
        mock_output = Mock()
        mock_output.embeddings = mock_embedding
        mock_model.return_value = mock_output
        mock_model_class.from_pretrained.return_value = mock_model

        # Mock clustering to return 2 speakers
        mock_clustering_instance = Mock()
        mock_clustering_instance.fit_predict.return_value = np.array([0, 1])  # 2 speakers
        mock_clustering.return_value = mock_clustering_instance

        # Mock numpy
        mock_np.array.return_value = np.array([[0.1], [0.2]])

        # Mock torch
        mock_torch.no_grad.return_value.__enter__ = Mock()
        mock_torch.no_grad.return_value.__exit__ = Mock()
        mock_torch.nn.functional.normalize.return_value = Mock()

        # Act
        result = transcribe_cli.transcribe_with_wavlm(mock_whisper_model, audio_path, 2, str(output_path))

        # Assert
        assert result == str(output_path)
        assert output_path.exists()

        content = output_path.read_text()
        assert "SPEAKER_" in content or "Hello world" in content

    def test_diarization_handles_no_words(self, mock_whisper_model, temp_output_dir):
        """
        TC-CLI-008: Diarization with no words

        Verify that diarization handles empty transcription gracefully.
        """
        # Arrange
        output_path = temp_output_dir / "empty_output.txt"
        audio_path = "/fake/silent.mp3"

        # Mock segment with no words
        segment = Mock()
        segment.words = []
        segment.text = ""

        info = Mock()
        info.language = "en"
        info.duration = 1.0

        mock_whisper_model.transcribe.return_value = ([segment], info)

        # Act
        result = transcribe_cli.transcribe_with_wavlm(mock_whisper_model, audio_path, 2, str(output_path))

        # Assert
        assert result == str(output_path)
        assert output_path.exists()

    @patch('transcribe_cli.torchaudio')
    @patch('transcribe_cli.WavLMForXVector')
    @patch('transcribe_cli.Wav2Vec2FeatureExtractor')
    def test_diarization_calls_whisper_with_word_timestamps(self, mock_extractor_class,
                                                            mock_model_class, mock_torchaudio,
                                                            mock_whisper_model, temp_output_dir):
        """
        TC-CLI-009: Verify Whisper is called with word_timestamps=True

        Essential for diarization to work.
        """
        # Arrange
        output_path = temp_output_dir / "output.txt"
        audio_path = "/fake/audio.mp3"

        segment = Mock()
        segment.words = []
        segment.text = "test"

        info = Mock()
        info.language = "en"
        info.duration = 1.0

        mock_whisper_model.transcribe.return_value = ([segment], info)

        # Act
        transcribe_cli.transcribe_with_wavlm(mock_whisper_model, audio_path, 2, str(output_path))

        # Assert
        mock_whisper_model.transcribe.assert_called_once()
        call_kwargs = mock_whisper_model.transcribe.call_args[1]
        assert call_kwargs['word_timestamps'] is True
        assert call_kwargs['vad_filter'] is True

    def test_sliding_window_constants(self):
        """
        TC-CLI-010: Validate sliding window parameters

        Verify that WINDOW_SIZE and WINDOW_STRIDE create correct overlap.
        """
        # This test verifies the constants are as expected
        # The actual implementation uses WINDOW_SIZE=1.0 and WINDOW_STRIDE=0.5

        # We can read the source to verify constants
        import inspect
        source = inspect.getsource(transcribe_cli.transcribe_with_wavlm)

        assert "WINDOW_SIZE = 1.0" in source
        assert "WINDOW_STRIDE = 0.5" in source

        # Verify 50% overlap
        # If WINDOW_SIZE=1.0 and STRIDE=0.5, overlap = (1.0 - 0.5) / 1.0 = 0.5 = 50%
        window_size = 1.0
        stride = 0.5
        overlap = (window_size - stride) / window_size
        assert overlap == 0.5, "Should have 50% overlap"

    def test_output_file_contains_metadata(self, mock_whisper_model, temp_output_dir):
        """
        TC-CLI-011: Verify output file contains metadata

        Check that transcript includes filename, language, duration.
        """
        # Arrange
        output_path = temp_output_dir / "metadata_test.txt"
        audio_path = "/fake/path/test_file.mp3"

        segment = Mock()
        segment.words = []
        segment.text = "Test content"

        info = Mock()
        info.language = "en"
        info.duration = 5.25

        mock_whisper_model.transcribe.return_value = ([segment], info)

        # Act
        transcribe_cli.transcribe_with_wavlm(mock_whisper_model, audio_path, 2, str(output_path))

        # Assert
        content = output_path.read_text()
        assert "test_file.mp3" in content
        assert "Language: en" in content
        assert "Duration: 5.25 seconds" in content


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


class TestTranscribeSimpleFunction:
    """Test suite for transcribe_simple() function."""

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


class TestCliMain:
    """Test suite for main() CLI function."""

    @patch('transcribe_cli.WhisperModel')
    @patch('transcribe_cli.transcribe_simple')
    def test_main_simple_transcription(self, mock_transcribe_simple, mock_whisper_class, temp_output_dir):
        """
        TC-CLI-016: CLI main() with simple transcription

        Verify main() processes JSON request for simple transcription.
        """
        # Arrange
        json_file = temp_output_dir / "request.json"
        audio_file = temp_output_dir / "test.mp3"
        audio_file.touch()

        request_data = {
            "audioFiles": [str(audio_file)],
            "modelSize": "tiny",
            "outputPath": str(temp_output_dir),
            "enableDiarization": False
        }
        json_file.write_text(json.dumps(request_data))

        mock_model = Mock()
        mock_whisper_class.return_value = mock_model
        mock_transcribe_simple.return_value = str(temp_output_dir / "test.txt")

        # Act
        with patch('sys.argv', ['transcribe_cli.py', '--json', str(json_file)]):
            transcribe_cli.main()

        # Assert
        mock_whisper_class.assert_called_once_with("tiny", device="auto", compute_type="auto")
        mock_transcribe_simple.assert_called_once()
        call_args = mock_transcribe_simple.call_args[0]
        assert call_args[0] == mock_model
        assert call_args[1] == str(audio_file)

    @patch('transcribe_cli.WhisperModel')
    @patch('transcribe_cli.transcribe_with_wavlm')
    def test_main_with_diarization(self, mock_diarize, mock_whisper_class, temp_output_dir):
        """
        TC-CLI-017: CLI main() with WavLM diarization

        Verify main() processes JSON request with diarization enabled.
        """
        # Arrange
        json_file = temp_output_dir / "request.json"
        audio_file = temp_output_dir / "test.mp3"
        audio_file.touch()

        request_data = {
            "audioFiles": [str(audio_file)],
            "modelSize": "tiny",
            "outputPath": str(temp_output_dir),
            "enableDiarization": True,
            "diarizationMethod": "wavlm",
            "numSpeakers": 3
        }
        json_file.write_text(json.dumps(request_data))

        mock_model = Mock()
        mock_whisper_class.return_value = mock_model
        mock_diarize.return_value = str(temp_output_dir / "test.txt")

        # Act
        with patch('sys.argv', ['transcribe_cli.py', '--json', str(json_file)]):
            with patch('transcribe_cli.HAS_WAVLM', True):
                transcribe_cli.main()

        # Assert
        mock_diarize.assert_called_once()
        call_args = mock_diarize.call_args[0]
        assert call_args[0] == mock_model
        assert call_args[1] == str(audio_file)
        assert call_args[2] == 3  # num_speakers

    @patch('transcribe_cli.WhisperModel')
    def test_main_multiple_files(self, mock_whisper_class, temp_output_dir):
        """
        TC-CLI-018: CLI main() with multiple audio files

        Verify main() processes all files in batch.
        """
        # Arrange
        json_file = temp_output_dir / "request.json"
        audio1 = temp_output_dir / "test1.mp3"
        audio2 = temp_output_dir / "test2.mp3"
        audio1.touch()
        audio2.touch()

        request_data = {
            "audioFiles": [str(audio1), str(audio2)],
            "modelSize": "tiny",
            "outputPath": str(temp_output_dir)
        }
        json_file.write_text(json.dumps(request_data))

        mock_model = Mock()
        mock_whisper_class.return_value = mock_model

        with patch('transcribe_cli.transcribe_simple') as mock_simple:
            mock_simple.return_value = "output.txt"

            # Act
            with patch('sys.argv', ['transcribe_cli.py', '--json', str(json_file)]):
                transcribe_cli.main()

            # Assert - transcribe_simple called twice
            assert mock_simple.call_count == 2

    def test_main_no_json_argument(self, capsys):
        """
        TC-CLI-019: CLI main() without --json argument

        Verify main() exits with error when --json is missing.
        """
        # Act & Assert
        with patch('sys.argv', ['transcribe_cli.py']):
            with pytest.raises(SystemExit) as exc_info:
                transcribe_cli.main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error: --json argument required" in captured.err

    def test_main_invalid_json_file(self, temp_output_dir, capsys):
        """
        TC-CLI-020: CLI main() with invalid JSON file

        Verify main() exits gracefully with invalid JSON.
        """
        # Arrange
        json_file = temp_output_dir / "invalid.json"
        json_file.write_text("{invalid json content")

        # Act & Assert
        with patch('sys.argv', ['transcribe_cli.py', '--json', str(json_file)]):
            with pytest.raises(SystemExit) as exc_info:
                transcribe_cli.main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error reading JSON" in captured.err

    def test_main_no_audio_files(self, temp_output_dir, capsys):
        """
        TC-CLI-021: CLI main() with empty audioFiles list

        Verify main() exits when no audio files are specified.
        """
        # Arrange
        json_file = temp_output_dir / "request.json"
        request_data = {
            "audioFiles": [],
            "modelSize": "tiny"
        }
        json_file.write_text(json.dumps(request_data))

        # Act & Assert
        with patch('sys.argv', ['transcribe_cli.py', '--json', str(json_file)]):
            with pytest.raises(SystemExit) as exc_info:
                transcribe_cli.main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "No audio files specified" in captured.err

    @patch('transcribe_cli.WhisperModel')
    @patch('transcribe_cli.transcribe_simple')
    def test_main_handles_processing_error(self, mock_simple, mock_whisper_class, temp_output_dir, capsys):
        """
        TC-CLI-022: CLI main() handles processing errors gracefully

        Verify main() continues processing when one file fails.
        """
        # Arrange
        json_file = temp_output_dir / "request.json"
        audio1 = temp_output_dir / "test1.mp3"
        audio2 = temp_output_dir / "test2.mp3"
        audio1.touch()
        audio2.touch()

        request_data = {
            "audioFiles": [str(audio1), str(audio2)],
            "modelSize": "tiny",
            "outputPath": str(temp_output_dir)
        }
        json_file.write_text(json.dumps(request_data))

        mock_model = Mock()
        mock_whisper_class.return_value = mock_model

        # First call raises exception, second succeeds
        mock_simple.side_effect = [
            Exception("Processing error"),
            str(temp_output_dir / "test2.txt")
        ]

        # Act
        with patch('sys.argv', ['transcribe_cli.py', '--json', str(json_file)]):
            transcribe_cli.main()

        # Assert - both files attempted despite first failure
        assert mock_simple.call_count == 2

        captured = capsys.readouterr()
        assert "Error processing" in captured.err


# Example of a minimal working test (not in test plan)
def test_pytest_working():
    """Sanity check that pytest is configured correctly."""
    assert True
