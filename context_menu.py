#!/usr/bin/env python3
"""
Context Menu Integration for Video Cutter
Adds/removes Video Cutter from Windows right-click menu for video files
"""

import os
import sys
import winreg
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


class ContextMenuManager:
    def __init__(self, exe_path=None):
        """Initialize with the path to the VideoCutter executable."""
        if exe_path is None:
            # Try to find the executable in common locations
            possible_paths = [
                Path(__file__).parent / "VideoCutter.exe",
                Path(__file__).parent / "dist" / "VideoCutter.exe",
                Path(sys.executable),  # If running as script
            ]
            
            for path in possible_paths:
                if path.exists() and path.suffix == '.exe':
                    exe_path = str(path)
                    break
            else:
                exe_path = str(Path(__file__).parent / "VideoCutter.exe")
        
        self.exe_path = str(Path(exe_path).resolve())
        self.menu_text = "Cut with Video Cutter"
        self.video_extensions = [
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', 
            '.webm', '.m4v', '.3gp', '.ogv', '.ts', '.mts'
        ]
    
    def is_admin(self):
        """Check if running as administrator."""
        try:
            return os.getuid() == 0
        except AttributeError:
            # Windows
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
    
    def run_as_admin(self):
        """Restart the script with admin privileges."""
        if self.is_admin():
            return True
        
        try:
            import ctypes
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([script] + sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
            return False  # Current process should exit
        except Exception as e:
            print(f"Failed to get admin privileges: {e}")
            return False
    
    def add_to_context_menu(self):
        """Add Video Cutter to the context menu for video files."""
        if not self.is_admin():
            messagebox.showerror(
                "Administrator Required",
                "Adding to context menu requires administrator privileges.\n\n"
                "Please run this script as administrator."
            )
            return False
        
        try:
            # Registry keys for different video file types
            for ext in self.video_extensions:
                self._add_extension_menu(ext)
            
            # Also add to generic video file class
            self._add_generic_video_menu()
            
            messagebox.showinfo(
                "Success",
                f"Video Cutter has been added to the right-click menu for video files!\n\n"
                f"Right-click any video file and select '{self.menu_text}' to open it with Video Cutter."
            )
            return True
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to add to context menu: {e}\n\n"
                "Make sure you're running as administrator."
            )
            return False
    
    def _add_extension_menu(self, extension):
        """Add context menu for a specific file extension."""
        # Try multiple approaches to add context menu
        
        # Approach 1: Direct extension registry
        try:
            self._add_shell_menu(extension)
        except Exception:
            pass
        
        # Approach 2: Get the file type association
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, extension, 0, winreg.KEY_READ) as key:
                file_type = winreg.QueryValue(key, "")
                if file_type:
                    self._add_shell_menu(file_type)
        except FileNotFoundError:
            # Extension not registered, create basic entry
            try:
                file_type = f"{extension[1:]}file"
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, extension) as key:
                    winreg.SetValue(key, "", winreg.REG_SZ, file_type)
                self._add_shell_menu(file_type)
            except Exception:
                pass
        
        # Approach 3: Try common video file associations
        if extension == '.mp4':
            common_types = ['WMP11.AssocFile.MP4', 'VLC.mp4', 'Applications\\wmplayer.exe']
            for file_type in common_types:
                try:
                    self._add_shell_menu(file_type)
                except Exception:
                    continue
        elif extension == '.avi':
            common_types = ['WMP11.AssocFile.AVI', 'VLC.avi', 'avifile']
            for file_type in common_types:
                try:
                    self._add_shell_menu(file_type)
                except Exception:
                    continue
    
    def _add_generic_video_menu(self):
        """Add context menu for generic video file types."""
        generic_types = ["VideoClip", "WMP11.AssocFile.MP4", "WMP11.AssocFile.AVI"]
        for file_type in generic_types:
            try:
                self._add_shell_menu(file_type)
            except Exception:
                # Ignore if the type doesn't exist
                pass
    
    def _add_shell_menu(self, file_type):
        """Add shell menu for a specific file type."""
        shell_key_path = f"{file_type}\\shell\\VideoCutter"
        command_key_path = f"{shell_key_path}\\command"
        
        try:
            # Create the shell menu entry
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, shell_key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, self.menu_text)
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, self.exe_path)
            
            # Create the command
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_key_path) as key:
                command = f'"{self.exe_path}" "%1"'
                winreg.SetValue(key, "", winreg.REG_SZ, command)
                
            print(f"✅ Added context menu to: {file_type}")
        except Exception as e:
            print(f"❌ Failed to add context menu to {file_type}: {e}")
            raise
    
    def remove_from_context_menu(self):
        """Remove Video Cutter from the context menu."""
        if not self.is_admin():
            messagebox.showerror(
                "Administrator Required",
                "Removing from context menu requires administrator privileges.\n\n"
                "Please run this script as administrator."
            )
            return False
        
        try:
            removed_count = 0
            
            # Remove from each video extension
            for ext in self.video_extensions:
                removed_count += self._remove_extension_menu(ext)
            
            # Remove from generic video types
            generic_types = ["VideoClip", "WMP11.AssocFile.MP4", "WMP11.AssocFile.AVI"]
            for file_type in generic_types:
                try:
                    removed_count += self._remove_shell_menu(file_type)
                except Exception:
                    pass
            
            if removed_count > 0:
                messagebox.showinfo(
                    "Success",
                    f"Video Cutter has been removed from the right-click menu.\n\n"
                    f"Removed from {removed_count} file type(s)."
                )
            else:
                messagebox.showinfo(
                    "Info",
                    "Video Cutter was not found in the context menu."
                )
            return True
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to remove from context menu: {e}\n\n"
                "Make sure you're running as administrator."
            )
            return False
    
    def _remove_extension_menu(self, extension):
        """Remove context menu for a specific file extension."""
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, extension, 0, winreg.KEY_READ) as key:
                file_type = winreg.QueryValue(key, "")
            
            if file_type:
                return self._remove_shell_menu(file_type)
            else:
                return self._remove_shell_menu(extension)
        except FileNotFoundError:
            return 0
    
    def _remove_shell_menu(self, file_type):
        """Remove shell menu for a specific file type."""
        try:
            shell_key_path = f"{file_type}\\shell"
            winreg.DeleteKeyEx(winreg.HKEY_CLASSES_ROOT, f"{shell_key_path}\\VideoCutter\\command")
            winreg.DeleteKeyEx(winreg.HKEY_CLASSES_ROOT, f"{shell_key_path}\\VideoCutter")
            return 1
        except FileNotFoundError:
            return 0
    
    def is_in_context_menu(self):
        """Check if Video Cutter is already in the context menu."""
        # Check multiple possible locations where the context menu might be installed
        test_locations = [
            ".mp4\\shell\\VideoCutter",
            "WMP11.AssocFile.MP4\\shell\\VideoCutter", 
            "VLC.mp4\\shell\\VideoCutter",
            "mp4file\\shell\\VideoCutter",
            "Applications\\wmplayer.exe\\shell\\VideoCutter"
        ]
        
        for location in test_locations:
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, location, 0, winreg.KEY_READ):
                    return True
            except FileNotFoundError:
                continue
        
        # Also check if .mp4 has a file type association and test that
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ".mp4", 0, winreg.KEY_READ) as key:
                file_type = winreg.QueryValue(key, "")
                if file_type:
                    test_key_path = f"{file_type}\\shell\\VideoCutter"
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, test_key_path, 0, winreg.KEY_READ):
                        return True
        except FileNotFoundError:
            pass
            
        return False


