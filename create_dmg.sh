#!/bin/bash
# Script to create a DMG for TranscribeAnything.app

set -e

APP_NAME="TranscribeAnything"
APP_PATH="TranscribeAnything/${APP_NAME}.app"
DMG_NAME="${APP_NAME}.dmg"
VOLUME_NAME="${APP_NAME}"
STAGING_DIR="dmg_staging"

echo "Creating DMG for ${APP_NAME}..."

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: ${APP_PATH} not found"
    exit 1
fi

# Clean up any previous staging directory
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

# Copy the app to staging
echo "Copying app to staging directory..."
cp -R "$APP_PATH" "$STAGING_DIR/"

# Create Applications symlink for easy installation
echo "Creating Applications symlink..."
ln -s /Applications "$STAGING_DIR/Applications"

# Remove any existing DMG
rm -f "$DMG_NAME"

# Create DMG
echo "Creating DMG..."
hdiutil create -volname "$VOLUME_NAME" \
    -srcfolder "$STAGING_DIR" \
    -ov -format UDZO \
    "$DMG_NAME"

# Clean up staging
rm -rf "$STAGING_DIR"

# Get DMG size
DMG_SIZE=$(du -h "$DMG_NAME" | cut -f1)

echo ""
echo "✅ DMG created successfully!"
echo "   File: ${DMG_NAME}"
echo "   Size: ${DMG_SIZE}"
echo ""
echo "To install: Double-click the DMG and drag TranscribeAnything.app to Applications"
