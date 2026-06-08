#!/usr/bin/env python3
"""
TDDownloader - Main Entry Point
A powerful IDM-like download manager for Linux with:
- Multi-threaded segmented downloads
- Video extraction (yt-dlp)
- YouTube playlist downloads
- Chrome extension integration
- Advanced PyQt6 dark theme GUI
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Ensure default download directory exists
    dl_dir = os.path.join(os.path.expanduser("~"), "TDdownloader")
    os.makedirs(dl_dir, exist_ok=True)

    # Set application metadata
    app.setApplicationName("TDDownloader")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("TDDownloader")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Dark palette
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0d0e1a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1e1f36"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#222340"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1e1f36"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1e1f36"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#6C63FF"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
