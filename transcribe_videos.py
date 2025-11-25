#!/usr/bin/env python3
"""
Batch transcription script using Faster Whisper
Transcribes all video and audio files in the current directory to text files.
"""

import os
import sys
from pathlib import Path
from faster_whisper import WhisperModel
from tqdm import tqdm

# Configuration
MODEL_SIZE = "medium"  # Options: tiny, base, small, medium, large-v2, large-v3
DEVICE = "auto"  # Options: auto, cpu, cuda
COMPUTE_TYPE = "auto"  # Options: auto, int8, float16, float32
MEDIA_EXTENSIONS = [
    # Video formats
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".MP4", ".MOV",
    # Audio formats
    ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma", ".opus",
    ".MP3", ".WAV", ".M4A", ".FLAC", ".OGG"
]
OUTPUT_DIR = "transcripts"


def get_media_files(directory="."):
    """Find all video and audio files in the directory"""
    media_files = []
    for ext in MEDIA_EXTENSIONS:
        media_files.extend(Path(directory).glob(f"*{ext}"))
    return sorted(media_files)


def transcribe_media(model, media_path, output_dir):
    """Transcribe a single video or audio file"""
    print(f"\n{'='*80}")
    print(f"Transcribing: {media_path.name}")
    print(f"{'='*80}")

    # Create output filename
    output_file = Path(output_dir) / f"{media_path.stem}.txt"

    # Skip if already transcribed
    if output_file.exists():
        print(f"⚠️  Transcript already exists: {output_file.name}")
        user_input = input("Do you want to re-transcribe? (y/N): ")
        if user_input.lower() != 'y':
            print("Skipping...")
            return

    try:
        # Transcribe
        segments, info = model.transcribe(
            str(media_path),
            language=None,  # Auto-detect language
            beam_size=5,
            vad_filter=True,  # Voice activity detection
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
        print(f"Duration: {info.duration:.2f} seconds")

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"Transcript: {media_path.name}\n")
            f.write(f"Language: {info.language}\n")
            f.write(f"Duration: {info.duration:.2f} seconds\n")
            f.write(f"{'-'*80}\n\n")

            # Write segments with timestamps
            for segment in tqdm(segments, desc="Processing segments"):
                timestamp = f"[{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}]"
                f.write(f"{timestamp}\n{segment.text.strip()}\n\n")

        print(f"✅ Saved transcript to: {output_file}")

    except Exception as e:
        print(f"❌ Error transcribing {media_path.name}: {e}")


def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def main():
    """Main function"""
    print("🎙️  Audio/Video Transcription Script (Faster Whisper)")
    print(f"Model: {MODEL_SIZE}")
    print(f"Device: {DEVICE}")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Find media files
    media_files = get_media_files()

    if not media_files:
        print("❌ No audio or video files found in the current directory")
        print(f"Looking for extensions: {', '.join(MEDIA_EXTENSIONS)}")
        sys.exit(1)

    print(f"\n📹 Found {len(media_files)} media file(s):\n")
    for i, media in enumerate(media_files, 1):
        size_mb = media.stat().st_size / (1024 * 1024)
        print(f"  {i}. {media.name} ({size_mb:.1f} MB)")

    # Ask for confirmation
    print(f"\nTranscripts will be saved to: {OUTPUT_DIR}/")
    user_input = input("\nProceed with transcription? (Y/n): ")
    if user_input.lower() == 'n':
        print("Cancelled.")
        sys.exit(0)

    # Load model
    print(f"\n⏳ Loading Whisper model '{MODEL_SIZE}'...")
    print("(First run will download the model, this may take a while)")

    try:
        model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        sys.exit(1)

    # Transcribe each media file
    for i, media_path in enumerate(media_files, 1):
        print(f"\n\n[{i}/{len(media_files)}]")
        transcribe_media(model, media_path, OUTPUT_DIR)

    print("\n" + "="*80)
    print("🎉 All done! Transcripts saved to:", OUTPUT_DIR)
    print("="*80)


if __name__ == "__main__":
    main()
