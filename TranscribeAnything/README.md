# Transcribe Anything - SwiftUI Edition

A native macOS SwiftUI interface for the Transcribe Anything app, providing a modern, polished user experience for audio transcription with speaker diarization.

## Features

- **Native macOS Interface**: Built with SwiftUI for a native macOS look and feel
- **Drag & Drop**: Easily add audio files by dragging them into the app
- **File Browser**: Browse and select audio files using the native file picker
- **Whisper Integration**: Supports multiple Whisper model sizes (tiny, base, small, medium, large-v3)
- **Speaker Diarization**: Integrated WavLM and Pyannote speaker diarization
- **Auto Language Detection**: Automatically detect the language or specify it manually
- **Progress Tracking**: Real-time progress updates during transcription
- **Batch Processing**: Transcribe multiple audio files at once

## Architecture

This SwiftUI app acts as a frontend to the Python transcription backend:

- **SwiftUI Interface** (`ContentView.swift`): The main UI with drag-and-drop, settings, and controls
- **Python Bridge** (`PythonBridge.swift`): Communicates with the Python transcription script
- **Models** (`Models.swift`): Data models for audio files and settings
- **App Entry** (`TranscribeAnythingApp.swift`): Main app configuration

## Building

### Requirements
- macOS 13.0 or later
- Swift 5.9 or later
- Python 3.8+ with the transcription dependencies installed

### Build and Run

```bash
cd TranscribeAnything
swift build
swift run
```

### Build for Release

```bash
swift build -c release
```

The built executable will be at `.build/release/TranscribeAnything`

## Python Backend Integration

The SwiftUI app communicates with the Python transcription backend via JSON:

1. SwiftUI creates a JSON request with audio files and settings
2. Launches the Python script with the JSON file path
3. Python script processes the request and outputs progress updates
4. SwiftUI parses progress messages (format: `PROGRESS:<value>:<message>`)
5. Python script outputs completed file paths (format: `OUTPUT:<path>`)

## Settings

### Whisper Model
- **Tiny**: Fastest, least accurate
- **Base**: Fast, good for simple audio
- **Small**: Balanced speed and accuracy
- **Medium**: Slower, more accurate (default)
- **Large-v3**: Slowest, most accurate

### Speaker Diarization
- **WavLM**: Microsoft's WavLM model for speaker identification
- **Pyannote**: Pyannote.audio speaker diarization (requires HuggingFace token)

### Language
- Auto-detect or specify a language code (en, es, fr, de, zh, ja, etc.)

## Development

The project uses Swift Package Manager for dependency management. To develop:

1. Open in Xcode (if available): `open Package.swift`
2. Or build from command line: `swift build`

## Future Enhancements

- [ ] Real-time transcription preview
- [ ] Custom output format options
- [ ] Transcript editing within the app
- [ ] Export to multiple formats (SRT, VTT, etc.)
- [ ] Keyboard shortcuts for common actions
- [ ] Menu bar integration
