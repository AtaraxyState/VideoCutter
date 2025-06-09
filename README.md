# 🎬 Video Cutter

[![Build Status](https://github.com/AtaraxyState/VideoCutter/workflows/Test%20Build/badge.svg)](https://github.com/AtaraxyState/VideoCutter/actions)
[![Release](https://github.com/AtaraxyState/VideoCutter/workflows/Build%20and%20Release/badge.svg)](https://github.com/AtaraxyState/VideoCutter/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Python application for cutting videos at specified timestamps using FFmpeg. Features both command-line and GUI versions with advanced functionality including preview, scaling options, and Windows context menu integration.

## ✨ Features

- **🖥️ Dual Interface**: Both GUI and command-line versions
- **📋 Preview Mode**: See exactly what segments will be created before processing
- **🔄 Smart Scaling**: Multiple resolution presets (720p, 480p, 360p, 240p) and custom settings
- **⚡ Fast Processing**: Stream copying for quick cuts without re-encoding
- **📁 Context Menu Integration**: Right-click video files in Windows Explorer
- **📊 Real-time Progress**: Live feedback during processing
- **🎯 Flexible Timestamps**: Supports HH:MM:SS, MM:SS, and SS formats
- **📦 Portable Executable**: Build standalone .exe for easy distribution
- **🎨 Modern GUI**: User-friendly interface with tabbed output and file preview

## Prerequisites

1. **Python 3.6+** (should be installed on your system)
2. **FFmpeg** - Download and install from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### Installing FFmpeg on Windows:
1. Download FFmpeg from the official website
2. Extract the files to a folder (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your system PATH (e.g., `C:\ffmpeg\bin`)
4. Restart your command prompt/PowerShell

## Usage

### GUI Version (Recommended for beginners)
```bash
python video_cutter_gui.py
```
The GUI provides an easy-to-use interface with:
- **📁 File Browser**: Easy video file selection
- **📋 Preview Mode**: See segments before cutting
- **⚙️ Visual Controls**: Timestamp management with validation
- **🔄 Scaling Options**: Dropdown with presets and custom settings
- **📊 Real-time Progress**: Live feedback with emoji indicators
- **📈 Results Tab**: File preview with sizes and quick actions
- **🎯 Output Management**: Custom directories and naming

### Command Line Version
```bash
python video_cutter.py input_video.mp4 --timestamps "1:30" "3:45" "5:20"
```

### Command Line Options

- `input_video`: Path to the input video file (required)
- `-t, --timestamps`: List of timestamps where to cut the video (required)
- `-o, --output-prefix`: Prefix for output filenames (default: "output")
- `-s, --scale`: Scale down resolution and bitrate (optional)

### Timestamp Formats

The program supports multiple timestamp formats:
- **Seconds only**: `90` (1 minute 30 seconds)
- **MM:SS format**: `1:30` (1 minute 30 seconds)
- **HH:MM:SS format**: `1:30:45` (1 hour 30 minutes 45 seconds)

### Scaling Options

The program supports scaling down videos to reduce file size:

**Preset Resolutions:**
- `720p` - 1280x720, 2Mbps video, 128kbps audio
- `480p` - 854x480, 1Mbps video, 96kbps audio  
- `360p` - 640x360, 500kbps video, 64kbps audio
- `240p` - 426x240, 250kbps video, 64kbps audio

**Custom Format:** `width:height:bitrate`
- Example: `1280:720:1.5M` (1280x720 resolution, 1.5Mbps bitrate)

### Examples

1. **Cut a video at 1:30, 3:45, and 5:20:**
   ```bash
   python video_cutter.py movie.mp4 -t "1:30" "3:45" "5:20"
   ```
   This creates 4 segments:
   - `output_segment_1.mp4` (0:00 to 1:30)
   - `output_segment_2.mp4` (1:30 to 3:45)
   - `output_segment_3.mp4` (3:45 to 5:20)
   - `output_segment_4.mp4` (5:20 to end)

2. **Use custom output prefix:**
   ```bash
   python video_cutter.py video.mp4 -t "2:00" "4:00" -o "scene"
   ```
   Creates: `scene_segment_1.mp4`, `scene_segment_2.mp4`, `scene_segment_3.mp4`

3. **Using timestamps in seconds:**
   ```bash
   python video_cutter.py input.avi -t "120" "240" "360"
   ```

4. **Scale down to 720p for smaller file sizes:**
   ```bash
   python video_cutter.py large_video.mp4 -t "2:00" "5:00" -s "720p"
   ```

5. **Custom resolution and bitrate:**
   ```bash
   python video_cutter.py video.mp4 -t "1:30" "4:00" -s "1280:720:1.5M"
   ```

## How It Works

1. The program parses the input timestamps and sorts them chronologically
2. It automatically adds a start timestamp (00:00:00) if not provided
3. Uses FFmpeg to cut the video into segments between consecutive timestamps
4. The last segment goes from the final timestamp to the end of the video
5. Uses FFmpeg's `-c copy` option for fast processing without re-encoding

## Features

- ✅ Fast processing (no re-encoding when not scaling)
- ✅ Supports multiple video formats (MP4, AVI, MOV, etc.)
- ✅ Flexible timestamp formats
- ✅ Resolution and bitrate scaling options
- ✅ Automatic filename generation
- ✅ Error handling and validation
- ✅ Progress feedback

## 📦 Download & Installation

### 🚀 **Quick Download (Recommended)**
**[📥 Download Latest Release](https://github.com/AtaraxyState/VideoCutter/releases/latest)**

- Pre-built Windows executable
- No Python installation required
- Extract and run `VideoCutter.exe`

### 🛠️ **Build from Source**

Create a standalone .exe file that doesn't require Python:

```bash
# Install dependencies
pip install -r requirements.txt

# Build executable
python build_exe.py

# Or use the batch file (Windows)
build.bat
```

This creates a `VideoCutter_Portable` folder with:
- `VideoCutter.exe` - The main executable
- All necessary dependencies
- README and documentation

### 🔄 **Automated Releases**
New releases are automatically built and published when version tags are created:
- Each release includes a portable Windows executable
- Releases are triggered by pushing tags like `v1.0.0`, `v1.1.0`, etc.
- GitHub Actions handles building, packaging, and publishing

## 🖱️ Windows Context Menu Integration

Add "Cut with Video Cutter" to your right-click menu:

```bash
python context_menu.py
```

**Note**: Requires administrator privileges to modify Windows registry.

After installation, you can right-click any video file and select "Cut with Video Cutter" to open it directly in the GUI.

## 📋 Preview Mode

The GUI includes a comprehensive preview feature:
- **Video Information**: Duration, resolution, file details
- **Segments Table**: Start/end times, durations, output filenames
- **Processing Estimates**: Fast copying vs. scaling time estimates
- **Validation**: Catch errors before processing starts

## 📁 File Structure

```
VideoCutter/
├── video_cutter.py          # Command-line interface
├── video_cutter_gui.py      # GUI interface
├── context_menu.py          # Windows context menu integration
├── build_exe.py             # Executable builder
├── build.bat                # Windows build script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration

- **Output Directory**: Customizable in GUI or via command line
- **Naming Convention**: Configurable prefix for output files
- **Scaling Presets**: 720p, 480p, 360p, 240p, or custom
- **Processing Mode**: Fast copy or quality scaling

## Troubleshooting

**Error: "FFmpeg is not installed or not found in PATH"**
- Make sure FFmpeg is properly installed and added to your system PATH

**Error: "Input video file not found"**
- Check that the video file path is correct and the file exists

**Error: "Invalid timestamp format"**
- Use supported formats: HH:MM:SS, MM:SS, or SS (seconds only)

**Context menu not appearing:**
- Try restarting Windows Explorer (Ctrl+Shift+Esc → Restart "Windows Explorer")
- Ensure you ran `context_menu.py` as administrator

**Permission errors:**
- Run as administrator or choose a different output directory
- Ensure you have write permissions to the output folder

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the Video Cutter!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 