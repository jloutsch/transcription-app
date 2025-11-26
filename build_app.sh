#!/bin/bash
set -e

echo "🏗️  Building standalone Transcribe Anything.app..."
echo ""

# Check for Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "📦 Installing Python 3.11..."
    brew install python@3.11
fi

# Install python-tk
echo "📦 Installing Python tkinter..."
brew install python-tk@3.11 2>/dev/null || true

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create/recreate build virtual environment
echo "🐍 Creating build environment..."
rm -rf build_venv
python3.11 -m venv build_venv

# Activate and install dependencies
echo "📚 Installing build dependencies..."
source build_venv/bin/activate
pip install --quiet -r requirements.txt pyinstaller

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Find faster_whisper assets path
ASSETS_PATH=$(python3.11 -c "import faster_whisper; from pathlib import Path; print(Path(faster_whisper.__file__).parent / 'assets')")

# Generate/update spec file if needed
if [ ! -f "Transcribe Anything.spec" ]; then
    echo "📝 Generating spec file..."
    pyinstaller \
        --name="Transcribe Anything" \
        --windowed \
        --noupx \
        --icon=AppIcon.icns \
        --add-data="AppIcon.icns:." \
        --add-data="$ASSETS_PATH:faster_whisper/assets" \
        --noconfirm \
        transcribe_gui.py
fi

# Update spec file to disable compression (prevents decompression errors)
echo "📝 Updating spec file to disable compression..."
sed -i '' 's/noarchive=False/noarchive=True/g' "Transcribe Anything.spec"

# Build the app using the spec file
echo "⚙️  Building app with PyInstaller..."
pyinstaller --noconfirm "Transcribe Anything.spec"

# Show result
echo ""
echo "✅ Build complete!"
echo ""
echo "App location: $SCRIPT_DIR/dist/Transcribe Anything.app"
echo "App size: $(du -sh "dist/Transcribe Anything.app" | cut -f1)"
echo ""
echo "To test: open \"dist/Transcribe Anything.app\""
echo "To distribute: Compress the .app and share the .zip file"
echo ""
echo "Note: The Whisper model (~500MB-1.5GB) downloads on first use."
echo ""
