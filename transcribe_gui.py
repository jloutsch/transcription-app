#!/usr/bin/env python3
"""
GUI Transcription App using Faster Whisper
Designed following Apple Human Interface Guidelines for macOS
"""

import os
import sys
import threading
import json
import multiprocessing
from pathlib import Path
from tkinter import Tk, Frame, Label, Button, Text, Scrollbar, filedialog, StringVar, BooleanVar, IntVar, Checkbutton
from tkinter import ttk
import tkinter as tk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

from faster_whisper import WhisperModel

# Try to import pyannote for speaker diarization (optional)
try:
    from pyannote.audio import Pipeline
    HAS_DIARIZATION = True
except ImportError:
    HAS_DIARIZATION = False
    Pipeline = None

# Configuration file path
CONFIG_FILE = Path.home() / '.transcribe_anything_config.json'

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

# macOS System Colors (HIG-compliant)
COLORS = {
    'bg': '#FFFFFF',
    'secondary_bg': '#F5F5F7',
    'tertiary_bg': '#EBEBEB',
    'accent': '#007AFF',
    'accent_hover': '#0051D5',
    'success': '#34C759',
    'success_hover': '#248A3D',
    'text_primary': '#000000',
    'text_secondary': '#3C3C43',
    'text_tertiary': '#48484A',
    'separator': '#D1D1D6',
    'control_bg': '#FFFFFF',
    'control_border': '#C7C7CC',
}


class MacButton(tk.Frame):
    """macOS-style button following HIG specifications"""
    def __init__(self, parent, text, command, style='primary',
                 font_size=13, state='normal'):
        # Button styles per HIG
        if style == 'primary':
            bg = COLORS['accent']
            fg = '#FFFFFF'
            hover_bg = COLORS['accent_hover']
        elif style == 'success':
            bg = COLORS['success']
            fg = '#FFFFFF'
            hover_bg = COLORS['success_hover']
        else:  # secondary
            bg = COLORS['control_bg']
            fg = COLORS['text_primary']
            hover_bg = COLORS['tertiary_bg']

        super().__init__(parent, bg=bg, highlightthickness=1,
                        highlightbackground=COLORS['control_border'] if style == 'secondary' else bg)

        self.command = command
        self.bg_color = bg
        self.hover_color = hover_bg
        self.fg_color = fg
        self.state = state
        self.style = style

        # HIG: Button heights should be 22-32pt, font 13pt regular/medium
        self.label = tk.Label(self, text=text, bg=bg, fg=fg,
                             font=('SF Pro Text', font_size, 'normal'),
                             cursor='hand2' if state == 'normal' else 'arrow')
        self.label.pack(padx=16, pady=6)  # HIG spacing

        # Apply disabled styling if button starts disabled
        if state == 'disabled':
            # Make disabled primary buttons still visible but muted
            if style == 'primary':
                disabled_bg = '#B3D7FF'  # Light blue (muted accent color)
                disabled_fg = '#FFFFFF'
            else:
                disabled_bg = COLORS['tertiary_bg']
                disabled_fg = '#8E8E93'
            self.configure(bg=disabled_bg)
            self.label.configure(fg=disabled_fg, bg=disabled_bg)

        if state == 'normal':
            self.bind('<Button-1>', lambda e: self._on_click())
            self.label.bind('<Button-1>', lambda e: self._on_click())
            self.bind('<Enter>', self._on_enter)
            self.bind('<Leave>', self._on_leave)
            self.label.bind('<Enter>', self._on_enter)
            self.label.bind('<Leave>', self._on_leave)

    def _on_click(self):
        print(f"DEBUG: Button clicked! State: {self.state}, Text: {self.label.cget('text')}")
        if self.state == 'normal' and self.command:
            print("DEBUG: Calling command...")
            self.command()
        else:
            print(f"DEBUG: Button is disabled or has no command")

    def _on_enter(self, event):
        if self.state == 'normal':
            self.configure(bg=self.hover_color)
            self.label.configure(bg=self.hover_color)

    def _on_leave(self, event):
        if self.state == 'normal':
            self.configure(bg=self.bg_color)
            self.label.configure(bg=self.bg_color)

    def config(self, **kwargs):
        if 'state' in kwargs:
            self.state = kwargs['state']
            if self.state == 'disabled':
                # Different disabled styling for primary vs secondary buttons
                if self.style == 'primary':
                    disabled_bg = '#B3D7FF'  # Light blue
                    disabled_fg = '#FFFFFF'
                else:
                    disabled_bg = COLORS['tertiary_bg']
                    disabled_fg = '#8E8E93'
                self.configure(cursor='arrow', bg=disabled_bg)
                self.label.configure(cursor='arrow', fg=disabled_fg, bg=disabled_bg)
                # Remove event bindings when disabled
                self.unbind('<Button-1>')
                self.label.unbind('<Button-1>')
                self.unbind('<Enter>')
                self.unbind('<Leave>')
                self.label.unbind('<Enter>')
                self.label.unbind('<Leave>')
            else:
                self.configure(cursor='hand2', bg=self.bg_color)
                self.label.configure(cursor='hand2', fg=self.fg_color, bg=self.bg_color)
                # Add event bindings when enabled
                self.bind('<Button-1>', lambda e: self._on_click())
                self.label.bind('<Button-1>', lambda e: self._on_click())
                self.bind('<Enter>', self._on_enter)
                self.bind('<Leave>', self._on_leave)
                self.label.bind('<Enter>', self._on_enter)
                self.label.bind('<Leave>', self._on_leave)


