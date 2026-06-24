"""
Video Download Dialog - Extracts video info and allows format/quality selection.
Supports both single videos and YouTube playlists.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFileDialog, QMessageBox, QComboBox, QCheckBox,
    QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from pathlib import Path
from core.video_extractor import VideoExtractor


class ExtractThread(QThread):
    """Background thread for video info extraction."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url: str, extractor: VideoExtractor, is_playlist: bool = False):
        super().__init__()
        self.url = url
        self.extractor = extractor
        self.is_playlist = is_playlist

    def run(self):
        try:
            if self.is_playlist:
                info = self.extractor.extract_playlist(self.url)
            else:
                info = self.extractor.extract_info(self.url)
            if "error" in info:
                self.error.emit(info["error"])
            else:
                self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class VideoDownloadDialog(QDialog):
    """Dialog to extract video info and choose format for downloading."""

    download_video = pyqtSignal(str, str, str)  # url, format_id, output_dir
    download_playlist = pyqtSignal(list, str, str)  # videos_list, quality, output_dir

    DIALOG_STYLE = """
        QDialog { background: #12132a; }
        QLabel { color: #e0e0e0; font-size: 12px; }
        QLineEdit {
            background: #1e1f36; border: 1px solid #2a2b4a; border-radius: 8px;
            padding: 10px 14px; color: #e0e0e0; font-size: 13px;
        }
        QLineEdit:focus { border: 1px solid #6C63FF; }
        QPushButton { border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: 600; }
        QTableWidget {
            background: #1e1f36; border: 1px solid #2a2b4a; border-radius: 8px;
            color: #e0e0e0; gridline-color: #2a2b4a; selection-background-color: #6C63FF;
        }
        QTableWidget::item { padding: 4px 8px; }
        QHeaderView::section {
            background: #222340; color: #aaa; border: none;
            padding: 6px; font-size: 11px; font-weight: 600;
        }
        QProgressBar {
            background: #2a2b4a; border-radius: 3px; border: none; text-align: center;
            color: white; font-size: 10px;
        }
        QProgressBar::chunk { background: #6C63FF; border-radius: 3px; }
        QComboBox {
            background: #1e1f36; border: 1px solid #2a2b4a; border-radius: 8px;
            padding: 8px 14px; color: #e0e0e0; font-size: 13px;
        }
        QComboBox:focus { border: 1px solid #6C63FF; }
        QComboBox QAbstractItemView {
            background: #1e1f36; color: #e0e0e0; border: 1px solid #2a2b4a;
            selection-background-color: #6C63FF;
        }
        QCheckBox { color: #e0e0e0; font-size: 12px; spacing: 8px; }
        QCheckBox::indicator {
            width: 18px; height: 18px; border-radius: 4px;
            border: 1px solid #3a3b5a; background: #1e1f36;
        }
        QCheckBox::indicator:checked { background: #6C63FF; border: 1px solid #6C63FF; }
    """

    def __init__(self, extractor: VideoExtractor, default_path: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Download")
        self.setMinimumSize(700, 560)
        self.setStyleSheet(self.DIALOG_STYLE)
        self.extractor = extractor
        self.default_path = default_path or str(Path.home() / "TDdownloader")
        self._video_info = {}
        self._playlist_info = {}
        self._is_playlist = False
        self._extract_thread = None
        self._playlist_checkboxes = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("🎬  Video / Playlist Download")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; font-size: 16px;")
        layout.addWidget(title)

        # URL input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube, TikTok, Facebook... URL or Playlist URL")
        url_layout.addWidget(self.url_input, 1)

        self.extract_btn = QPushButton("🔍 Extract")
        self.extract_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6C63FF, stop:1 #3F3D9E);
                color: white; border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7B73FF, stop:1 #4F4DAE);
            }
        """)
        self.extract_btn.clicked.connect(self._on_extract)
        url_layout.addWidget(self.extract_btn)
        layout.addLayout(url_layout)

        # Progress
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Video info
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #aaa; font-size: 11px; padding: 4px;")
        layout.addWidget(self.info_label)

        # === Single video: format table ===
        self.format_table = QTableWidget()
        self.format_table.setColumnCount(5)
        self.format_table.setHorizontalHeaderLabels(["Format", "Resolution", "Extension", "Size", "Codec"])
        self.format_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.format_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.format_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.format_table.verticalHeader().setVisible(False)
        self.format_table.hide()
        layout.addWidget(self.format_table)

        # === Playlist: quality selector + video list ===
        self.playlist_panel = QWidget()
        playlist_layout = QVBoxLayout(self.playlist_panel)
        playlist_layout.setContentsMargins(0, 0, 0, 0)
        playlist_layout.setSpacing(8)

        # Quality combo
        quality_row = QHBoxLayout()
        quality_label = QLabel("Quality:")
        quality_label.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        quality_row.addWidget(quality_label)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "Best (Video+Audio)", "1080p", "720p", "480p", "360p", "Audio Only (MP3)"
        ])
        self.quality_combo.setCurrentIndex(0)
        quality_row.addWidget(self.quality_combo, 1)
        playlist_layout.addLayout(quality_row)

        # Select all checkbox
        self.select_all_check = QCheckBox("Select All")
        self.select_all_check.setChecked(True)
        self.select_all_check.toggled.connect(self._toggle_select_all)
        playlist_layout.addWidget(self.select_all_check)

        # Playlist table with checkboxes
        self.playlist_table = QTableWidget()
        self.playlist_table.setColumnCount(3)
        self.playlist_table.setHorizontalHeaderLabels(["#", "Title", "Duration"])
        self.playlist_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.playlist_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.playlist_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.playlist_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.playlist_table.verticalHeader().setVisible(False)
        playlist_layout.addWidget(self.playlist_table)

        self.playlist_panel.hide()
        layout.addWidget(self.playlist_panel)

        # Save path
        path_layout = QHBoxLayout()
        path_label = QLabel("Save to:")
        path_layout.addWidget(path_label)
        self.path_input = QLineEdit(self.default_path)
        path_layout.addWidget(self.path_input, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("""
            QPushButton { background: #2a2b4a; color: #e0e0e0; border: 1px solid #3a3b5a; }
            QPushButton:hover { background: #3a3b5a; }
        """)
        browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton { background: #2a2b4a; color: #e0e0e0; border: 1px solid #3a3b5a; }
            QPushButton:hover { background: #3a3b5a; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.download_btn = QPushButton("⬇  Download")
        self.download_btn.setEnabled(False)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6C63FF, stop:1 #3F3D9E);
                color: white; border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7B73FF, stop:1 #4F4DAE);
            }
            QPushButton:disabled { background: #2a2b4a; color: #555; }
        """)
        self.download_btn.clicked.connect(self._on_download)
        btn_layout.addWidget(self.download_btn)

        layout.addLayout(btn_layout)

    def _on_extract(self):
        url = self.url_input.text().strip()
        if not url:
            return

        self.extract_btn.setEnabled(False)
        self.progress.show()
        self.format_table.hide()
        self.playlist_panel.hide()
        self.download_btn.setEnabled(False)

        # Detect playlist vs single video
        self._is_playlist = VideoExtractor.is_playlist_url(url)
        self.info_label.setText(
            "Extracting playlist info..." if self._is_playlist else "Extracting video info..."
        )

        self._extract_thread = ExtractThread(url, self.extractor, self._is_playlist)
        self._extract_thread.finished.connect(self._on_info_ready)
        self._extract_thread.error.connect(self._on_extract_error)
        self._extract_thread.start()

    def _on_extract_error(self, error: str):
        self.progress.hide()
        self.extract_btn.setEnabled(True)
        self.info_label.setText(f"<span style='color: #F44336;'>Error: {error}</span>")

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder", self.default_path)
        if path:
            self.path_input.setText(path)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes <= 0:
            return "?"
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _on_info_ready(self, info: dict):
        self.progress.hide()
        self.extract_btn.setEnabled(True)

        if self._is_playlist:
            self._show_playlist_info(info)
        else:
            self._show_video_info(info)

    def _show_video_info(self, info: dict):
        """Show single video formats."""
        self._video_info = info

        # Show info
        duration = info.get("duration", 0)
        dur_str = f"{duration // 60}:{duration % 60:02d}" if duration else "Unknown"
        self.info_label.setText(
            f"<b>{info.get('title', 'Unknown')}</b><br>"
            f"👤 {info.get('uploader', 'Unknown')} • ⏱ {dur_str}"
        )

        # Populate format table
        formats = info.get("formats", [])
        self.format_table.setRowCount(len(formats))
        for i, f in enumerate(formats):
            self.format_table.setItem(i, 0, QTableWidgetItem(f.get("format_id", "")))
            self.format_table.setItem(i, 1, QTableWidgetItem(f.get("resolution", "")))
            self.format_table.setItem(i, 2, QTableWidgetItem(f.get("ext", "")))
            size = f.get("filesize", 0)
            size_str = self._format_size(size) if size else "~"
            self.format_table.setItem(i, 3, QTableWidgetItem(size_str))
            codec = []
            if f.get("vcodec", "none") != "none":
                codec.append(f["vcodec"][:10])
            if f.get("acodec", "none") != "none":
                codec.append(f["acodec"][:10])
            self.format_table.setItem(i, 4, QTableWidgetItem(" + ".join(codec) or "unknown"))

        self.format_table.show()
        self.playlist_panel.hide()
        self.format_table.selectRow(0)
        self.download_btn.setEnabled(True)

    def _show_playlist_info(self, info: dict):
        """Show playlist entries with checkboxes."""
        self._playlist_info = info
        entries = info.get("entries", [])

        self.info_label.setText(
            f"<b>📋 {info.get('title', 'Playlist')}</b><br>"
            f"👤 {info.get('uploader', 'Unknown')} • {len(entries)} videos"
        )

        # Populate playlist table
        self._playlist_checkboxes.clear()
        self.playlist_table.setRowCount(len(entries))

        for i, entry in enumerate(entries):
            # Number
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            num_item.setCheckState(Qt.CheckState.Checked)
            self.playlist_table.setItem(i, 0, num_item)
            self._playlist_checkboxes.append(num_item)

            # Title
            self.playlist_table.setItem(i, 1, QTableWidgetItem(entry.get("title", "Unknown")))

            # Duration
            dur = entry.get("duration", 0)
            if dur:
                dur_str = f"{dur // 60}:{dur % 60:02d}"
            else:
                dur_str = "—"
            self.playlist_table.setItem(i, 2, QTableWidgetItem(dur_str))

        self.format_table.hide()
        self.select_all_check.setChecked(True)
        self.playlist_panel.show()
        self.download_btn.setEnabled(True)
        self.download_btn.setText(f"⬇  Download {len(entries)} Videos")

    def _toggle_select_all(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for item in self._playlist_checkboxes:
            item.setCheckState(state)
        # Update button text
        if self._is_playlist:
            count = sum(1 for item in self._playlist_checkboxes if item.checkState() == Qt.CheckState.Checked)
            self.download_btn.setText(f"⬇  Download {count} Videos")

    def _on_download(self):
        output_dir = self.path_input.text().strip()

        if self._is_playlist:
            # Gather selected videos
            entries = self._playlist_info.get("entries", [])
            selected = []
            for i, item in enumerate(self._playlist_checkboxes):
                if item.checkState() == Qt.CheckState.Checked and i < len(entries):
                    selected.append(entries[i])

            if not selected:
                QMessageBox.warning(self, "No Selection", "Please select at least one video.")
                return

            # Map quality combo to yt-dlp format
            quality_map = {
                0: "bestvideo+bestaudio/best",  # Best
                1: "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                2: "bestvideo[height<=720]+bestaudio/best[height<=720]",
                3: "bestvideo[height<=480]+bestaudio/best[height<=480]",
                4: "bestvideo[height<=360]+bestaudio/best[height<=360]",
                5: "bestaudio/best",  # Audio Only
            }
            quality = quality_map.get(self.quality_combo.currentIndex(), "best")
            self.download_playlist.emit(selected, quality, output_dir)
        else:
            # Single video
            selected = self.format_table.selectedItems()
            if not selected:
                return
            row = selected[0].row()
            format_id = self.format_table.item(row, 0).text()
            codec_text = self.format_table.item(row, 4).text()
            
            # If the selected format is missing audio (or video), use yt-dlp to merge
            if format_id != "best" and "+" not in codec_text and "audio" not in codec_text.lower():
                format_id = f"{format_id}+bestaudio/{format_id}"

            self.download_video.emit(self.url_input.text().strip(), format_id, output_dir)

        self.accept()
