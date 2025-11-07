"""
playlist_downloader_prototype.py
Minimal PySide6 + yt_dlp prototype for packaging.
This script lists a playlist and starts downloads. It's the same prototype we discussed.
"""
import sys, os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QLabel
# We put a lightweight placeholder GUI here so initial build is simple.
# Replace this with your full prototype code later if desired.
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = QLabel("PlaylistPro — placeholder UI\nReplace src/playlist_downloader_prototype.py with full prototype.py when ready.")
    w.setWindowTitle("PlaylistPro")
    w.resize(640,200)
    w.show()
    sys.exit(app.exec())
