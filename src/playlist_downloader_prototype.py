"""
playlist_downloader_prototype.py
A PySide6 + yt_dlp prototype for a portable Windows playlist downloader.

Requirements:
    pip install PySide6 yt-dlp

FFmpeg:
    ffmpeg.exe must be in PATH or placed next to the final EXE for merging.

Run:
    python src/playlist_downloader_prototype.py
"""
import sys
import os
import json
import threading
import time
from pathlib import Path
from queue import Queue
from functools import partial

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QListWidget, QListWidgetItem, QProgressBar,
    QCheckBox, QComboBox, QSpinBox, QTextEdit, QMessageBox, QFrame
)

# yt_dlp import must be installed
try:
    import yt_dlp
except Exception as e:
    raise RuntimeError("yt_dlp module not found. Run: pip install yt-dlp") from e

# ------------------------------
# Helper signals object to safely update UI from worker threads
# ------------------------------
class Signals(QObject):
    update_progress = Signal(str, float, int, int, str)
    update_status = Signal(str, str)
    finished_video = Signal(str, bool, str)

signals = Signals()

# ------------------------------
# Per-item widget in the list
# ------------------------------
class VideoWidget(QWidget):
    def __init__(self, info):
        super().__init__()
        self.info = info
        self.video_id = info.get('id') or info.get('url') or info.get('webpage_url')
        self.title = info.get('title', self.video_id)
        self.duration = info.get('duration')
        self.url = info.get('url') if info.get('url') else info.get('webpage_url')
        self.init_ui()

    def init_ui(self):
        main = QHBoxLayout()
        main.setContentsMargins(6,6,6,6)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        main.addWidget(self.checkbox)

        leftcol = QVBoxLayout()
        title = QLabel(self.title)
        title.setToolTip(self.title)
        leftcol.addWidget(title)

        meta = QLabel(f"Duration: {self._fmt_duration(self.duration)}")
        meta.setStyleSheet("color: #666; font-size: 11px;")
        leftcol.addWidget(meta)
        main.addLayout(leftcol)

        spacer = QHBoxLayout()
        spacer.addStretch()
        main.addLayout(spacer)

        rightcol = QVBoxLayout()
        self.status_label = QLabel("Queued")
        rightcol.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedWidth(300)
        rightcol.addWidget(self.progress)
        main.addLayout(rightcol)

        self.setLayout(main)
        self.setMinimumHeight(64)

    def _fmt_duration(self, d):
        if not d:
            return "–"
        h = d // 3600
        m = (d % 3600) // 60
        s = d % 60
        if h:
            return f"{h:d}:{m:02d}:{s:02d}"
        return f"{m:d}:{s:02d}"

    def set_progress(self, percent, downloaded_bytes, total_bytes, status_text):
        if percent is None:
            self.progress.setValue(0)
        else:
            try:
                p = int(percent)
            except:
                p = 0
            self.progress.setValue(p)
        # status_text should always be a string
        self.status_label.setText(status_text or "")

    def set_status_text(self, text):
        self.status_label.setText(text or "")

# ------------------------------
# Worker that downloads a single video using yt_dlp
# ------------------------------
class DownloadWorker(threading.Thread):
    def __init__(self, video_entry, out_dir, opts, archive_path):
        super().__init__(daemon=True)
        self.entry = video_entry
        self.out_dir = out_dir
        self.opts = opts.copy()
        self.archive_path = archive_path
        self.video_id = self.entry.get('id') or self.entry.get('url') or self.entry.get('webpage_url')
        self._stop = threading.Event()

    def run(self):
        def progress_hook(d):
            status = d.get('status')
            if status == 'downloading':
                downloaded = d.get('downloaded_bytes') or 0
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or -1

                # percent may be in different keys or None
                percent_float = None
                try:
                    if 'percent' in d and d['percent'] is not None:
                        percent_float = float(d['percent'])
                    else:
                        percent_str = d.get('_percent_str')
                        if percent_str:
                            percent_float = float(percent_str.strip().strip('%'))
                except Exception:
                    percent_float = None

                # ensure we never format None
                p_display = percent_float if percent_float is not None else 0.0

                speed = d.get('speed') or 0
                # build status text safely
                status_text = f"Downloading {p_display:.1f}% • {self._fmt_bytes(downloaded)} / "
                status_text += f"{self._fmt_bytes(total) if total != -1 else '?'} • {self._fmt_bytes(speed)}/s"

                # emit a numeric percent (float) guaranteed not None
                signals.update_progress.emit(self.video_id, float(p_display), downloaded, total if total else -1, status_text)

            elif status == 'finished':
                signals.update_progress.emit(self.video_id, 100.0, d.get('downloaded_bytes') or 0, d.get('total_bytes') or -1, "Processing/merging")
            elif status == 'error':
                # pass a safe message
                signals.update_status.emit(self.video_id, "Error")

        ydl_opts = self.opts.copy()
        tpl = ydl_opts.get('outtmpl') or "%(playlist_index)03d - %(title)s.%(ext)s"
        ydl_opts['outtmpl'] = os.path.join(self.out_dir, tpl)
        if self.archive_path:
            ydl_opts['download_archive'] = self.archive_path
        ydl_opts['progress_hooks'] = [progress_hook]
        ydl_opts.setdefault('quiet', True)
        ydl_opts.setdefault('no_warnings', True)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                url = self.entry.get('webpage_url') or self.entry.get('url') or self.entry.get('id')
                signals.update_status.emit(self.video_id, "Starting")
                ydl.download([url])
            signals.finished_video.emit(self.video_id, True, "Done")
        except Exception as e:
            # always convert exception to string so UI can display it safely
            signals.finished_video.emit(self.video_id, False, str(e))

    def _fmt_bytes(self, b):
        try:
            b = float(b)
        except:
            return "?"
        if b < 1024:
            return f"{b:.0f}B"
        if b < 1024**2:
            return f"{b/1024:.1f}KB"
        if b < 1024**3:
            return f"{b/(1024**2):.1f}MB"
        return f"{b/(1024**3):.1f}GB"

