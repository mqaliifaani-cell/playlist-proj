# PlaylistPro — Modern Playlist Downloader (Prototype)

[![Build Windows][badge-actions]][actions] [![License: MIT][badge-license]][license-link]

> Portable, professional Windows playlist downloader (PySide6 + yt-dlp).  
> Designed to reliably download large YouTube playlists with per-video control and modern UX.

---

## 🚀 Key Features
- Import playlist or channel URLs (fast listing).
- Per-video selection with checkboxes and per-video progress bars.
- Concurrent downloads with configurable worker limit.
- Quality and audio selection (global presets).
- Output folder + optional per-playlist subfolder.
- `download-archive` support to skip already-downloaded videos.
- Robust retries, resume support, and console log for troubleshooting.
- Portable Windows distribution (PyInstaller `--onedir`) produced by CI.

---

## 🖼 Screenshots
(Replace these with real screenshots in `/docs/screenshots` later.)

- Main UI: playlist listing, per-item checkboxes and progress bars.  
- Console/log panel for detailed output.

---

## ⚙️ Quickstart (developer)
> These commands are for development on Linux (AlmaLinux) and for producing a Windows build via GitHub Actions.

### 1. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install runtime dependencies (for local dev/testing):
```bash
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

### 3. Run the GUI (Linux requires X/Wayland):
```bash
python src/playlist_downloader_prototype.py
```

> **Note:** The packaged Windows build contains a bundled `ffmpeg.exe`.  
> For local testing on Linux, install `ffmpeg` in your system path.

---

## 🧱 Building a portable Windows release (CI)
This repository includes a GitHub Actions workflow at `.github/workflows/build-windows.yml` that:

- Runs on `windows-latest`
- Installs dependencies and PyInstaller
- Downloads a Windows `ffmpeg` binary
- Runs `pyinstaller --onedir --add-binary "ffmpeg.exe;."`  
- Uploads the `dist/PlaylistPro` folder as an artifact

To produce a release artifact:
- Push to `main` (workflow is triggered on push)
- Download the `PlaylistPro-windows` artifact from the Actions run (or via `gh run download`)

Example artifact download:
```bash
gh run download <run-id> --name PlaylistPro-windows --dir artifacts
```

---

## 💻 Packaging locally (Windows)
If you prefer to build on a Windows machine:

1. Prepare environment:
```powershell
python -m venv venv
venv\Scripts\Activate
pip install -U pip setuptools wheel pyinstaller
pip install -r requirements.txt
```

2. Place `ffmpeg.exe` next to entry script or in PATH.  
3. Build:
```powershell
pyinstaller --noconfirm --onedir --add-binary "path\to\ffmpeg.exe;." --name PlaylistPro src\playlist_downloader_prototype.py
```

---

## ⚙️ Configuration & Advanced Options
- `--playlist-start` / `--playlist-end` — download selected video ranges.
- `--download-archive downloaded.txt` — skip previously downloaded videos.
- `--limit-rate` — limit download bandwidth.
- Export/import cookies for private or age-restricted playlists (via `--cookies cookies.txt`).

---

## 🤝 Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines:  
code style, tests, how to run CI locally, and PR workflow.

---

## 📜 License
This project is released under the **MIT License** — see [LICENSE](LICENSE).

---

## 🧭 Roadmap / Next Steps
- Add per-video format picker (`yt-dlp -F` integration).  
- Pause/resume capability.  
- Queue reordering (drag & drop).  
- Improved packaging & installer (Inno Setup or NSIS).  
- User account sign-in for private playlists (secure cookie import).  

---

[badge-actions]: https://img.shields.io/badge/actions-build-brightgreen
[badge-license]: https://img.shields.io/badge/license-MIT-blue
[actions]: https://github.com/mqaliifaani-cell/playlist-proj/actions
[license-link]: LICENSE
