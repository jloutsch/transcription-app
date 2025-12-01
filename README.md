# Audio/Video Transcription App

Local, privacy-focused audio and video transcription using OpenAI's Whisper model (via Faster Whisper). No cloud services required - everything runs on your Mac.

## 📦 Download Native macOS App

**TranscribeAnything.dmg** - Ready-to-use macOS application with SwiftUI interface!

📥 [Download DMG from Releases](https://github.com/jloutsch/transcribe_anything/releases)

See [Installation Guide](docs/INSTALLATION_GUIDE.md) for setup instructions.

---

## Features

- 🎙️ **Three interfaces**: Native macOS app, Command-line, and Python GUI
- 🔒 **100% local processing** - No data sent to cloud services
- 📁 **Drag and drop support** in GUI versions
- 🎬 **Multiple formats**: MP4, MOV, MP3, WAV, M4A, FLAC, OGG, and more
- ⚡ **Fast transcription** using optimized Whisper models
- 📝 **Timestamped output** for easy reference
- 🌍 **Auto language detection**
- 👥 **Speaker diarization** (WavLM & PyAnnote.audio)

## Quick Start

### Option 1: macOS Native App (Easiest)

1. Download `TranscribeAnything.dmg`
2. Open the DMG and drag the app to Applications
3. Right-click the app → Open (first time only)
4. See [Installation Guide](docs/INSTALLATION_GUIDE.md) for details

### Option 2: Automated Installation (Python GUI)

```bash
# Clone the repository
git clone https://github.com/jloutsch/transcription-app.git
cd transcription-app

# Run the installer
./scripts/install.sh
```

The installer will:
- Check for and install Python 3.13 if needed (via Homebrew)
- Install required system packages (tkinter, ffmpeg)
- Create a virtual environment
- Install all Python dependencies
- Configure the launcher script

After installation, run the app with:
```bash
./scripts/launch_gui.sh
```

### Manual Installation

**Prerequisites:**
- Python 3.13 (recommended) or Python 3.11+
- Homebrew (for macOS dependencies)

```bash
# Clone the repository
git clone https://github.com/jloutsch/transcription-app.git
cd transcription-app

# Install system dependencies
brew install python@3.13 python-tk@3.13

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
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

## Creating a Standalone Mac .app (For Distribution)

Want to distribute a "just works" .app that others can download and use immediately? Run:

```bash
./build_app.sh
```

This creates `dist/Transcribe Anything.app` - a **completely standalone application** (~171MB) that includes:
- Python runtime
- All dependencies (faster-whisper, tkinter, etc.)
- App icon
- Everything needed to run

### Distributing the App

1. **Build the app:** `./build_app.sh`
2. **Compress it:** Right-click `dist/Transcribe Anything.app` → Compress
3. **Share the .zip file:** Upload to GitHub Releases, Dropbox, etc.
4. **Users download and run:** Extract .zip, double-click the app

**Note:** The Whisper model (~500MB-1.5GB) downloads automatically on first use.

### Mac Security

When users first run the app, macOS may show a security warning. Users should:
1. Right-click the app → "Open"
2. Or: System Settings → Privacy & Security → Click "Open Anyway"

### For Personal Use (Platypus Alternative)

If you only want to use this on your own machine:

1. Run `./install.sh` to set up dependencies
2. Run `./launch_gui.sh` to start the app
3. (Optional) Use [Platypus](https://sveinbjorn.org/platypus) to create a quick launcher:
   - Script: `launch_gui.sh`
   - Interface: None
   - Icon: Drag `AppIcon.icns`

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

## 📁 Repository Structure

```
transcription-app/
├── TranscribeAnything.dmg          # 📱 Native macOS app (ready to use)
├── transcribe_gui.py               # Python GUI application
├── transcribe_cli.py               # CLI interface
├── transcribe_videos.py            # Video transcriber
│
├── scripts/                        # Build & utility scripts
│   ├── build_app.sh                # Build macOS app
│   ├── create_dmg.sh               # Create DMG package
│   ├── install.sh                  # Automated installer
│   ├── launch_gui.sh               # GUI launcher
│   └── dev/                        # Development test scripts
│
├── docs/                           # Documentation
│   ├── INSTALLATION_GUIDE.md       # macOS installation help
│   ├── GUI_INSTRUCTIONS.md         # GUI usage guide
│   └── TEST_*.md                   # Test documentation
│
├── TranscribeAnything/             # SwiftUI app source code
└── tests/                          # Test suite (47% coverage)
```