class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcribe Anything")
        self.root.geometry("600x1050")  # Adjusted height for diarization settings
        self.root.configure(bg=COLORS['bg'])
        self.root.minsize(600, 1050)  # Ensure Start button is always visible

        self.model = None
        self.output_folder = None
        self.file_queue = []
        self.is_processing = False
        self.remember_folder = BooleanVar()

        # Performance settings
        self.cpu_cores = multiprocessing.cpu_count()
        self.cpu_threads = IntVar(value=self.cpu_cores)  # Use all cores by default

        # Output format settings
        self.output_format = StringVar(value="with_timestamps")  # "with_timestamps" or "plain_text"

        # Speaker diarization settings
        self.enable_diarization = BooleanVar(value=False)
        self.hf_token = StringVar(value="")
        self.num_speakers = IntVar(value=0)  # 0 = auto-detect
        self.diarization_pipeline = None

        # Progress tracking (thread-safe)
        self.progress_lock = threading.Lock()
        self.current_progress = 0.0  # 0-100
        self.processed_segments = 0
        self.total_segments_estimate = 0

        # Selected file tracking
        self.selected_file_index = None

        # Stop flag for canceling transcription
        self.stop_requested = False

        # Load saved configuration
        self.load_config()

        self.setup_ui()

        # Set default folder if saved
        if self.output_folder:
            display_path = self.output_folder if len(self.output_folder) < 50 else "…" + self.output_folder[-47:]
            self.folder_var.set(display_path)
            self.update_start_button()

    def setup_ui(self):
        # Add menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About Transcribe Anything", command=self.show_about)

        # HIG: Use 20pt margins on macOS windows
        main_container = Frame(self.root, bg=COLORS['bg'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Header section
        header_frame = Frame(main_container, bg=COLORS['bg'])
        header_frame.pack(fill='x', pady=(0, 24))

        # HIG: Large title uses 26pt SF Pro Display Bold
        title = Label(header_frame, text="Transcribe Anything",
                     font=('SF Pro Display', 26, 'bold'),
                     bg=COLORS['bg'],
                     fg=COLORS['text_primary'])
        title.pack(anchor='w')

        # HIG: Body text uses 13pt SF Pro Text Regular
        subtitle = Label(header_frame,
                        text="Convert audio and video files to text using AI",
                        font=('SF Pro Text', 13),
                        bg=COLORS['bg'],
                        fg=COLORS['text_secondary'])
        subtitle.pack(anchor='w', pady=(4, 0))

        # Separator (HIG uses 1pt lines)
        separator1 = Frame(main_container, height=1, bg=COLORS['separator'])
        separator1.pack(fill='x', pady=(0, 16))

        # Output folder section
        folder_label = Label(main_container, text="Output Folder",
                           font=('SF Pro Text', 13, 'bold'),
                           bg=COLORS['bg'],
                           fg=COLORS['text_primary'])
        folder_label.pack(anchor='w', pady=(0, 8))

        folder_row = Frame(main_container, bg=COLORS['bg'])
        folder_row.pack(fill='x', pady=(0, 16))

        # HIG: Text fields have specific styling
        self.folder_var = StringVar(value="No folder selected")
        folder_display = Label(folder_row, textvariable=self.folder_var,
                             font=('SF Pro Text', 13),
                             bg=COLORS['control_bg'],
                             fg=COLORS['text_secondary'],
                             anchor='w',
                             relief='solid',
                             borderwidth=1,
                             padx=12,
                             pady=8)
        folder_display.pack(side='left', fill='x', expand=True, padx=(0, 8))

        choose_btn = MacButton(folder_row, text="Choose…",
                              command=self.choose_output_folder,
                              style='secondary',
                              font_size=13)
        choose_btn.pack(side='left')

        # Remember folder checkbox in a well (HIG pattern for settings)
        remember_well = Frame(main_container,
                             bg=COLORS['secondary_bg'],
                             relief='flat',
                             borderwidth=0)
        remember_well.pack(fill='x', pady=(0, 16))

        remember_check = Checkbutton(remember_well,
                                     text="Remember this folder for future sessions",
                                     variable=self.remember_folder,
                                     font=('SF Pro Text', 12),
                                     bg=COLORS['secondary_bg'],
                                     fg=COLORS['text_primary'],
                                     activebackground=COLORS['secondary_bg'],
                                     activeforeground=COLORS['text_primary'],
                                     selectcolor=COLORS['secondary_bg'],
                                     highlightthickness=0,
                                     command=self.save_config)
        remember_check.pack(anchor='w', padx=12, pady=10)

        # Performance settings section
        perf_label = Label(main_container, text="Performance",
                          font=('SF Pro Text', 13, 'bold'),
                          bg=COLORS['bg'],
                          fg=COLORS['text_primary'])
        perf_label.pack(anchor='w', pady=(0, 8))

        # Performance settings in a well
        perf_well = Frame(main_container,
                         bg=COLORS['secondary_bg'],
                         relief='flat',
                         borderwidth=0)
        perf_well.pack(fill='x', pady=(0, 16))

        # CPU Threads setting
        cpu_frame = Frame(perf_well, bg=COLORS['secondary_bg'])
        cpu_frame.pack(fill='x', padx=12, pady=(10, 5))

        Label(cpu_frame,
              text=f"CPU Threads (1-{self.cpu_cores})",
              font=('SF Pro Text', 12),
              bg=COLORS['secondary_bg'],
              fg=COLORS['text_primary']).pack(side='left')

        cpu_spinbox = ttk.Spinbox(cpu_frame,
                                  from_=1,
                                  to=self.cpu_cores,
                                  textvariable=self.cpu_threads,
                                  width=10,
                                  command=self.save_config)
        cpu_spinbox.pack(side='right')

        # Output Format setting
        output_frame = Frame(perf_well, bg=COLORS['secondary_bg'])
        output_frame.pack(fill='x', padx=12, pady=(10, 5))

        Label(output_frame,
              text="Output Format",
              font=('SF Pro Text', 12),
              bg=COLORS['secondary_bg'],
              fg=COLORS['text_primary']).pack(anchor='w')

        # Radio buttons for output format
        from tkinter import Radiobutton
        radio_frame = Frame(output_frame, bg=COLORS['secondary_bg'])
        radio_frame.pack(anchor='w', pady=(5, 0))

        self.radio_timestamp = Radiobutton(radio_frame,
                   text="With timestamps (for subtitles)",
                   variable=self.output_format,
                   value="with_timestamps",
                   font=('SF Pro Text', 11),
                   bg=COLORS['secondary_bg'],
                   fg=COLORS['text_primary'],
                   activebackground=COLORS['secondary_bg'],
                   activeforeground=COLORS['text_primary'],
                   selectcolor=COLORS['secondary_bg'],
                   highlightthickness=0,
                   command=self.save_config)
        self.radio_timestamp.pack(anchor='w')

        self.radio_plaintext = Radiobutton(radio_frame,
                   text="Plain text (conversational)",
                   variable=self.output_format,
                   value="plain_text",
                   font=('SF Pro Text', 11),
                   bg=COLORS['secondary_bg'],
                   fg=COLORS['text_primary'],
                   activebackground=COLORS['secondary_bg'],
                   activeforeground=COLORS['text_primary'],
                   selectcolor=COLORS['secondary_bg'],
                   highlightthickness=0,
                   command=self.save_config)
        self.radio_plaintext.pack(anchor='w')

        # Speaker Diarization section (if available)
        if HAS_DIARIZATION:
            diarization_frame = Frame(perf_well, bg=COLORS['secondary_bg'])
            diarization_frame.pack(fill='x', padx=12, pady=(15, 5))

            Label(diarization_frame,
                  text="Speaker Diarization (identify different speakers)",
                  font=('SF Pro Text', 12),
                  bg=COLORS['secondary_bg'],
                  fg=COLORS['text_primary']).pack(anchor='w')

            # Enable diarization checkbox
            Checkbutton(diarization_frame,
                       text="Enable speaker identification",
                       variable=self.enable_diarization,
                       font=('SF Pro Text', 11),
                       bg=COLORS['secondary_bg'],
                       fg=COLORS['text_primary'],
                       activebackground=COLORS['secondary_bg'],
                       activeforeground=COLORS['text_primary'],
                       selectcolor=COLORS['secondary_bg'],
                       highlightthickness=0,
                       command=self.save_config).pack(anchor='w', pady=(5, 5))

            # HF Token entry
            token_frame = Frame(diarization_frame, bg=COLORS['secondary_bg'])
            token_frame.pack(fill='x', pady=(5, 5))

            Label(token_frame,
                  text="Hugging Face Token:",
                  font=('SF Pro Text', 10),
                  bg=COLORS['secondary_bg'],
                  fg=COLORS['text_secondary']).pack(side='left')

            token_entry = ttk.Entry(token_frame,
                                    textvariable=self.hf_token,
                                    width=30,
                                    show="*")
            token_entry.pack(side='left', padx=(5, 0))
            token_entry.bind('<FocusOut>', lambda e: self.save_config())

            # Number of speakers
            speakers_frame = Frame(diarization_frame, bg=COLORS['secondary_bg'])
            speakers_frame.pack(fill='x', pady=(5, 0))

            Label(speakers_frame,
                  text="Speakers (0=auto):",
                  font=('SF Pro Text', 10),
                  bg=COLORS['secondary_bg'],
                  fg=COLORS['text_secondary']).pack(side='left')

            speaker_spinbox = ttk.Spinbox(speakers_frame,
                                          from_=0,
                                          to=10,
                                          textvariable=self.num_speakers,
                                          width=10,
                                          command=self.save_config)
            speaker_spinbox.pack(side='left', padx=(5, 0))

            # Diarization info
            Label(diarization_frame,
                  text="⚠️ Requires HF account & accepting model terms (see Help > About)",
                  font=('SF Pro Text', 9),
                  bg=COLORS['secondary_bg'],
                  fg=COLORS['text_tertiary']).pack(anchor='w', pady=(5, 0))

        # Performance info label
        perf_info = Label(perf_well,
                         text="Higher values use more CPU but may speed up transcription",
                         font=('SF Pro Text', 10),
                         bg=COLORS['secondary_bg'],
                         fg=COLORS['text_tertiary'])
        perf_info.pack(anchor='w', padx=12, pady=(5, 10))

        # Drop zone
        drop_label = Label(main_container, text="Files",
                         font=('SF Pro Text', 13, 'bold'),
                         bg=COLORS['bg'],
                         fg=COLORS['text_primary'])
        drop_label.pack(anchor='w', pady=(0, 8))

        # HIG: Drop zones should be clearly indicated
        self.drop_frame = Frame(main_container,
                               bg=COLORS['secondary_bg'],
                               relief='solid',
                               borderwidth=2,
                               highlightbackground=COLORS['separator'],
                               highlightcolor=COLORS['accent'],
                               highlightthickness=0)
        self.drop_frame.pack(fill='both', expand=False, pady=(0, 16))
        self.drop_frame.config(height=150)  # Fixed height for drop zone

        if HAS_DND:
            drop_text = "Drop files here or use the button below"
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        else:
            drop_text = "Use the button below to add files"

        drop_icon = Label(self.drop_frame,
                         text="📁",
                         font=('SF Pro Text', 48),
                         bg=COLORS['secondary_bg'],
                         fg=COLORS['text_tertiary'])
        drop_icon.pack(pady=(40, 8))

        drop_label_text = Label(self.drop_frame,
                               text=drop_text,
                               font=('SF Pro Text', 13),
                               bg=COLORS['secondary_bg'],
                               fg=COLORS['text_secondary'])
        drop_label_text.pack(pady=(0, 40))

        # Add Files button
        add_btn = MacButton(main_container, text="Add Files…",
                          command=self.add_files,
                          style='secondary',
                          font_size=13)
        add_btn.pack(anchor='center', pady=(0, 16))

        # File list
        list_label = Label(main_container, text="Queue",
                         font=('SF Pro Text', 13, 'bold'),
                         bg=COLORS['bg'],
                         fg=COLORS['text_primary'])
        list_label.pack(anchor='w', pady=(0, 8))

        # HIG: Lists should have proper scrolling
        list_container = Frame(main_container, bg=COLORS['bg'])
        list_container.pack(fill='both', expand=False, pady=(0, 8))

        scrollbar = Scrollbar(list_container)
        scrollbar.pack(side='right', fill='y')

        self.file_listbox = Text(list_container,
                                height=5,
                                font=('SF Pro Text', 12),
                                bg=COLORS['control_bg'],
                                fg=COLORS['text_primary'],
                                relief='solid',
                                borderwidth=1,
                                padx=12,
                                pady=8,
                                yscrollcommand=scrollbar.set,
                                state='disabled',
                                wrap='word',
                                cursor='arrow')
        self.file_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # Bind click event for file selection
        self.file_listbox.bind('<Button-1>', self.on_file_click)

        # Remove selected file button
        self.remove_btn = MacButton(main_container, text="Remove Selected",
                                   command=self.remove_selected_file,
                                   style='secondary',
                                   font_size=12)
        self.remove_btn.pack(anchor='center', pady=(0, 16))
        self.remove_btn.config(state='disabled')  # Disabled until file is selected

        # Separator
        separator2 = Frame(main_container, height=1, bg=COLORS['separator'])
        separator2.pack(fill='x', pady=(0, 16))

        # Status and progress
        self.status_var = StringVar(value="Ready")
        status_label = Label(main_container, textvariable=self.status_var,
                           font=('SF Pro Text', 12),
                           bg=COLORS['bg'],
                           fg=COLORS['text_secondary'])
        status_label.pack(anchor='w', pady=(0, 8))

        # HIG: Progress indicators
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Mac.Horizontal.TProgressbar",
                       troughcolor=COLORS['separator'],
                       background=COLORS['accent'],
                       borderwidth=0,
                       thickness=6)

        self.progress = ttk.Progressbar(main_container,
                                       mode='determinate',
                                       style="Mac.Horizontal.TProgressbar")
        self.progress.pack(fill='x', pady=(0, 16))
        self.progress['value'] = 0  # Start at 0, not showing progress

        # Primary action button - make it prominent and ensure it's visible
        button_container = Frame(main_container, bg=COLORS['bg'])
        button_container.pack(fill='x', pady=(8, 0))

        self.start_button = MacButton(button_container, text="Start Transcription",
                                     command=self.start_transcription,
                                     style='primary',
                                     font_size=14,
                                     state='disabled')
        self.start_button.pack(side='right')

        self.stop_button = MacButton(button_container, text="Stop",
                                    command=self.stop_transcription,
                                    style='secondary',
                                    font_size=14)
        self.stop_button.pack(side='right', padx=(0, 8))
        self.stop_button.pack_forget()  # Hidden by default

    def load_config(self):
        """Load saved configuration from file"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.output_folder = config.get('output_folder')
                    self.remember_folder.set(config.get('remember_folder', False))
                    self.cpu_threads.set(config.get('cpu_threads', self.cpu_cores))
                    self.output_format.set(config.get('output_format', 'with_timestamps'))
                    self.enable_diarization.set(config.get('enable_diarization', False))
                    self.hf_token.set(config.get('hf_token', ''))
                    self.num_speakers.set(config.get('num_speakers', 0))
        except Exception as e:
            print(f"Could not load config: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'output_folder': self.output_folder if self.remember_folder.get() else None,
                'remember_folder': self.remember_folder.get(),
                'cpu_threads': self.cpu_threads.get(),
                'output_format': self.output_format.get(),
                'enable_diarization': self.enable_diarization.get(),
                'hf_token': self.hf_token.get(),
                'num_speakers': self.num_speakers.get()
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Could not save config: {e}")

    def show_about(self):
        """Show About dialog with AI model information"""
        from tkinter import messagebox
        diarization_info = ""
        if HAS_DIARIZATION:
            diarization_info = (
                "\n\nSpeaker Diarization:\n"
                "• pyannote/speaker-diarization-3.1\n"
                "• Requires Hugging Face account\n\n"
                "Setup Instructions:\n"
                "1. Create account: huggingface.co/join\n"
                "2. Accept terms at:\n"
                "   huggingface.co/pyannote/speaker-diarization-3.1\n"
                "   huggingface.co/pyannote/segmentation-3.0\n"
                "3. Generate token: huggingface.co/settings/tokens\n"
                "4. Enter token in app settings\n"
            )

        about_text = (
            "Transcribe Anything\n\n"
            "Local, privacy-focused transcription\n\n"
            "AI Models:\n"
            f"• OpenAI Whisper ({MODEL_SIZE})\n"
            f"• Device: {DEVICE}\n"
            f"• Compute: {COMPUTE_TYPE}"
            f"{diarization_info}\n"
            "All processing happens locally on your computer.\n"
            "No data is sent to external services.\n\n"
            "Powered by faster-whisper & pyannote.audio"
        )
        messagebox.showinfo("About Transcribe Anything", about_text)

    def choose_output_folder(self):
        # Default to user's home directory, or saved folder if available
        initial_dir = self.output_folder if self.output_folder else str(Path.home())

        folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=initial_dir
        )

        if folder:
            self.output_folder = folder
            display_path = folder if len(folder) < 50 else "…" + folder[-47:]
            self.folder_var.set(display_path)
            self.save_config()
            self.update_start_button()

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Audio or Video Files",
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
            file_path = file_path.strip('{}')
            path = Path(file_path)
            if path.is_file() and path.suffix in MEDIA_EXTENSIONS:
                if path not in self.file_queue:
                    self.file_queue.append(path)

        self.update_file_list()
        self.update_start_button()

    def update_file_list(self):
        self.file_listbox.config(state='normal')
        self.file_listbox.delete(1.0, 'end')

        # Clear any existing tags
        self.file_listbox.tag_delete('selected')

        if self.file_queue:
            for i, file_path in enumerate(self.file_queue, 1):
                line_start = self.file_listbox.index('end-1c')
                self.file_listbox.insert('end', f"{i}. {file_path.name}\n")
                line_end = self.file_listbox.index('end-1c')

                # Highlight selected file
                if self.selected_file_index == i - 1:
                    self.file_listbox.tag_add('selected', line_start, line_end)
                    self.file_listbox.tag_config('selected', background=COLORS['accent'], foreground='white')
        else:
            self.file_listbox.insert('end', "No files added")
            self.selected_file_index = None

        self.file_listbox.config(state='disabled')
        self.update_remove_button()

    def update_remove_button(self):
        """Enable/disable remove button based on selection and processing state"""
        if self.selected_file_index is not None and not self.is_processing:
            self.remove_btn.config(state='normal')
        else:
            self.remove_btn.config(state='disabled')

    def on_file_click(self, event):
        """Handle click on file list to select a file"""
        if not self.file_queue or self.is_processing:
            return

        # Get the line number that was clicked
        index = self.file_listbox.index(f"@{event.x},{event.y}")
        line_num = int(index.split('.')[0])

        # Convert line number to file index (0-based)
        file_index = line_num - 1

        if 0 <= file_index < len(self.file_queue):
            self.selected_file_index = file_index
            self.update_file_list()

    def remove_selected_file(self):
        """Remove the selected file from the queue"""
        if self.selected_file_index is not None and not self.is_processing:
            if 0 <= self.selected_file_index < len(self.file_queue):
                removed_file = self.file_queue.pop(self.selected_file_index)
                print(f"Removed file from queue: {removed_file.name}")

                # Clear selection
                self.selected_file_index = None

                # Update UI
                self.update_file_list()
                self.update_start_button()

    def update_start_button(self):
        if self.file_queue and self.output_folder and not self.is_processing:
            self.start_button.config(state='normal')
        else:
            self.start_button.config(state='disabled')

    def start_transcription(self):
        print("DEBUG: Start transcription clicked!")
        print(f"DEBUG: Files in queue: {len(self.file_queue)}")
        print(f"DEBUG: Output folder: {self.output_folder}")
        print(f"DEBUG: CPU Threads: {self.cpu_threads.get()}")

        self.is_processing = True
        self.stop_requested = False

        # Update button visibility
        self.start_button.pack_forget()
        self.stop_button.pack(side='right', padx=(0, 8))

        # Lock output format during transcription
        self.radio_timestamp.config(state='disabled')
        self.radio_plaintext.config(state='disabled')
        self.status_var.set(f"Loading OpenAI Whisper ({MODEL_SIZE}) model…")
        self.progress.config(mode='determinate', value=0)

        # Reset progress tracking variables to prevent showing stale values
        with self.progress_lock:
            self.current_progress = 0.0
            self.processed_segments = 0
            self.total_segments_estimate = 0

        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()

    def stop_transcription(self):
        """Request to stop the current transcription"""
        print("DEBUG: Stop requested")
        self.stop_requested = True
        self.status_var.set("Stopping transcription (may take 30-60 seconds)...")
        self.stop_button.config(state='disabled')

    def process_files(self):
        try:
            # Initialize model with user-configured CPU threads
            cpu_threads = self.cpu_threads.get()
            print(f"Initializing model with {cpu_threads} CPU threads")
            self.model = WhisperModel(
                MODEL_SIZE,
                device=DEVICE,
                compute_type=COMPUTE_TYPE,
                cpu_threads=cpu_threads
            )

            # Initialize diarization pipeline if enabled
            if HAS_DIARIZATION and self.enable_diarization.get() and self.hf_token.get():
                try:
                    print("Initializing speaker diarization pipeline...")
                    self.root.after(0, lambda: self.status_var.set("Loading speaker diarization model..."))
                    self.diarization_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=self.hf_token.get()
                    )
                    print("Diarization pipeline loaded successfully")
                except Exception as e:
                    print(f"Failed to load diarization pipeline: {e}")
                    self.root.after(0, lambda: self.status_var.set(f"Diarization error: {str(e)[:50]}"))
                    self.diarization_pipeline = None
            else:
                self.diarization_pipeline = None

            # Switch to determinate progress mode
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.progress.config(mode='determinate', value=0))
            models_loaded = f"Loaded OpenAI Whisper ({MODEL_SIZE})"
            if self.diarization_pipeline:
                models_loaded += " + Speaker Diarization"
            self.root.after(0, lambda msg=models_loaded: self.status_var.set(msg))

            # Start polling progress from main thread
            self.root.after(100, self.poll_progress)

            total_files = len(self.file_queue)
            for i, file_path in enumerate(self.file_queue, 1):
                # Check if stop was requested
                if self.stop_requested:
                    print("Transcription stopped by user")
                    break

                # Update status
                self.root.after(0, lambda f=file_path, idx=i, total=total_files:
                              self.status_var.set(f"Transcribing {idx} of {total}: {f.name}"))

                # Update progress bar - show progress based on file completion
                progress_percent = int(((i - 1) / total_files) * 100)
                self.root.after(0, lambda p=progress_percent: self.progress.config(value=p))

                self.transcribe_file(file_path)

                # Update progress after file completes
                progress_percent = int((i / total_files) * 100)
                self.root.after(0, lambda p=progress_percent: self.progress.config(value=p))

            self.root.after(0, self.transcription_complete)

        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.progress.config(mode='determinate', value=0))
            self.is_processing = False

    def transcribe_file(self, file_path):
        try:
            print(f"Starting transcription of: {file_path}")
            output_file = Path(self.output_folder) / f"{file_path.stem}.txt"
            print(f"Output file will be: {output_file}")

            segments, info = self.model.transcribe(
                str(file_path),
                language=None,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            print(f"Transcription started. Language: {info.language}, Duration: {info.duration:.2f}s")

            # Reset progress tracking
            with self.progress_lock:
                self.current_progress = 0.0
                self.processed_segments = 0

            # Process segments one by one with progress updates
            segments_list = []
            total_duration = info.duration
            last_end_time = 0.0

            for segment in segments:
                # Check if stop was requested
                if self.stop_requested:
                    print("Stopping transcription during segment processing")
                    return  # Exit transcribe_file early

                segments_list.append(segment)
                last_end_time = segment.end

                # Update progress based on time processed vs total duration
                with self.progress_lock:
                    self.processed_segments = len(segments_list)
                    if total_duration > 0:
                        self.current_progress = min(95.0, (last_end_time / total_duration) * 100)

            # Set to 95% before writing file
            with self.progress_lock:
                self.current_progress = 95.0

            print(f"Got {len(segments_list)} segments")

            # Perform speaker diarization if enabled
            speaker_labels = {}  # Maps segment index to speaker label
            if self.diarization_pipeline:
                try:
                    print("Running speaker diarization...")
                    with self.progress_lock:
                        self.current_progress = 96.0

                    # Run diarization
                    num_speakers = self.num_speakers.get() if self.num_speakers.get() > 0 else None
                    diarization = self.diarization_pipeline(
                        str(file_path),
                        num_speakers=num_speakers
                    )

                    print(f"Diarization complete. Matching speakers to segments...")

                    # Match each transcription segment to a speaker
                    for idx, segment in enumerate(segments_list):
                        seg_start = segment.start
                        seg_end = segment.end
                        seg_mid = (seg_start + seg_end) / 2  # Use midpoint for matching

                        # Find which speaker was talking at the segment midpoint
                        for turn, _, speaker in diarization.itertracks(yield_label=True):
                            if turn.start <= seg_mid <= turn.end:
                                speaker_labels[idx] = speaker
                                break

                    print(f"Matched {len(speaker_labels)} segments to speakers")

                    with self.progress_lock:
                        self.current_progress = 98.0

                except Exception as e:
                    print(f"Diarization failed: {e}")
                    speaker_labels = {}

            # Write output based on selected format
            output_format = self.output_format.get()

            with open(output_file, 'w', encoding='utf-8') as f:
                # Header (always included)
                f.write(f"Transcript: {file_path.name}\n")
                f.write(f"Language: {info.language}\n")
                f.write(f"Duration: {info.duration:.2f} seconds\n")
                f.write(f"{'-'*80}\n\n")

                if output_format == "with_timestamps":
                    # Format with timestamps (for subtitles)
                    for idx, segment in enumerate(segments_list):
                        timestamp = f"[{self.format_timestamp(segment.start)} --> {self.format_timestamp(segment.end)}]"
                        speaker = speaker_labels.get(idx, "")
                        speaker_label = f"{speaker}: " if speaker else ""
                        f.write(f"{timestamp}\n{speaker_label}{segment.text.strip()}\n\n")
                else:
                    # Plain text format (conversational with speakers)
                    current_speaker = None
                    for idx, segment in enumerate(segments_list):
                        speaker = speaker_labels.get(idx, "")
                        # Add speaker label when speaker changes
                        if speaker and speaker != current_speaker:
                            if current_speaker is not None:  # Not first speaker
                                f.write("\n\n")
                            f.write(f"{speaker}: ")
                            current_speaker = speaker
                        f.write(f"{segment.text.strip()} ")
                    f.write("\n")

            print(f"Successfully wrote transcript to: {output_file}")
            return True

        except Exception as e:
            error_msg = f"Error transcribing {file_path.name}: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.status_var.set(error_msg))
            return False

    def format_timestamp(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def poll_progress(self):
        """Poll progress from main thread and update UI"""
        if self.is_processing:
            with self.progress_lock:
                progress_value = self.current_progress
                segments_info = f" ({self.processed_segments} segments)" if self.processed_segments > 0 else ""

            # Update progress bar
            self.progress['value'] = progress_value

            # Update status with percentage
            if progress_value > 0:
                self.status_var.set(f"Transcribing... {progress_value:.0f}%{segments_info}")

            # Force UI update
            self.progress.update_idletasks()

            # Schedule next poll
            self.root.after(500, self.poll_progress)

    def transcription_complete(self):
        self.progress.stop()
        self.progress.config(mode='determinate')

        # Update status based on whether it was stopped or completed
        if self.stop_requested:
            self.progress['value'] = 0
            self.status_var.set("Stopped by user")
        else:
            self.progress['value'] = 100
            self.status_var.set(f"Complete — Transcribed {len(self.file_queue)} file(s)")
            self.file_queue = []

        self.update_file_list()
        self.is_processing = False

        # Restore button visibility
        self.stop_button.pack_forget()
        self.stop_button.config(state='normal')  # Re-enable for next time
        self.start_button.pack(side='right')
        self.update_start_button()

        # Unlock output format
        self.radio_timestamp.config(state='normal')
        self.radio_plaintext.config(state='normal')

        # Progress bar will reset when next transcription starts
        # No delayed reset needed - prevents jumping when starting consecutive transcriptions


def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = Tk()

    app = TranscriptionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
