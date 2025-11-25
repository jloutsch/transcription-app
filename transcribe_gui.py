#!/usr/bin/env python3
"""
GUI Transcription App using Faster Whisper
Drag and drop audio/video files for transcription with visual progress
"""

import os
import sys
import threading
from pathlib import Path
from tkinter import Tk, Frame, Label, Button, Text, Scrollbar, filedialog, StringVar
from tkinter import ttk
import tkinter as tk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("Note: tkinterdnd2 not found. Drag-and-drop will not be available.")
    print("Install with: pip install tkinterdnd2")

from faster_whisper import WhisperModel
from tqdm import tqdm

# Configuration
MODEL_SIZE = "medium"
DEVICE = "auto"
COMPUTE_TYPE = "auto"
MEDIA_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".webm",
    ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma", ".opus",
    ".MP4", ".MOV", ".AVI", ".MKV", ".WEBM",
    ".MP3", ".WAV", ".M4A", ".FLAC", ".OGG", ".AAC", ".WMA", ".OPUS"
}


class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio/Video Transcription")
        self.root.geometry("700x600")
        self.root.configure(bg='#f0f0f0')

        self.model = None
        self.output_folder = None
        self.file_queue = []
        self.is_processing = False

        self.setup_ui()

    def setup_ui(self):
        # Title
        title = Label(self.root, text="🎙️ Audio/Video Transcription",
                     font=("Arial", 20, "bold"), bg='#f0f0f0')
        title.pack(pady=20)

        # Output folder selection
        folder_frame = Frame(self.root, bg='#f0f0f0')
        folder_frame.pack(pady=10, padx=20, fill='x')

        Label(folder_frame, text="Output Folder:", font=("Arial", 12),
              bg='#f0f0f0').pack(side='left', padx=5)

        self.folder_var = StringVar(value="Not selected")
        folder_label = Label(folder_frame, textvariable=self.folder_var,
                           font=("Arial", 10), bg='white', relief='sunken',
                           anchor='w', width=40)
        folder_label.pack(side='left', padx=5, fill='x', expand=True)

        Button(folder_frame, text="Choose", command=self.choose_output_folder,
               font=("Arial", 10), bg='#4CAF50', fg='white',
               padx=10, pady=5).pack(side='left', padx=5)

        # Drop zone or file selection
        self.drop_frame = Frame(self.root, bg='#e3f2fd', relief='solid',
                               borderwidth=2, height=150)
        self.drop_frame.pack(pady=20, padx=20, fill='both', expand=True)
        self.drop_frame.pack_propagate(False)

        if HAS_DND:
            self.drop_label = Label(self.drop_frame,
                                   text="📁 Drag and drop audio/video files here\n\nor click 'Add Files' button below",
                                   font=("Arial", 14), bg='#e3f2fd',
                                   fg='#1976d2')
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        else:
            self.drop_label = Label(self.drop_frame,
                                   text="📁 Click 'Add Files' button below to select files",
                                   font=("Arial", 14), bg='#e3f2fd',
                                   fg='#1976d2')

        self.drop_label.pack(expand=True)

        # Add Files button
        Button(self.root, text="Add Files", command=self.add_files,
               font=("Arial", 12, "bold"), bg='#2196F3', fg='white',
               padx=20, pady=10).pack(pady=10)

        # File list
        list_frame = Frame(self.root, bg='#f0f0f0')
        list_frame.pack(pady=10, padx=20, fill='both', expand=True)

        Label(list_frame, text="Files to transcribe:", font=("Arial", 11, "bold"),
              bg='#f0f0f0').pack(anchor='w')

        # File list with scrollbar
        scroll_frame = Frame(list_frame)
        scroll_frame.pack(fill='both', expand=True)

        scrollbar = Scrollbar(scroll_frame)
        scrollbar.pack(side='right', fill='y')

        self.file_listbox = Text(scroll_frame, height=6, font=("Arial", 10),
                                yscrollcommand=scrollbar.set, state='disabled')
        self.file_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # Progress section
        progress_frame = Frame(self.root, bg='#f0f0f0')
        progress_frame.pack(pady=10, padx=20, fill='x')

        self.status_var = StringVar(value="Ready")
        Label(progress_frame, textvariable=self.status_var,
              font=("Arial", 11), bg='#f0f0f0').pack(anchor='w')

        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate',
                                       length=300)
        self.progress.pack(fill='x', pady=5)

        # Start button
        self.start_button = Button(self.root, text="Start Transcription",
                                   command=self.start_transcription,
                                   font=("Arial", 12, "bold"), bg='#4CAF50',
                                   fg='white', padx=30, pady=10, state='disabled')
        self.start_button.pack(pady=20)

    def choose_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.folder_var.set(folder)
            self.update_start_button()

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Audio/Video Files",
            filetypes=[
                ("Media Files", " ".join(f"*{ext}" for ext in MEDIA_EXTENSIONS)),
                ("All Files", "*.*")
            ]
        )
        if files:
            self.add_files_to_queue(files)

    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        self.add_files_to_queue(files)

    def add_files_to_queue(self, files):
        for file_path in files:
            file_path = file_path.strip('{}')  # Remove braces from drag-drop
            path = Path(file_path)
            if path.is_file() and path.suffix in MEDIA_EXTENSIONS:
                if path not in self.file_queue:
                    self.file_queue.append(path)

        self.update_file_list()
        self.update_start_button()

    def update_file_list(self):
        self.file_listbox.config(state='normal')
        self.file_listbox.delete(1.0, 'end')
        for i, file_path in enumerate(self.file_queue, 1):
            self.file_listbox.insert('end', f"{i}. {file_path.name}\n")
        self.file_listbox.config(state='disabled')

    def update_start_button(self):
        if self.file_queue and self.output_folder and not self.is_processing:
            self.start_button.config(state='normal')
        else:
            self.start_button.config(state='disabled')

    def start_transcription(self):
        self.is_processing = True
        self.start_button.config(state='disabled')
        self.status_var.set("Loading model...")
        self.progress.start(10)

        # Run in separate thread to keep UI responsive
        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()

    def process_files(self):
        try:
            # Load model
            self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
            self.root.after(0, lambda: self.status_var.set("Model loaded! Starting transcription..."))

            # Process each file
            total_files = len(self.file_queue)
            for i, file_path in enumerate(self.file_queue, 1):
                self.root.after(0, lambda f=file_path, idx=i, total=total_files:
                              self.status_var.set(f"[{idx}/{total}] Transcribing: {f.name}"))

                self.transcribe_file(file_path)

            # Done
            self.root.after(0, self.transcription_complete)

        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self.root.after(0, lambda: self.progress.stop())
            self.is_processing = False

    def transcribe_file(self, file_path):
        try:
            output_file = Path(self.output_folder) / f"{file_path.stem}.txt"

            # Transcribe
            segments, info = self.model.transcribe(
                str(file_path),
                language=None,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Transcript: {file_path.name}\n")
                f.write(f"Language: {info.language}\n")
                f.write(f"Duration: {info.duration:.2f} seconds\n")
                f.write(f"{'-'*80}\n\n")

                for segment in segments:
                    timestamp = f"[{self.format_timestamp(segment.start)} --> {self.format_timestamp(segment.end)}]"
                    f.write(f"{timestamp}\n{segment.text.strip()}\n\n")

        except Exception as e:
            print(f"Error transcribing {file_path.name}: {e}")

    def format_timestamp(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def transcription_complete(self):
        self.progress.stop()
        self.status_var.set(f"✅ Complete! Transcribed {len(self.file_queue)} file(s)")
        self.file_queue = []
        self.update_file_list()
        self.is_processing = False
        self.update_start_button()


def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = Tk()

    app = TranscriptionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
