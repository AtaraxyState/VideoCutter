#!/usr/bin/env python3
"""
Video Cutter - A simple program to cut videos at specified timestamps
Uses FFmpeg to process video files efficiently
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple
import argparse


class VideoCutter:
    def __init__(self, input_video: str, validate_file: bool = True):
        """Initialize the VideoCutter with an input video file."""
        self.input_video = input_video
        if validate_file and not os.path.exists(input_video):
            raise FileNotFoundError(f"Input video file not found: {input_video}")
    
    @staticmethod
    def parse_timestamp(timestamp: str) -> str:
        """Parse and validate timestamp format (supports HH:MM:SS or MM:SS or SS)."""
        # Remove whitespace
        timestamp = timestamp.strip()
        
        # Split by colon
        parts = timestamp.split(':')
        
        if len(parts) == 1:
            # Just seconds
            try:
                seconds = int(parts[0])
                return f"00:00:{seconds:02d}"
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {timestamp}")
        elif len(parts) == 2:
            # MM:SS format
            try:
                minutes, seconds = int(parts[0]), int(parts[1])
                return f"00:{minutes:02d}:{seconds:02d}"
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {timestamp}")
        elif len(parts) == 3:
            # HH:MM:SS format
            try:
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {timestamp}")
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp}")
    
    def _parse_scale_settings(self, scale: str) -> List[str]:
        """Parse scale settings and return FFmpeg arguments."""
        scale = scale.lower().strip()
        
        # Predefined scale presets
        presets = {
            '720p': ['-vf', 'scale=1280:720', '-b:v', '2M', '-b:a', '128k'],
            '480p': ['-vf', 'scale=854:480', '-b:v', '1M', '-b:a', '96k'],
            '360p': ['-vf', 'scale=640:360', '-b:v', '500k', '-b:a', '64k'],
            '240p': ['-vf', 'scale=426:240', '-b:v', '250k', '-b:a', '64k']
        }
        
        if scale in presets:
            return presets[scale]
        
        # Custom format: "width:height:bitrate" (e.g., "1280:720:2M")
        if ':' in scale:
            parts = scale.split(':')
            if len(parts) >= 2:
                try:
                    width = int(parts[0])
                    height = int(parts[1])
                    bitrate = parts[2] if len(parts) > 2 else '1M'
                    
                    return ['-vf', f'scale={width}:{height}', '-b:v', bitrate, '-b:a', '128k']
                except ValueError:
                    raise ValueError(f"Invalid custom scale format: {scale}")
        
        raise ValueError(f"Invalid scale setting: {scale}. Use presets (720p, 480p, 360p, 240p) or custom format (width:height:bitrate)")
    
    def _create_safe_filename(self, base_filename: str) -> str:
        """Create a safe filename that doesn't conflict with existing files."""
        if not os.path.exists(base_filename):
            return base_filename
        
        # If file exists, try with numbered suffix
        base_name, ext = os.path.splitext(base_filename)
        counter = 1
        while os.path.exists(f"{base_name}_{counter}{ext}"):
            counter += 1
        return f"{base_name}_{counter}{ext}"
    
    def cut_video(self, timestamps: List[str], output_prefix: str = "output", scale: str = None, output_dir: str = None) -> List[str]:
        """
        Cut video into segments based on timestamps.
        
        Args:
            timestamps: List of timestamp strings where to cut
            output_prefix: Prefix for output filenames
            scale: Scale preset for resolution and bitrate (720p, 480p, 360p, or custom like "1280:720:2M")
            output_dir: Directory to save output files (default: current directory)
            
        Returns:
            List of created output filenames
        """
        if not timestamps:
            raise ValueError("At least one timestamp is required")
        
        # Parse and sort timestamps
        parsed_timestamps = []
        for ts in timestamps:
            parsed_timestamps.append(VideoCutter.parse_timestamp(ts))
        
        # Sort timestamps to ensure correct order
        parsed_timestamps.sort()
        
        # Add start timestamp (00:00:00) if not present
        if parsed_timestamps[0] != "00:00:00":
            parsed_timestamps.insert(0, "00:00:00")
        
        output_files = []
        input_path = Path(self.input_video)
        
        # Set up output directory
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            test_dir = output_dir
        else:
            test_dir = "."
        
        # Check write permissions in output directory
        try:
            test_file = os.path.join(test_dir, "temp_permission_test.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except PermissionError:
            raise PermissionError(f"No write permission in directory '{test_dir}'. Try running as administrator or choosing a different directory.")
        
        # Parse scale settings
        scale_args = []
        if scale:
            scale_args = self._parse_scale_settings(scale)
        
        # Create segments between timestamps
        for i in range(len(parsed_timestamps)):
            start_time = parsed_timestamps[i]
            
            # Determine end time (next timestamp or end of video)
            if i + 1 < len(parsed_timestamps):
                # Cut from start_time to next timestamp
                end_time = parsed_timestamps[i + 1]
                base_filename = f"{output_prefix}_segment_{i+1}.{input_path.suffix[1:]}"
                if output_dir:
                    base_filename = os.path.join(output_dir, base_filename)
                output_filename = self._create_safe_filename(base_filename)
                
                if scale_args:
                    cmd = [
                        'ffmpeg',
                        '-i', self.input_video,
                        '-ss', start_time,
                        '-to', end_time,
                        '-avoid_negative_ts', 'make_zero',
                        '-y',  # Overwrite output files
                    ] + scale_args + [output_filename]
                else:
                    cmd = [
                        'ffmpeg',
                        '-i', self.input_video,
                        '-ss', start_time,
                        '-to', end_time,
                        '-c', 'copy',  # Copy streams without re-encoding for speed
                        '-avoid_negative_ts', 'make_zero',
                        '-y',  # Overwrite output files
                        output_filename
                    ]
            else:
                # Cut from start_time to end of video
                base_filename = f"{output_prefix}_segment_{i+1}.{input_path.suffix[1:]}"
                if output_dir:
                    base_filename = os.path.join(output_dir, base_filename)
                output_filename = self._create_safe_filename(base_filename)
                
                if scale_args:
                    cmd = [
                        'ffmpeg',
                        '-i', self.input_video,
                        '-ss', start_time,
                        '-avoid_negative_ts', 'make_zero',
                        '-y',
                    ] + scale_args + [output_filename]
                else:
                    cmd = [
                        'ffmpeg',
                        '-i', self.input_video,
                        '-ss', start_time,
                        '-c', 'copy',
                        '-avoid_negative_ts', 'make_zero',
                        '-y',
                        output_filename
                    ]
            
            print(f"Creating segment {i+1}: {start_time} -> {end_time if i+1 < len(parsed_timestamps) else 'end'}")
            print(f"Output: {output_filename}")
            
            if scale_args:
                print(f"🔄 Processing with scaling (this may take a while)...")
            else:
                print(f"🚀 Fast copying (no re-encoding)...")
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                output_files.append(output_filename)
                print(f"✓ Successfully created {output_filename}")
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() if e.stderr else str(e)
                print(f"✗ Error creating {output_filename}: {error_msg}")
                
                # Check for common permission issues
                if "Permission denied" in error_msg:
                    print("  → This might be due to:")
                    print("    - File is currently open in another application")
                    print("    - Insufficient write permissions in current directory")
                    print("    - Antivirus software blocking file creation")
                    print("  → Try closing other applications or running as administrator")
                elif "No such file or directory" in error_msg:
                    print("  → Check that the input file path is correct")
                elif "Invalid argument" in error_msg:
                    print("  → Check that the input file is a valid video format")
                
                continue
            except Exception as e:
                print(f"✗ Unexpected error creating {output_filename}: {str(e)}")
                continue
        
        return output_files


def main():
    parser = argparse.ArgumentParser(
        description="Cut video into segments at specified timestamps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python video_cutter.py input.mp4 --timestamps "1:30" "3:45" "5:20"
  python video_cutter.py video.mp4 -t "00:01:30" "00:03:45" --output-prefix "scene"
  python video_cutter.py movie.avi -t "90" "225" "320"  # timestamps in seconds
  python video_cutter.py video.mp4 -t "2:00" "4:00" --scale "720p"  # scale to 720p
  python video_cutter.py input.mp4 -t "1:30" -s "1280:720:1.5M"  # custom resolution
        """
    )
    
    parser.add_argument('input_video', help='Input video file path')
    parser.add_argument(
        '-t', '--timestamps', 
        nargs='+', 
        required=True,
        help='Timestamps where to cut (format: HH:MM:SS, MM:SS, or SS)'
    )
    parser.add_argument(
        '-o', '--output-prefix', 
        default='output',
        help='Prefix for output filenames (default: output)'
    )
    parser.add_argument(
        '-s', '--scale',
        help='Scale down resolution and bitrate. Use presets: 720p, 480p, 360p, 240p or custom format: width:height:bitrate (e.g., 1280:720:2M)'
    )
    parser.add_argument(
        '-d', '--output-dir',
        help='Output directory for video segments (default: current directory)'
    )
    
    args = parser.parse_args()
    
    try:
        # Check if FFmpeg is available
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: FFmpeg is not installed or not found in PATH")
        print("Please install FFmpeg from https://ffmpeg.org/")
        sys.exit(1)
    
    try:
        cutter = VideoCutter(args.input_video)
        output_files = cutter.cut_video(args.timestamps, args.output_prefix, args.scale, args.output_dir)
        
        print(f"\n✓ Successfully created {len(output_files)} video segments:")
        for i, filename in enumerate(output_files, 1):
            print(f"  {i}. {filename}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 