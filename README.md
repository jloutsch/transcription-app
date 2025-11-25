# Audio/Video Transcription App

Local, privacy-focused audio and video transcription using OpenAI's Whisper model (via Faster Whisper). No cloud services required - everything runs on your Mac.

## Features

- 🎙️ **Two interfaces**: Command-line and GUI
- 🔒 **100% local processing** - No data sent to cloud services
- 📁 **Drag and drop support** in GUI version
- 🎬 **Multiple formats**: MP4, MOV, MP3, WAV, M4A, FLAC, OGG, and more
- ⚡ **Fast transcription** using optimized Whisper models
- 📝 **Timestamped output** for easy reference
- 🌍 **Auto language detection**

## Quick Start

### Prerequisites

- Python 3.8 or higher
- FFmpeg (install with `brew install ffmpeg` on Mac)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/transcription-app.git
cd transcription-app

# Install dependencies
pip install -r requirements-gui.txt
```

## Usage

### Option 1: GUI Application (Recommended)

Run the graphical interface with drag-and-drop support:

```bash
python transcribe_gui.py
```

**Features:**
- Drag and drop audio/video files
- Choose output folder
- Visual progress indication
- Add multiple files to queue
- Processes one file at a time

**Steps:**
1. Click "Choose" to select output folder
2. Drag files into the drop zone (or click "Add Files")
3. Click "Start Transcription"
4. Transcripts saved as `.txt` files with timestamps

### Option 2: Command Line

Batch process all media files in a directory:

```bash
python transcribe_videos.py
```

The script will:
- Find all audio/video files in current directory
- Show you what it found
- Ask for confirmation
- Transcribe each file
- Save transcripts to `transcripts/` folder

## Supported Formats

### Video
`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`

### Audio
`.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.aac`, `.wma`, `.opus`

## Output Format

Transcripts are saved as text files with timestamps and metadata:

```
Transcript: example.mp4
Language: en
Duration: 125.50 seconds
--------------------------------------------------------------------------------

[00:00:00 --> 00:00:05]
Hello and welcome to this training session.

[00:00:05 --> 00:00:12]
Today we're going to discuss networking strategies.
```

## Configuration

Edit the model size in either script for different speed/accuracy tradeoffs:

```python
MODEL_SIZE = "medium"  # Options: tiny, base, small, medium, large-v3
```

**Model Comparison:**
- `tiny` - Fastest, least accurate (~1GB RAM)
- `base` - Fast, basic accuracy (~1GB RAM)
- `small` - Balanced (~2GB RAM)
- `medium` - Good accuracy (default, ~5GB RAM)
- `large-v3` - Best accuracy, slower (~10GB RAM)

## Creating a Mac .app Bundle

To create a standalone Mac application:

### Using py2app (Creates native .app)

```bash
pip install py2app
python setup.py py2app
```

Your app will be in the `dist/` folder. Drag it to Applications!

### Using Platypus (Easiest option)

1. Download [Platypus](https://sveinbjorn.org/platypus)
2. Open Platypus
3. Set Script Type: Python
4. Set Script Path: Browse to `transcribe_gui.py`
5. Set App Name: "Audio Transcriber"
6. Check "Accepts dropped items"
7. Click "Create App"

See [GUI_INSTRUCTIONS.md](GUI_INSTRUCTIONS.md) for detailed instructions.

## Performance Tips

- **First run**: Model will be downloaded (~500MB-1.5GB depending on size)
- **Processing time**: ~1x speed on modern hardware (10 min audio = ~10 min processing)
- **Memory**: Ensure enough RAM for selected model size
- **GPU**: Automatically uses GPU if available (CUDA on compatible hardware)

## Troubleshooting

### "Command not found: ffmpeg"
```bash
brew install ffmpeg
```

### Drag-and-drop not working in GUI
```bash
pip install tkinterdnd2
```
If still not working, use the "Add Files" button.

### macOS security warning
Go to System Preferences → Security & Privacy → Click "Open Anyway"

Or run:
```bash
xattr -dr com.apple.quarantine /path/to/app
```

## Privacy

- All processing happens locally on your machine
- No internet connection required (after initial model download)
- No data sent to external services
- Audio/video files never leave your computer

## Dependencies

- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Optimized Whisper implementation
- [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2) - Drag-and-drop support
- [tqdm](https://github.com/tqdm/tqdm) - Progress bars
- [FFmpeg](https://ffmpeg.org/) - Audio/video processing

## License

MIT License - feel free to use and modify!

## Contributing

Issues and pull requests welcome!

## Credits

Built with OpenAI's Whisper model and the excellent Faster Whisper implementation.
