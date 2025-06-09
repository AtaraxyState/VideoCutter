@echo off
echo 🎬 Video Cutter Portable Builder
echo ================================
echo.

REM Change to the directory where this batch file is located
cd /d "%~dp0"
echo 📁 Working directory: %CD%
echo.

REM Check if required files exist
if not exist "build_exe.py" (
    echo ❌ build_exe.py not found in current directory!
    echo Make sure you're running this from the Video Cutter project folder.
    pause
    exit /b 1
)

if not exist "video_cutter_gui.py" (
    echo ❌ video_cutter_gui.py not found in current directory!
    echo Make sure you're running this from the Video Cutter project folder.
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)

echo ✅ Python found
echo ✅ Required files found
echo.

REM Run the build script
echo 🚀 Starting build process...
python build_exe.py

if errorlevel 1 (
    echo.
    echo ❌ Build failed! Check the errors above.
    pause
    exit /b 1
)

echo.
echo 🎉 Build completed successfully!
echo.
echo 📦 Your portable Video Cutter is ready in the VideoCutter_Portable folder
echo 💡 You can copy this folder to any Windows computer or USB drive
echo.

REM Ask if user wants to set up context menu
set /p SETUP_CONTEXT=Do you want to set up the right-click context menu? (y/n): 
if /i "%SETUP_CONTEXT%"=="y" (
    echo.
    echo 🔧 Setting up context menu...
    python context_menu.py
)

echo.
echo ✨ All done! Press any key to exit...
pause >nul 