# utils.py
import subprocess
import sys
import os
import webbrowser

def install_requirements():
    required_packages = [
        'customtkinter',
        'python-vlc',
        'yt-dlp',
        'beautifulsoup4',
        'requests',
        'pillow'
    ]
    print("Checking and installing required packages...")
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except:
            print(f"Failed to install {package}")

def check_vlc():
    vlc_path = r"C:\Program Files\VideoLAN\VLC"
    if not os.path.exists(vlc_path):
        raise RuntimeError("VLC not found. Please install VLC media player")
        
    # Add VLC to system PATH
    if vlc_path not in os.environ['PATH']:
        os.environ['PATH'] = vlc_path + os.pathsep + os.environ['PATH']
    
    # Add DLL directory for Windows
    if os.name == 'nt':
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(vlc_path)
    
    return True

def format_time(milliseconds):
    seconds = milliseconds // 1000
    minutes = seconds // 60
    seconds %= 60
    return f"{minutes}:{seconds:02d}"