import os
import sys
import time
from player import YouTubePlayer
from utils import install_requirements, check_vlc
from gui import SearchFrame, ControlsFrame

def main():
    # Check and install dependencies
    if not os.path.exists("installed.flag"):
        install_requirements()
        with open("installed.flag", "w") as f:
            f.write("Dependencies installed")
    
    # Check VLC
    check_vlc()
    
    # Run application
    app = YouTubePlayer()
    app.run()

if __name__ == "__main__":
    main()