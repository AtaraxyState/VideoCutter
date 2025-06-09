#!/usr/bin/env python3
"""
Build script for creating a portable Video Cutter executable
Requires PyInstaller: pip install pyinstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """Build the Video Cutter executable."""
    print("Building Video Cutter executable...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed successfully!")
    
    # Clean previous builds
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            print(f"Cleaning {folder} folder...")
            shutil.rmtree(folder)
    
    # Build command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window (for GUI)
        "--icon=icon.ico",             # Icon file (if exists)
        "--name=VideoCutter",          # Output name
        "--add-data=video_cutter.py;.", # Include the core module
        "--hidden-import=tkinter",      # Ensure tkinter is included
        "--hidden-import=tkinter.ttk",  # Ensure ttk is included
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.scrolledtext",
        "video_cutter_gui.py"          # Main GUI script
    ]
    
    # Remove icon parameter if icon file doesn't exist
    if not os.path.exists("icon.ico"):
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
        print("No icon.ico found, building without custom icon")
    
    print("Running PyInstaller...")
    print(" ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        print("Build completed successfully!")
        
        # Check if executable exists
        exe_path = Path("dist/VideoCutter.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable created: {exe_path}")
            print(f"Size: {size_mb:.1f} MB")
            print(f"This executable can be run from anywhere (USB, different computers, etc.)")
            
            # Create portable package
            create_portable_package()
        else:
            print("Executable not found in expected location")
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False
    
    return True

def create_portable_package():
    """Create a portable package with the executable and instructions."""
    print("\nCreating portable package...")
    
    package_dir = Path("VideoCutter_Portable")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    
    # Copy executable
    shutil.copy("dist/VideoCutter.exe", package_dir)
    
    # Create instructions file
    instructions = """# Video Cutter - Portable Version

## Quick Start
1. Double-click VideoCutter.exe to run the application
2. No installation required - runs from anywhere!

## Features
- Cut videos at specific timestamps
- Scale down resolution and bitrate
- Easy-to-use graphical interface
- Preview results with file sizes
- Portable - runs from USB drives

## First Run Setup
- The application will offer to add itself to the right-click menu for video files
- This is optional but convenient for quick access

## Usage
1. Browse and select your input video
2. Add timestamps where you want to cut (format: HH:MM:SS, MM:SS, or SS)
3. Choose scaling options if desired
4. Select output directory
5. Click "Cut Video"

## Requirements
- Windows 10 or later
- FFmpeg (the app will guide you to install it if needed)

## Troubleshooting
- If you get permission errors, try running as administrator
- For best results, save output to your Documents folder
- Make sure no other programs have the video file open

Enjoy your video cutting!
"""
    
    with open(package_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(instructions)
    
    # Copy FFmpeg download link file
    ffmpeg_info = """# FFmpeg Installation

Video Cutter requires FFmpeg to process video files.

## Download FFmpeg
Visit: https://ffmpeg.org/download.html

## Windows Installation
1. Download the latest build from https://www.gyan.dev/ffmpeg/builds/
2. Extract to C:\\ffmpeg
3. Add C:\\ffmpeg\\bin to your PATH environment variable
4. Restart command prompt/applications

## Alternative - Chocolatey (Recommended)
If you have Chocolatey package manager:
choco install ffmpeg

## Alternative - Direct Download
The Video Cutter will detect if FFmpeg is missing and guide you through installation.
"""
    
    with open(package_dir / "FFmpeg_Installation.txt", "w", encoding="utf-8") as f:
        f.write(ffmpeg_info)
    
    print(f"Portable package created: {package_dir}")
    print("Contents:")
    for item in package_dir.iterdir():
        print(f"   - {item.name}")

def main():
    """Main build function."""
    print("Video Cutter Portable Builder")
    print("=" * 40)
    
    # Check if required files exist
    required_files = ["video_cutter.py", "video_cutter_gui.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"Missing required files: {', '.join(missing_files)}")
        return False
    
    # Build executable
    success = build_executable()
    
    if success:
        print("\nBuild completed successfully!")
        print("Your portable Video Cutter is ready!")
        print("You can now copy the VideoCutter_Portable folder to any Windows computer or USB drive")
    else:
        print("\nBuild failed. Check the error messages above.")
    
    return success

if __name__ == "__main__":
    main() 