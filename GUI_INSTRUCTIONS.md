# GUI Transcription App - Installation & Usage

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-gui.txt
```

### 2. Run the App

```bash
python transcribe_gui.py
```

## Features

- ✅ Drag and drop audio/video files (if tkinterdnd2 is installed)
- ✅ Browse and select files manually
- ✅ Choose custom output folder
- ✅ Visual progress indication
- ✅ Processes one file at a time
- ✅ Supports all major audio/video formats

## Supported Formats

**Video:** `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`
**Audio:** `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.aac`, `.wma`, `.opus`

## Creating a Mac .app Bundle

To create a standalone Mac application that you can keep in your Applications folder:

### Option 1: Using py2app (Recommended)

1. Install py2app:
```bash
pip install py2app
```

2. Create setup file:
```bash
cat > setup.py << 'EOF'
from setuptools import setup

APP = ['transcribe_gui.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['faster_whisper', 'tkinter', 'tkinterdnd2'],
    'iconfile': None,  # Add your icon file path here if you have one
    'plist': {
        'CFBundleName': 'Audio Transcriber',
        'CFBundleDisplayName': 'Audio Transcriber',
        'CFBundleIdentifier': 'com.transcriber.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
EOF
```

3. Build the app:
```bash
python setup.py py2app
```

4. Your app will be in the `dist/` folder. You can drag it to Applications:
```bash
open dist/
```

### Option 2: Using Automator (Simple but requires Python to be installed)

1. Open Automator
2. Create new "Application"
3. Add "Run Shell Script" action
4. Set shell to `/bin/bash`
5. Paste this script:
```bash
cd /Users/justin/Documents/Catapult_Dream_job/networking-videos
/usr/bin/python3 transcribe_gui.py
```
6. Save as "Audio Transcriber" in Applications

### Option 3: Using Platypus (Easy GUI wrapper)

1. Download Platypus from https://sveinbjorn.org/platypus
2. Open Platypus
3. Set Script Type: Python
4. Set Script Path: Browse to `transcribe_gui.py`
5. Set App Name: "Audio Transcriber"
6. Check "Accepts dropped items"
7. Click "Create App"

## Troubleshooting

### Drag and Drop Not Working

If drag and drop doesn't work, you can still use the "Add Files" button. To enable drag and drop:

```bash
pip install tkinterdnd2
```

### Model Download

On first run, the Whisper model will be downloaded (~1.5GB for medium model). This is a one-time download.

### Performance

- **Model size**: Default is "medium" (good balance of speed/accuracy)
- To change model size, edit `MODEL_SIZE` in `transcribe_gui.py`:
  - `tiny` - Fastest, least accurate
  - `base` - Fast
  - `small` - Balanced
  - `medium` - Good (default)
  - `large-v3` - Most accurate, slowest

### macOS Security

If you get a security warning when running the app:
1. Go to System Preferences → Security & Privacy
2. Click "Open Anyway"

Or run from Terminal:
```bash
xattr -dr com.apple.quarantine /path/to/Audio\ Transcriber.app
```

## Configuration

Edit these variables in `transcribe_gui.py`:

```python
MODEL_SIZE = "medium"  # Model size
DEVICE = "auto"        # "auto", "cpu", or "cuda"
COMPUTE_TYPE = "auto"  # "auto", "int8", "float16", "float32"
```

## Usage Tips

1. Select your output folder first
2. Add files (drag-drop or browse)
3. Click "Start Transcription"
4. Transcripts will be saved as `.txt` files with timestamps
5. Files are processed one at a time to manage memory

## Notes

- The app keeps running after transcription completes
- You can add more files and transcribe again
- Output files have the same name as input files with `.txt` extension
- If a transcript already exists, it will be overwritten