def show_context_menu_dialog():
    """Show a dialog for managing context menu integration."""
    if os.name != 'nt':
        messagebox.showerror("Unsupported OS", "Context menu integration is only supported on Windows.")
        return
    
    root = tk.Tk()
    root.title("Video Cutter - Context Menu Setup")
    root.geometry("500x350")
    root.resizable(False, False)
    
    # Try to find the executable
    manager = ContextMenuManager()
    
    # Check if executable exists
    if not os.path.exists(manager.exe_path):
        tk.Label(
            root, 
            text="⚠️ VideoCutter.exe not found!",
            font=("Arial", 12, "bold"),
            fg="red"
        ).pack(pady=10)
        
        tk.Label(
            root,
            text=f"Expected location: {manager.exe_path}\n\n"
                 "Please build the executable first using build_exe.py",
            wraplength=450,
            justify="center"
        ).pack(pady=10)
        
        tk.Button(root, text="Close", command=root.quit).pack(pady=20)
        root.mainloop()
        return
    
    # Main content
    tk.Label(
        root,
        text="🎬 Video Cutter Context Menu Setup",
        font=("Arial", 16, "bold")
    ).pack(pady=20)
    
    tk.Label(
        root,
        text="Add Video Cutter to the right-click menu for video files.\n"
             "This will allow you to quickly open videos with Video Cutter\n"
             "by right-clicking them in Windows Explorer.",
        wraplength=450,
        justify="center"
    ).pack(pady=10)
    
    # Status
    status_frame = tk.Frame(root)
    status_frame.pack(pady=20)
    
    is_installed = manager.is_in_context_menu()
    status_text = "✅ Installed" if is_installed else "❌ Not Installed"
    status_color = "green" if is_installed else "red"
    
    tk.Label(
        status_frame,
        text=f"Current Status: {status_text}",
        font=("Arial", 12, "bold"),
        fg=status_color
    ).pack()
    
    tk.Label(
        status_frame,
        text=f"Executable: {manager.exe_path}",
        font=("Arial", 9),
        fg="gray"
    ).pack()
    
    # Buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)
    
    def install_context_menu():
        manager.add_to_context_menu()
        root.quit()
    
    def uninstall_context_menu():
        manager.remove_from_context_menu()
        root.quit()
    
    if not is_installed:
        tk.Button(
            button_frame,
            text="🔧 Install Context Menu",
            command=install_context_menu,
            bg="green",
            fg="white",
            font=("Arial", 12),
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
    else:
        tk.Button(
            button_frame,
            text="🗑️ Remove Context Menu",
            command=uninstall_context_menu,
            bg="red",
            fg="white",
            font=("Arial", 12),
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
    
    tk.Button(
        button_frame,
        text="❌ Cancel",
        command=root.quit,
        font=("Arial", 12),
        padx=20,
        pady=10
    ).pack(side=tk.LEFT, padx=10)
    
    # Admin warning
    if not manager.is_admin():
        tk.Label(
            root,
            text="⚠️ Administrator privileges required for context menu changes",
            font=("Arial", 9),
            fg="orange"
        ).pack(pady=10)
    
    root.mainloop()


if __name__ == "__main__":
    show_context_menu_dialog() 