# ------------------------------
# Main window
# ------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Playlist Downloader — Prototype")
        self.resize(1000, 700)

        self.playlist = None
        self.video_widgets = {}
        self.queue = Queue()
        self.active_workers = []
        self.max_concurrent = 3
        self.download_opts = {}
        self.download_archive = os.path.join(os.getcwd(), "downloaded.txt")

        layout = QVBoxLayout(self)

        urlrow = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste playlist or channel URL here...")
        self.fetch_btn = QPushButton("Fetch")
        urlrow.addWidget(self.url_input)
        urlrow.addWidget(self.fetch_btn)
        layout.addLayout(urlrow)

        midrow = QHBoxLayout()
        self.output_input = QLineEdit(str(Path.cwd()))
        self.browse_output = QPushButton("Browse...")
        midrow.addWidget(QLabel("Output folder:"))
        midrow.addWidget(self.output_input)
        midrow.addWidget(self.browse_output)
        layout.addLayout(midrow)

        optsrow = QHBoxLayout()
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["best", "bestvideo+bestaudio", "1080", "720", "480", "audio"])
        self.concurrent_spin = QSpinBox(); self.concurrent_spin.setRange(1, 12); self.concurrent_spin.setValue(3)
        self.per_playlist_folder_cb = QCheckBox("Create subfolder per playlist")
        self.archive_cb = QCheckBox("Use download archive (skip downloaded)")
        self.archive_cb.setChecked(True)
        optsrow.addWidget(QLabel("Quality:"))
        optsrow.addWidget(self.quality_combo)
        optsrow.addWidget(QLabel("Concurrency:"))
        optsrow.addWidget(self.concurrent_spin)
        optsrow.addWidget(self.per_playlist_folder_cb)
        optsrow.addWidget(self.archive_cb)
        layout.addLayout(optsrow)

        control_row = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        self.download_selected_btn = QPushButton("Download Selected")
        control_row.addWidget(self.select_all_btn)
        control_row.addWidget(self.deselect_all_btn)
        control_row.addStretch()
        control_row.addWidget(self.download_selected_btn)
        layout.addLayout(control_row)

        middle = QHBoxLayout()

        self.list_widget = QListWidget()
        middle.addWidget(self.list_widget, 3)

        rightside = QVBoxLayout()
        self.status_console = QTextEdit()
        self.status_console.setReadOnly(True)
        rightside.addWidget(QLabel("Console"))
        rightside.addWidget(self.status_console)
        middle.addLayout(rightside, 2)

        layout.addLayout(middle)

        bottom = QHBoxLayout()
        self.global_progress = QProgressBar()
        self.global_progress.setRange(0, 100)
        bottom.addWidget(self.global_progress)
        layout.addLayout(bottom)

        self.fetch_btn.clicked.connect(self.on_fetch)
        self.browse_output.clicked.connect(self.on_browse_output)
        self.select_all_btn.clicked.connect(self.on_select_all)
        self.deselect_all_btn.clicked.connect(self.on_deselect_all)
        self.download_selected_btn.clicked.connect(self.on_download_selected)
        self.concurrent_spin.valueChanged.connect(self.on_concurrency_changed)

        signals.update_progress.connect(self.on_update_progress)
        signals.update_status.connect(self.on_update_status)
        signals.finished_video.connect(self.on_finished_video)

    def on_fetch(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "No URL", "Please paste a playlist or channel URL.")
            return
        self.status_console.append("Fetching playlist metadata...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            ydl_opts = {'quiet': True, 'extract_flat': 'in_playlist', 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Fetch error", f"Could not fetch playlist: {e}")
            return
        QApplication.restoreOverrideCursor()
        self.playlist = info
        entries = info.get('entries', [])
        self.list_widget.clear()
        self.video_widgets.clear()
        for e in entries:
            widget = VideoWidget(e)
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
            vid = widget.video_id
            self.video_widgets[vid] = (item, widget, e)
        self.status_console.append(f"Loaded {len(entries)} items from playlist: {info.get('title')}")

    def on_browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder", str(Path.cwd()))
        if folder:
            self.output_input.setText(folder)

    def on_select_all(self):
        for _, widget_tuple in self.video_widgets.items():
            widget = widget_tuple[1]
            widget.checkbox.setChecked(True)

    def on_deselect_all(self):
        for _, widget_tuple in self.video_widgets.items():
            widget = widget_tuple[1]
            widget.checkbox.setChecked(False)

    def on_concurrency_changed(self, val):
        self.max_concurrent = int(val)

    def on_download_selected(self):
        selected = []
        for vid, (item, widget, entry) in self.video_widgets.items():
            if widget.checkbox.isChecked():
                selected.append((vid, widget, entry))
        if not selected:
            QMessageBox.information(self, "No selection", "No videos selected for download.")
            return

        out_root = Path(self.output_input.text().strip() or os.getcwd())
        out_root.mkdir(parents=True, exist_ok=True)
        if self.per_playlist_folder_cb.isChecked() and self.playlist:
            safe_title = self._safe_filename(self.playlist.get('title', 'playlist'))
            out_dir = out_root / safe_title
        else:
            out_dir = out_root
        out_dir = str(out_dir)
        archive_path = self.download_archive if self.archive_cb.isChecked() else None

        quality_choice = self.quality_combo.currentText()
        ydl_base_opts = {
            'format': self._quality_to_format(quality_choice),
            'merge_output_format': 'mp4',
            'outtmpl': "%(playlist_index)03d - %(title)s.%(ext)s",
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True
        }
        total = len(selected)
        self.status_console.append(f"Queueing {total} selected videos...")
        self.global_total = total
        self.global_done = 0
        self.global_progress.setValue(0)
        semaphore = threading.Semaphore(self.max_concurrent)
        self.active_workers = []

        def worker_launcher(entry_tuple):
            vid, widget, entry = entry_tuple
            semaphore.acquire()
            worker = DownloadWorker(entry, out_dir, ydl_base_opts, archive_path)
            self.active_workers.append(worker)
            worker.start()
            def monitor():
                worker.join()
                semaphore.release()
            t = threading.Thread(target=monitor, daemon=True)
            t.start()

        for entry_tuple in selected:
            t = threading.Thread(target=worker_launcher, args=(entry_tuple,), daemon=True)
            t.start()

    def on_update_progress(self, video_id, percent, downloaded_bytes, total_bytes, status_text):
        try:
            item, widget, entry = self.video_widgets.get(video_id)
        except:
            widget = None
            for _, t in self.video_widgets.items():
                if t[1].video_id == video_id:
                    widget = t[1]
                    break
        if widget:
            widget.set_progress(percent, downloaded_bytes, total_bytes, status_text)

    def on_update_status(self, video_id, status_text):
        if video_id in self.video_widgets:
            _, widget, _ = self.video_widgets[video_id]
            widget.set_status_text(status_text)

    def on_finished_video(self, video_id, success, message):
        self.global_done += 1
        if self.global_total:
            pct = int(100 * (self.global_done / self.global_total))
            self.global_progress.setValue(pct)
        try:
            item, widget, entry = self.video_widgets.get(video_id)
        except:
            widget = None
            for _, t in self.video_widgets.items():
                if t[1].video_id == video_id:
                    widget = t[1]
                    break
        if widget:
            if success:
                widget.set_status_text("Done")
                widget.progress.setValue(100)
            else:
                widget.set_status_text("Failed")
        # ensure message is string
        self.status_console.append(f"[{video_id}] {'OK' if success else 'FAILED'} — {str(message)}")

    def _quality_to_format(self, q):
        if q == "best":
            return "best"
        if q == "bestvideo+bestaudio":
            return "bestvideo+bestaudio/best"
        if q == "audio":
            return "bestaudio"
        if q.isdigit():
            return f"bestvideo[height<={q}]+bestaudio/best[height<={q}]"
        return "best"

    def _safe_filename(self, s):
        keep = (" ", ".", "_", "-")
        return "".join(c for c in s if c.isalnum() or c in keep).rstrip()

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
