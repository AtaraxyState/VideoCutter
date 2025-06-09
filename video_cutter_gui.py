#!/usr/bin/env python3
"""
Video Cutter GUI - A simple graphical interface for cutting videos at timestamps
Uses tkinter for the GUI and FFmpeg for video processing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
from pathlib import Path
from typing import List
import queue
import time

# Import the VideoCutter class from the original script
from video_cutter import VideoCutter


class VideoCutterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Cutter")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_prefix = tk.StringVar(value="output")
        # Default to user's Documents folder to avoid permission issues
        default_dir = os.path.expanduser("~/Documents/VideoCuts")
        self.output_dir = tk.StringVar(value=default_dir)
        self.scale_option = tk.StringVar(value="No scaling")
        self.timestamps = []
        
        # Queue for thread communication
        self.progress_queue = queue.Queue()
        
        # Create GUI elements
        self.create_widgets()
        
        # Check for FFmpeg
        self.check_ffmpeg()
        
        # Start checking progress queue
        self.check_progress_queue()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Input file selection
        ttk.Label(main_frame, text="Input Video:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_file, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_file).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1
        
        # Output prefix
        ttk.Label(main_frame, text="Output Prefix:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_prefix, width=20).grid(row=row, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        row += 1
        
        # Output directory
        ttk.Label(main_frame, text="Output Directory:").grid(row=row, column=0, sticky=tk.W, pady=5)
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        dir_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(dir_frame, textvariable=self.output_dir, width=40).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(dir_frame, text="Browse", command=self.browse_output_dir).grid(row=0, column=1)
        ttk.Label(dir_frame, text="(Leave empty for current directory)", font=("Arial", 8)).grid(row=1, column=0, columnspan=2, sticky=tk.W)
        row += 1
        
        # Scale options
        ttk.Label(main_frame, text="Scale:").grid(row=row, column=0, sticky=tk.W, pady=5)
        scale_frame = ttk.Frame(main_frame)
        scale_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        
        scale_options = ["No scaling", "720p", "480p", "360p", "240p", "Custom"]
        scale_combo = ttk.Combobox(scale_frame, textvariable=self.scale_option, values=scale_options, state="readonly", width=15)
        scale_combo.grid(row=0, column=0, sticky=tk.W)
        
        self.custom_scale = tk.StringVar(value="1280:720:1.5M")
        self.custom_entry = ttk.Entry(scale_frame, textvariable=self.custom_scale, width=20, state="disabled")
        self.custom_entry.grid(row=0, column=1, padx=(10, 0))
        
        scale_combo.bind('<<ComboboxSelected>>', self.on_scale_change)
        row += 1
        
        # Timestamps section
        ttk.Label(main_frame, text="Timestamps:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        
        # Timestamps frame
        timestamps_frame = ttk.Frame(main_frame)
        timestamps_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0), pady=5)
        timestamps_frame.columnconfigure(0, weight=1)
        timestamps_frame.rowconfigure(1, weight=1)
        
        # Add timestamp controls
        add_frame = ttk.Frame(timestamps_frame)
        add_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        add_frame.columnconfigure(0, weight=1)
        
        self.timestamp_entry = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.timestamp_entry, width=15).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(add_frame, text="Add", command=self.add_timestamp).grid(row=0, column=1, padx=(5, 0))
        ttk.Label(add_frame, text="(Format: HH:MM:SS, MM:SS, or SS)", font=("Arial", 8)).grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        # Timestamps listbox
        list_frame = ttk.Frame(timestamps_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.timestamps_listbox = tk.Listbox(list_frame, height=6)
        self.timestamps_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.timestamps_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.timestamps_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Remove button
        ttk.Button(list_frame, text="Remove Selected", command=self.remove_timestamp).grid(row=1, column=0, pady=(5, 0))
        
        row += 1
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        self.preview_button = ttk.Button(buttons_frame, text="📋 Preview", command=self.show_preview)
        self.preview_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cut_button = ttk.Button(buttons_frame, text="Cut Video", command=self.start_cutting, style="Accent.TButton")
        self.cut_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(buttons_frame, text="Stop", command=self.stop_cutting, state="disabled")
        self.stop_button.pack(side=tk.LEFT)
        
        row += 1
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Output section with tabs
        ttk.Label(main_frame, text="Output:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0), pady=5)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Create notebook for tabs
        self.output_notebook = ttk.Notebook(output_frame)
        self.output_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log tab
        log_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(log_frame, text="Process Log")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(log_frame, height=8, width=60)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Results tab
        results_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(results_frame, text="Results")
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results treeview
        columns = ("File", "Size", "Location")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure columns
        self.results_tree.heading("File", text="Filename")
        self.results_tree.heading("Size", text="Size (MB)")
        self.results_tree.heading("Location", text="Full Path")
        
        self.results_tree.column("File", width=200)
        self.results_tree.column("Size", width=100)
        self.results_tree.column("Location", width=300)
        
        # Results scrollbar
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        results_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        # Results buttons
        results_buttons = ttk.Frame(results_frame)
        results_buttons.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        ttk.Button(results_buttons, text="Open Folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(results_buttons, text="Play Selected", command=self.play_selected_video).pack(side=tk.LEFT)
        
        # Configure grid weights for resizing
        main_frame.rowconfigure(row-1, weight=1)  # Timestamps section
        main_frame.rowconfigure(row, weight=1)    # Output section
        
        # Bind Enter key to add timestamp
        self.root.bind('<Return>', lambda e: self.add_timestamp())
    
    def show_preview(self):
        """Show a preview window with segments that will be created."""
        # Validate inputs first
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input video file.")
            return
        
        if not self.timestamps:
            messagebox.showerror("Error", "Please add at least one timestamp.")
            return
        
        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("Error", "Input video file not found.")
            return
        
        # Get video info
        video_info = self.get_video_info()
        if not video_info:
            messagebox.showerror("Error", "Could not read video information.")
            return
        
        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Preview - Video Segments")
        preview_window.geometry("800x600")
        preview_window.resizable(True, True)
        
        # Main frame
        main_frame = ttk.Frame(preview_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_window.columnconfigure(0, weight=1)
        preview_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header info
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        ttk.Label(header_frame, text="📹 Video File:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(header_frame, text=os.path.basename(self.input_file.get())).grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(header_frame, text="⏱️ Duration:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(header_frame, text=video_info['duration']).grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(header_frame, text="📐 Resolution:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W)
        ttk.Label(header_frame, text=f"{video_info['width']}x{video_info['height']}").grid(row=2, column=1, sticky=tk.W, padx=(5, 0))
        
        # Scale info
        scale_text = self.scale_option.get()
        if scale_text == "Custom":
            scale_text = f"Custom ({self.custom_scale.get()})"
        ttk.Label(header_frame, text="🔧 Scale:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=tk.W)
        ttk.Label(header_frame, text=scale_text).grid(row=3, column=1, sticky=tk.W, padx=(5, 0))
        
        # Segments preview
        segments_frame = ttk.LabelFrame(main_frame, text="📋 Segments Preview", padding="10")
        segments_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        segments_frame.columnconfigure(0, weight=1)
        segments_frame.rowconfigure(0, weight=1)
        
        # Create treeview for segments
        columns = ("Segment", "Start", "End", "Duration", "Output Filename")
        segments_tree = ttk.Treeview(segments_frame, columns=columns, show="headings")
        segments_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure columns
        segments_tree.heading("Segment", text="Segment #")
        segments_tree.heading("Start", text="Start Time")
        segments_tree.heading("End", text="End Time")
        segments_tree.heading("Duration", text="Duration")
        segments_tree.heading("Output Filename", text="Output Filename")
        
        segments_tree.column("Segment", width=80)
        segments_tree.column("Start", width=100)
        segments_tree.column("End", width=100)
        segments_tree.column("Duration", width=100)
        segments_tree.column("Output Filename", width=300)
        
        # Scrollbar for segments tree
        segments_scrollbar = ttk.Scrollbar(segments_frame, orient="vertical", command=segments_tree.yview)
        segments_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        segments_tree.configure(yscrollcommand=segments_scrollbar.set)
        
        # Calculate and display segments
        self.populate_segments_preview(segments_tree, video_info)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, pady=(10, 0))
        
        ttk.Button(buttons_frame, text="✅ Looks Good - Start Cutting", 
                  command=lambda: [preview_window.destroy(), self.start_cutting()]).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="❌ Cancel", 
                  command=preview_window.destroy).pack(side=tk.LEFT)
    
    def get_video_info(self):
        """Get video duration and other info using FFprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                self.input_file.get()
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = None
            for stream in data['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                return None
            
            # Get duration
            duration_seconds = None
            if 'duration' in data['format']:
                duration_seconds = float(data['format']['duration'])
            elif 'duration' in video_stream:
                duration_seconds = float(video_stream['duration'])
            
            if duration_seconds:
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                seconds = int(duration_seconds % 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = "Unknown"
            
            return {
                'duration': duration_str,
                'duration_seconds': duration_seconds or 0,
                'width': video_stream.get('width', 'Unknown'),
                'height': video_stream.get('height', 'Unknown'),
                'fps': video_stream.get('r_frame_rate', 'Unknown')
            }
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            return None
    
    def populate_segments_preview(self, tree, video_info):
        """Populate the segments preview tree."""
        # Parse and sort timestamps (same logic as VideoCutter)
        parsed_timestamps = []
        for ts in self.timestamps:
            parsed_timestamps.append(VideoCutter.parse_timestamp(ts))
        
        parsed_timestamps.sort()
        if parsed_timestamps[0] != "00:00:00":
            parsed_timestamps.insert(0, "00:00:00")
        
        # Get output settings
        prefix = self.output_prefix.get()
        output_dir = self.output_dir.get().strip()
        video_extension = Path(self.input_file.get()).suffix[1:]
        
        # Calculate total duration that will be processed
        total_duration_seconds = 0
        
        for i in range(len(parsed_timestamps)):
            start_time = parsed_timestamps[i]
            
            # Determine end time
            if i + 1 < len(parsed_timestamps):
                end_time = parsed_timestamps[i + 1]
            else:
                if video_info['duration_seconds'] > 0:
                    end_seconds = video_info['duration_seconds']
                    hours = int(end_seconds // 3600)
                    minutes = int((end_seconds % 3600) // 60)
                    seconds = int(end_seconds % 60)
                    end_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    end_time = "End of video"
            
            # Calculate duration
            if end_time != "End of video":
                start_seconds = self.timestamp_to_seconds(start_time)
                end_seconds = self.timestamp_to_seconds(end_time)
                duration_seconds = end_seconds - start_seconds
                total_duration_seconds += duration_seconds
                
                duration_hours = int(duration_seconds // 3600)
                duration_minutes = int((duration_seconds % 3600) // 60)
                duration_secs = int(duration_seconds % 60)
                duration_str = f"{duration_hours:02d}:{duration_minutes:02d}:{duration_secs:02d}"
            else:
                duration_str = "Until end"
            
            # Generate filename
            base_filename = f"{prefix}_segment_{i+1}.{video_extension}"
            if output_dir:
                full_filename = os.path.join(output_dir, base_filename)
            else:
                full_filename = base_filename
            
            # Add to tree
            tree.insert("", "end", values=(
                f"#{i+1}",
                start_time,
                end_time,
                duration_str,
                full_filename
            ))
        
        # Add summary info
        if total_duration_seconds > 0:
            summary_hours = int(total_duration_seconds // 3600)
            summary_minutes = int((total_duration_seconds % 3600) // 60)
            summary_secs = int(total_duration_seconds % 60)
            summary_duration = f"{summary_hours:02d}:{summary_minutes:02d}:{summary_secs:02d}"
            
            tree.insert("", "end", values=("", "", "", "", ""))  # Empty row
            tree.insert("", "end", values=(
                "TOTAL",
                f"{len(parsed_timestamps)} segments",
                "",
                summary_duration,
                f"Estimated processing time: {'Long' if self.scale_option.get() != 'No scaling' else 'Fast'}"
            ), tags=("summary",))
            
            # Style the summary row
            tree.tag_configure("summary", background="lightblue", font=("Arial", 9, "bold"))
    
    def timestamp_to_seconds(self, timestamp):
        """Convert timestamp string to seconds."""
        parts = timestamp.split(':')
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    def check_ffmpeg(self):
        """Check if FFmpeg is available."""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showerror(
                "FFmpeg Not Found", 
                "FFmpeg is not installed or not found in PATH.\n\n"
                "Please install FFmpeg from https://ffmpeg.org/ and add it to your system PATH."
            )
    
    def browse_file(self):
        """Open file dialog to select input video."""
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.input_file.set(filename)
    
    def browse_output_dir(self):
        """Open directory dialog to select output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory"
        )
        if directory:
            self.output_dir.set(directory)
    
    def on_scale_change(self, event=None):
        """Handle scale option change."""
        if self.scale_option.get() == "Custom":
            self.custom_entry.config(state="normal")
        else:
            self.custom_entry.config(state="disabled")
    
    def add_timestamp(self):
        """Add timestamp to the list."""
        timestamp = self.timestamp_entry.get().strip()
        if not timestamp:
            return
        
        try:
            # Validate timestamp format using VideoCutter's static method
            parsed = VideoCutter.parse_timestamp(timestamp)
            
            if timestamp not in self.timestamps:
                self.timestamps.append(timestamp)
                self.timestamps_listbox.insert(tk.END, timestamp)
                self.timestamp_entry.set("")
            else:
                messagebox.showwarning("Duplicate", "Timestamp already exists!")
                
        except ValueError as e:
            messagebox.showerror("Invalid Timestamp", str(e))
    
    def remove_timestamp(self):
        """Remove selected timestamp from the list."""
        selection = self.timestamps_listbox.curselection()
        if selection:
            index = selection[0]
            self.timestamps_listbox.delete(index)
            del self.timestamps[index]
    
    def log_message(self, message):
        """Add message to output log."""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_cutting(self):
        """Start the video cutting process in a separate thread."""
        # Validate inputs
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input video file.")
            return
        
        if not self.timestamps:
            messagebox.showerror("Error", "Please add at least one timestamp.")
            return
        
        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("Error", "Input video file not found.")
            return
        
        # Disable controls
        self.cut_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress.start()
        
        # Clear output
        self.output_text.delete(1.0, tk.END)
        
        # Start cutting in separate thread
        self.cutting_thread = threading.Thread(target=self.cut_video_thread)
        self.cutting_thread.daemon = True
        self.cutting_thread.start()
    
    def cut_video_thread(self):
        """Video cutting process running in separate thread."""
        try:
            # Prepare scale argument
            scale_arg = None
            if self.scale_option.get() != "No scaling":
                if self.scale_option.get() == "Custom":
                    scale_arg = self.custom_scale.get()
                else:
                    scale_arg = self.scale_option.get()
            
            # Prepare output directory
            output_dir = self.output_dir.get().strip() if self.output_dir.get().strip() else None
            
            # Create VideoCutter instance
            cutter = VideoCutter(self.input_file.get())
            
            # Add progress message
            self.progress_queue.put(("message", f"Starting to cut video: {os.path.basename(self.input_file.get())}"))
            self.progress_queue.put(("message", f"Timestamps: {', '.join(self.timestamps)}"))
            if scale_arg:
                self.progress_queue.put(("message", f"Scale: {scale_arg}"))
                self.progress_queue.put(("message", f"⚠️ Scaling enabled - this will take longer as video needs to be re-encoded"))
            else:
                self.progress_queue.put(("message", f"🚀 Fast mode - copying streams without re-encoding"))
            if output_dir:
                self.progress_queue.put(("message", f"Output directory: {output_dir}"))
            else:
                self.progress_queue.put(("message", f"Output directory: Current directory"))
            self.progress_queue.put(("message", "-" * 50))
            
            # Cut video with progress callback
            output_files = self.cut_video_with_progress(
                cutter,
                self.timestamps, 
                self.output_prefix.get(), 
                scale_arg,
                output_dir
            )
            
            # Success message with file info
            self.progress_queue.put(("message", "-" * 50))
            self.progress_queue.put(("message", f"✓ Successfully created {len(output_files)} video segments:"))
            
            total_size = 0
            for i, filename in enumerate(output_files, 1):
                try:
                    file_size = os.path.getsize(filename)
                    size_mb = file_size / (1024 * 1024)
                    total_size += file_size
                    self.progress_queue.put(("message", f"  {i}. {os.path.basename(filename)} ({size_mb:.1f} MB)"))
                except OSError:
                    self.progress_queue.put(("message", f"  {i}. {os.path.basename(filename)} (size unknown)"))
            
            total_mb = total_size / (1024 * 1024)
            self.progress_queue.put(("message", f"📊 Total output size: {total_mb:.1f} MB"))
            self.progress_queue.put(("file_results", output_files))  # Send file list for preview
            self.progress_queue.put(("complete", "success"))
                
        except Exception as e:
            self.progress_queue.put(("message", f"Error: {str(e)}"))
            self.progress_queue.put(("complete", "error"))
    
    def cut_video_with_progress(self, cutter, timestamps, output_prefix, scale_arg, output_dir):
        """Cut video with progress feedback."""
        # Parse and sort timestamps (same as VideoCutter.cut_video)
        parsed_timestamps = []
        for ts in timestamps:
            parsed_timestamps.append(VideoCutter.parse_timestamp(ts))
        
        parsed_timestamps.sort()
        if parsed_timestamps[0] != "00:00:00":
            parsed_timestamps.insert(0, "00:00:00")
        
        output_files = []
        input_path = Path(cutter.input_video)
        
        # Set up output directory
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            test_dir = output_dir
        else:
            test_dir = "."
        
        # Check write permissions
        try:
            test_file = os.path.join(test_dir, "temp_permission_test.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except PermissionError:
            raise PermissionError(f"No write permission in directory '{test_dir}'. Try running as administrator or choosing a different directory.")
        
        # Parse scale settings
        scale_args = []
        if scale_arg:
            scale_args = cutter._parse_scale_settings(scale_arg)
        
        total_segments = len(parsed_timestamps)
        
        # Create segments with progress feedback
        for i in range(total_segments):
            start_time = parsed_timestamps[i]
            
            # Update progress
            self.progress_queue.put(("message", f"Processing segment {i+1} of {total_segments}..."))
            
            # Determine end time and create filename
            if i + 1 < len(parsed_timestamps):
                end_time = parsed_timestamps[i + 1]
                base_filename = f"{output_prefix}_segment_{i+1}.{input_path.suffix[1:]}"
                if output_dir:
                    base_filename = os.path.join(output_dir, base_filename)
                output_filename = cutter._create_safe_filename(base_filename)
                
                if scale_args:
                    self.progress_queue.put(("message", f"🔄 Scaling segment {i+1} ({start_time} → {end_time}) - Please wait..."))
                    cmd = [
                        'ffmpeg',
                        '-i', cutter.input_video,
                        '-ss', start_time,
                        '-to', end_time,
                        '-avoid_negative_ts', 'make_zero',
                        '-y',
                    ] + scale_args + [output_filename]
                else:
                    self.progress_queue.put(("message", f"🚀 Fast copying segment {i+1} ({start_time} → {end_time})"))
                    cmd = [
                        'ffmpeg',
                        '-i', cutter.input_video,
                        '-ss', start_time,
                        '-to', end_time,
                        '-c', 'copy',
                        '-avoid_negative_ts', 'make_zero',
                        '-y',
                        output_filename
                    ]
            else:
                # Last segment to end of video
                base_filename = f"{output_prefix}_segment_{i+1}.{input_path.suffix[1:]}"
                if output_dir:
                    base_filename = os.path.join(output_dir, base_filename)
                output_filename = cutter._create_safe_filename(base_filename)
                
                if scale_args:
                    self.progress_queue.put(("message", f"🔄 Scaling final segment {i+1} ({start_time} → end) - Please wait..."))
                    cmd = [
                        'ffmpeg',
                        '-i', cutter.input_video,
                        '-ss', start_time,
                        '-avoid_negative_ts', 'make_zero',
                        '-y',
                    ] + scale_args + [output_filename]
                else:
                    self.progress_queue.put(("message", f"🚀 Fast copying final segment {i+1} ({start_time} → end)"))
                    cmd = [
                        'ffmpeg',
                        '-i', cutter.input_video,
                        '-ss', start_time,
                        '-c', 'copy',
                        '-avoid_negative_ts', 'make_zero',
                        '-y',
                        output_filename
                    ]
            
            # Execute FFmpeg command
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                output_files.append(output_filename)
                self.progress_queue.put(("message", f"✅ Successfully created: {os.path.basename(output_filename)}"))
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() if e.stderr else str(e)
                self.progress_queue.put(("message", f"❌ Error creating segment {i+1}: {error_msg}"))
                
                if "Permission denied" in error_msg:
                    self.progress_queue.put(("message", "   → Try running as administrator or choose a different output directory"))
                elif "No such file or directory" in error_msg:
                    self.progress_queue.put(("message", "   → Check that the input file path is correct"))
                elif "Invalid argument" in error_msg:
                    self.progress_queue.put(("message", "   → Check that the input file is a valid video format"))
                
                continue
            except Exception as e:
                self.progress_queue.put(("message", f"❌ Unexpected error with segment {i+1}: {str(e)}"))
                continue
        
        return output_files
    
    def open_output_folder(self):
        """Open the output folder in file explorer."""
        output_dir = self.output_dir.get().strip()
        if not output_dir:
            output_dir = os.getcwd()
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(output_dir)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', output_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
    
    def play_selected_video(self):
        """Play the selected video file."""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a video file to play.")
            return
        
        item = self.results_tree.item(selection[0])
        file_path = item['values'][2]  # Full path is in the third column
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open video file: {e}")
    
    def update_results_preview(self, output_files):
        """Update the results tab with file information."""
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Add new results
        for file_path in output_files:
            try:
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                size_mb = f"{file_size / (1024 * 1024):.1f}"
                
                self.results_tree.insert("", "end", values=(filename, size_mb, file_path))
            except OSError:
                # File might not exist or be accessible
                filename = os.path.basename(file_path)
                self.results_tree.insert("", "end", values=(filename, "Unknown", file_path))
        
        # Switch to results tab
        self.output_notebook.select(1)
    
    def stop_cutting(self):
        """Stop the cutting process."""
        # Note: This is a simple implementation. In a more advanced version,
        # you could implement actual process termination
        self.progress_queue.put(("message", "Stopping..."))
        self.progress.stop()
        self.cut_button.config(state="normal")
        self.stop_button.config(state="disabled")
    
    def check_progress_queue(self):
        """Check for messages from the cutting thread."""
        try:
            while True:
                message_type, content = self.progress_queue.get_nowait()
                
                if message_type == "message":
                    self.log_message(content)
                elif message_type == "file_results":
                    self.update_results_preview(content)
                elif message_type == "complete":
                    self.progress.stop()
                    self.cut_button.config(state="normal")
                    self.stop_button.config(state="disabled")
                    
                    if content == "success":
                        messagebox.showinfo("Success", "Video cutting completed successfully!")
                    else:
                        messagebox.showerror("Error", "Video cutting failed. Check the output log for details.")
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_progress_queue)


def main():
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Video Cutter GUI")
    parser.add_argument('input_file', nargs='?', help='Input video file (for context menu integration)')
    parser.add_argument('--setup-context-menu', action='store_true', help='Show context menu setup dialog')
    args = parser.parse_args()
    
    # Check if FFmpeg is available at startup
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Show error but continue - the GUI will show the error too
        pass
    
    # Handle context menu setup
    if args.setup_context_menu:
        try:
            from context_menu import show_context_menu_dialog
            show_context_menu_dialog()
        except ImportError:
            messagebox.showerror("Error", "Context menu module not found. Make sure context_menu.py is in the same directory.")
        return
    
    # Create and run GUI
    root = tk.Tk()
    
    # Try to set a nice theme if available
    try:
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'vista' in available_themes:
            style.theme_use('vista')
    except:
        pass  # Use default theme
    
    app = VideoCutterGUI(root)
    
    # If launched with a file (from context menu), set it as input
    if args.input_file and os.path.exists(args.input_file):
        app.input_file.set(args.input_file)
    
    # Schedule first run check to happen after GUI is shown
    root.after(100, lambda: check_first_run(root))
    
    root.mainloop()

def check_first_run(root):
    """Check if this is the first run and offer context menu setup."""
    try:
        settings_file = Path.home() / '.video_cutter_settings'
        if not settings_file.exists():
            # First run
            if os.name == 'nt':  # Windows only
                response = messagebox.askyesno(
                    "First Run Setup",
                    "Welcome to Video Cutter!\n\n"
                    "Would you like to add Video Cutter to the right-click context menu for video files?\n\n"
                    "This will allow you to right-click any video file and select 'Cut with Video Cutter' "
                    "to open it directly in this application.\n\n"
                    "You can change this later by running the application with --setup-context-menu",
                    parent=root
                )
                
                if response:
                    try:
                        from context_menu import show_context_menu_dialog
                        show_context_menu_dialog()
                    except ImportError:
                        messagebox.showerror("Error", "Context menu module not found.", parent=root)
            
            # Create settings file to mark first run as complete
            settings_file.write_text("first_run_complete=true")
    except Exception:
        # Ignore errors in first run check
        pass


if __name__ == "__main__":
    main() 