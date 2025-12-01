# TranscribeAnything Installation Guide

## ✅ Quick Status

**Good news!** The app is running successfully on your Mac (macOS 15.7.2).

If you built it locally, it should open without issues. If you download the DMG from GitHub, see the methods below.

---

## Opening the App on macOS

Since this app is not signed with an Apple Developer certificate, macOS Gatekeeper may block it when downloaded from the internet. Here's how to open it:

---

## Method 1: Right-Click Method (Recommended)

1. **Download** `TranscribeAnything.dmg` from the repository
2. **Double-click** the DMG to mount it
3. **Drag** `TranscribeAnything.app` to your Applications folder
4. **Right-click** (or Control+click) on `TranscribeAnything.app` in Applications
5. Select **"Open"** from the menu
6. Click **"Open"** in the security dialog that appears
7. The app will now open and be trusted for future launches

![Right-click to open](https://support.apple.com/library/content/dam/edam/applecare/images/en_US/macos/macos-ventura-right-click-open-unidentified-app.png)

---

## Method 2: System Settings (Alternative)

⚠️ **Note**: On macOS Sequoia (15.x), the "Open Anyway" button only appears **after** you've tried to open the app and it's been blocked. Follow these steps:

1. **Try to open the app normally** (double-click) - it will be blocked
2. **Immediately** go to **System Settings** → **Privacy & Security**
3. Scroll down to the **Security** section (may need to scroll past other settings)
4. Look for the message: *"TranscribeAnything.app was blocked..."* (appears at the top of Security section)
5. Click **"Open Anyway"** (appears only after the app was blocked)
6. Try opening the app again
7. Click **"Open"** in the confirmation dialog

**Important**: The "Open Anyway" button disappears after 30 seconds, so act quickly!

---

## Method 3: Terminal Command (Advanced)

If you're comfortable with Terminal:

```bash
# Remove quarantine attribute from the app
xattr -dr com.apple.quarantine /Applications/TranscribeAnything.app

# Launch the app
open /Applications/TranscribeAnything.app
```

This removes the quarantine flag that macOS applies to downloaded files.

---

## ⚠️ Security Notice

This app is **safe to use** but unsigned because:
- It's built from open-source code (you can review it on GitHub)
- It doesn't contain malware or harmful code
- It's a local application that processes audio files on your Mac
- No data is sent to external servers

**However**, you should only download it from the official GitHub repository to ensure authenticity.

---

## Why Is This Happening?

macOS Gatekeeper blocks apps that aren't:
1. Downloaded from the Mac App Store, OR
2. Signed with an Apple Developer certificate ($99/year)

Since this is an open-source project built without an Apple Developer account, it uses an "adhoc" signature (local development only).

---

## For Developers: Signing the App

If you want to sign the app with your own Apple Developer certificate:

### Step 1: Check Your Certificates

```bash
security find-identity -v -p codesigning
```

### Step 2: Sign the App

```bash
# Replace "Your Developer ID" with your actual certificate name
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  TranscribeAnything/TranscribeAnything.app
```

### Step 3: Verify Signature

```bash
codesign -dv TranscribeAnything/TranscribeAnything.app
```

### Step 4: Notarize (Optional, for Distribution)

```bash
# Package as DMG
./create_dmg.sh

# Submit for notarization
xcrun notarytool submit TranscribeAnything.dmg \
  --apple-id "your@email.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password"

# Staple the notarization ticket
xcrun stapler staple TranscribeAnything.dmg
```

---

## Troubleshooting

### "App is Damaged" Error

If you see *"TranscribeAnything is damaged and can't be opened"*:

```bash
# Remove quarantine attribute
xattr -dr com.apple.quarantine /Applications/TranscribeAnything.app
```

### App Won't Launch After Opening

1. Check that Python is installed: `python3 --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Check Console.app for error messages

### Permission Denied Errors

```bash
# Make the executable actually executable
chmod +x /Applications/TranscribeAnything.app/Contents/MacOS/TranscribeAnything
```

---

## First Launch Setup

After successfully opening the app:

1. **Grant Permissions**: The app may request permissions to access files
2. **Install Dependencies**: Make sure Python dependencies are installed
3. **Configure Settings**: Set your preferred Whisper model size
4. **Test with Audio**: Try transcribing a short audio file first

---

## Uninstallation

To remove the app:

1. Close TranscribeAnything if it's running
2. Drag `TranscribeAnything.app` from Applications to Trash
3. Empty Trash
4. (Optional) Remove config files: `rm -rf ~/.transcribe-anything/`

---

## Need Help?

- **GitHub Issues**: https://github.com/jloutsch/transcribe_anything/issues
- **Documentation**: Check the README.md in the repository
- **Build from Source**: Clone the repo and build it yourself

---

## Version Information

- **App Version**: 1.0
- **macOS Requirement**: macOS 13.0 or later
- **Architecture**: Apple Silicon (ARM64)
- **Python Requirement**: Python 3.8+

---

**Last Updated**: 2025-11-30
