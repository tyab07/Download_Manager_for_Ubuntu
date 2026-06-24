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
