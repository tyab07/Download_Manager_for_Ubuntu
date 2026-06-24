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
