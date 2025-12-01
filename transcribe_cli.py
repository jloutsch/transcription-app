#!/usr/bin/env python3
"""
CLI Transcription Script for SwiftUI App
Accepts JSON requests and outputs progress updates
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Import transcription dependencies
from faster_whisper import WhisperModel

# Optional: WavLM for speaker diarization
try:
    from transformers import Wav2Vec2FeatureExtractor, WavLMForXVector
    import torch
    import torchaudio
    from sklearn.cluster import AgglomerativeClustering
    import numpy as np
    from collections import Counter
    HAS_WAVLM = True
except ImportError:
    HAS_WAVLM = False

# Optional: Pyannote for speaker diarization
try:
    from pyannote.audio import Pipeline
    HAS_PYANNOTE = True
except ImportError:
    HAS_PYANNOTE = False


def progress_print(value, message):
    """Output progress in format: PROGRESS:value:message"""
    print(f"PROGRESS:{value:.2f}:{message}", flush=True)


def output_print(file_path):
    """Output completed file path in format: OUTPUT:path"""
    print(f"OUTPUT:{file_path}", flush=True)


def transcribe_with_wavlm(model, audio_path, num_speakers, output_path):
    """Transcribe audio file with WavLM speaker diarization"""
    progress_print(0.1, f"Starting transcription: {Path(audio_path).name}")

    # Transcribe with Whisper
    segments, info = model.transcribe(
        audio_path,
        language=None,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=100),
        word_timestamps=True
    )

    progress_print(0.3, f"Transcribing ({info.language}, {info.duration:.1f}s)...")

    # Collect segments
    segments_list = list(segments)
    progress_print(0.6, f"Processing {len(segments_list)} segments...")

    # Collect all words
    all_words = []
    for segment in segments_list:
        if hasattr(segment, 'words') and segment.words:
            all_words.extend(segment.words)

    if not all_words:
        progress_print(0.7, "No words found, skipping diarization")
        speaker_labels = {}
    else:
        progress_print(0.7, f"Running speaker diarization on {len(all_words)} words...")

        # Load WavLM models
        feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained('microsoft/wavlm-base-plus-sv')
        wavlm_model = WavLMForXVector.from_pretrained('microsoft/wavlm-base-plus-sv')

        # Load audio
        waveform, sample_rate = torchaudio.load(audio_path)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
            sample_rate = 16000

        # Create sliding windows
        WINDOW_SIZE = 1.0
        WINDOW_STRIDE = 0.5

        segments_for_embedding = []
        total_duration = all_words[-1].end if all_words else 0

        current_time = 0
        while current_time < total_duration:
            window_start = current_time
            window_end = min(current_time + WINDOW_SIZE, total_duration)

            # Find words in this window
            window_word_indices = []
            for i, word in enumerate(all_words):
                word_center = (word.start + word.end) / 2
                if window_start <= word_center < window_end:
                    window_word_indices.append(i)

            if window_word_indices:
                segments_for_embedding.append({
                    'word_indices': window_word_indices,
                    'start': window_start,
                    'end': window_end
                })

            current_time += WINDOW_STRIDE

        progress_print(0.75, f"Extracting embeddings for {len(segments_for_embedding)} windows...")

        # Extract embeddings
        embeddings_list = []
        valid_segments = []

        for seg_info in segments_for_embedding:
            try:
                start_sample = int(seg_info['start'] * sample_rate)
                end_sample = int(seg_info['end'] * sample_rate)
                segment_audio = waveform[:, start_sample:end_sample]

                # Skip very short segments
                if segment_audio.shape[1] < 1600:  # Less than 0.1 seconds
                    continue

                inputs = feature_extractor(
                    segment_audio.squeeze().numpy(),
                    sampling_rate=16000,
                    return_tensors="pt",
                    padding=True
                )

                with torch.no_grad():
                    embedding = wavlm_model(**inputs).embeddings
                    embedding = torch.nn.functional.normalize(embedding, dim=-1)

                embeddings_list.append(embedding[0].cpu().numpy())
                valid_segments.append(seg_info)
            except Exception as e:
                continue

        if len(embeddings_list) < num_speakers:
            progress_print(0.8, f"Not enough data for {num_speakers} speakers, using 1")
            num_speakers = 1

        # Cluster embeddings
        embeddings_array = np.array(embeddings_list)
        progress_print(0.85, f"Clustering {len(embeddings_array)} embeddings...")

        clustering = AgglomerativeClustering(
            n_clusters=num_speakers,
            metric='cosine',
            linkage='average'
        )
        speaker_ids = clustering.fit_predict(embeddings_array)

        # Assign speaker labels to segments
        for i, seg_info in enumerate(valid_segments):
            seg_info['speaker'] = f"SPEAKER_{speaker_ids[i]:02d}"

        # Assign speakers to words using majority voting
        for word_idx, word in enumerate(all_words):
            speaker_votes = []
            for seg_info in valid_segments:
                if word_idx in seg_info['word_indices']:
                    speaker_votes.append(seg_info['speaker'])

            if speaker_votes:
                speaker_counts = Counter(speaker_votes)
                word.speaker = speaker_counts.most_common(1)[0][0]
            else:
                word.speaker = "SPEAKER_00"

    progress_print(0.9, "Writing transcript...")

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Transcript: {Path(audio_path).name}\n")
        f.write(f"Language: {info.language}\n")
        f.write(f"Duration: {info.duration:.2f} seconds\n")
        f.write("-" * 80 + "\n\n")

        # Group words by speaker
        if all_words and hasattr(all_words[0], 'speaker'):
            current_speaker = None
            current_text = []

            for word in all_words:
                speaker = getattr(word, 'speaker', 'SPEAKER_00')
                if speaker != current_speaker:
                    if current_text:
                        f.write(f"{current_speaker}: {' '.join(current_text)}\n\n")
                    current_speaker = speaker
                    current_text = [word.word.strip()]
                else:
                    current_text.append(word.word.strip())

            if current_text:
                f.write(f"{current_speaker}: {' '.join(current_text)}\n\n")
        else:
            # No diarization - just write segments
            for segment in segments_list:
                f.write(f"{segment.text.strip()}\n\n")

    progress_print(1.0, "Complete")
    return output_path


def transcribe_simple(model, audio_path, output_path):
    """Simple transcription without diarization"""
    progress_print(0.1, f"Starting transcription: {Path(audio_path).name}")

    segments, info = model.transcribe(
        audio_path,
        language=None,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=100)
    )

    progress_print(0.3, f"Transcribing ({info.language}, {info.duration:.1f}s)...")

    segments_list = list(segments)
    progress_print(0.7, f"Processing {len(segments_list)} segments...")

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Transcript: {Path(audio_path).name}\n")
        f.write(f"Language: {info.language}\n")
        f.write(f"Duration: {info.duration:.2f} seconds\n")
        f.write("-" * 80 + "\n\n")

        for segment in segments_list:
            f.write(f"{segment.text.strip()}\n\n")

    progress_print(1.0, "Complete")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='CLI Transcription Tool')
    parser.add_argument('--json', type=str, help='Path to JSON request file')
    args = parser.parse_args()

    if not args.json:
        print("Error: --json argument required", file=sys.stderr)
        sys.exit(1)

    # Read JSON request
    try:
        with open(args.json, 'r') as f:
            request = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse request
    audio_files = request.get('audioFiles', [])
    model_size = request.get('modelSize', 'medium')
    language = request.get('language')  # None for auto-detect
    enable_diarization = request.get('enableDiarization', False)
    diarization_method = request.get('diarizationMethod', 'wavlm')
    num_speakers = request.get('numSpeakers', 2)
    output_path_base = request.get('outputPath', str(Path.home() / 'Documents'))

    if not audio_files:
        print("Error: No audio files specified", file=sys.stderr)
        sys.exit(1)

    # Load Whisper model
    progress_print(0.0, f"Loading Whisper {model_size} model...")
    model = WhisperModel(model_size, device="auto", compute_type="auto")

    # Process each file
    total_files = len(audio_files)
    for i, audio_path in enumerate(audio_files, 1):
        file_progress_base = (i - 1) / total_files
        file_progress_range = 1.0 / total_files

        progress_print(file_progress_base, f"File {i}/{total_files}: {Path(audio_path).name}")

        # Determine output path
        output_file = Path(output_path_base) / f"{Path(audio_path).stem}.txt"

        try:
            if enable_diarization and diarization_method == 'wavlm' and HAS_WAVLM:
                output_file = transcribe_with_wavlm(model, audio_path, num_speakers, output_file)
            else:
                output_file = transcribe_simple(model, audio_path, output_file)

            output_print(str(output_file))
        except Exception as e:
            print(f"Error processing {audio_path}: {e}", file=sys.stderr)
            continue

    progress_print(1.0, f"All files complete ({total_files} files)")


if __name__ == '__main__':
    main()
