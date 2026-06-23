"""
Add Download Dialog - Allows user to paste a URL and configure download settings.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFileDialog, QSpinBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import os
from pathlib import Path


class AddDownloadDialog(QDialog):
    """Dialog to add a new download by URL."""

    download_requested = pyqtSignal(str, str, str, int)  # url, filename, save_path, segments

    DIALOG_STYLE = """
        QDialog {
            background: #12132a;
        }
        QLabel {
            color: #e0e0e0;
            font-size: 12px;
        }
        QLineEdit {
            background: #1e1f36;
            border: 1px solid #2a2b4a;
            border-radius: 8px;
            padding: 10px 14px;
            color: #e0e0e0;
            font-size: 13px;
            selection-background-color: #6C63FF;
        }
        QLineEdit:focus {
            border: 1px solid #6C63FF;
        }
        QSpinBox {
            background: #1e1f36;
            border: 1px solid #2a2b4a;
            border-radius: 8px;
            padding: 8px 12px;
            color: #e0e0e0;
            font-size: 13px;
        }
        QSpinBox:focus {
            border: 1px solid #6C63FF;
        }
        QPushButton {
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
        }
        QGroupBox {
            border: 1px solid #2a2b4a;
            border-radius: 10px;
            margin-top: 16px;
            padding-top: 20px;
            color: #aaa;
            font-size: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px;
        }
    """

    def __init__(self, default_path: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Download")
        self.setFixedSize(520, 380)
        self.setStyleSheet(self.DIALOG_STYLE)
        self.default_path = default_path or str(Path.home() / "Downloads")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("⬇  Add New Download")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; font-size: 16px;")
        layout.addWidget(title)

        # URL
        url_label = QLabel("Download URL")
        layout.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/file.zip")
        layout.addWidget(self.url_input)

