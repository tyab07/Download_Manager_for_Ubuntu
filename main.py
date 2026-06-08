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

