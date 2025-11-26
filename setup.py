"""
py2app setup file for Audio Transcriber
Run: python setup.py py2app
"""

from setuptools import setup

APP = ['transcribe_gui.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['faster_whisper', 'tkinter', 'tqdm'],
    'includes': ['tkinterdnd2'],
    'iconfile': 'AppIcon.icns',
    'plist': {
        'CFBundleName': 'Audio Transcriber',
        'CFBundleDisplayName': 'Audio Transcriber',
        'CFBundleIdentifier': 'com.transcriber.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    name='Audio Transcriber',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
