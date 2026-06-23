"""
yt-dlp wrapper for video extraction and downloading.
Supports YouTube, Facebook, TikTok, and other platforms.
"""
import yt_dlp
import os
import json
from typing import Optional, Callable
from pathlib import Path


class VideoExtractor:
    """Extracts video info and downloads using yt-dlp."""

    def __init__(self, download_dir: str = None):
        self.download_dir = download_dir or str(Path.home() / "Downloads")
        self._progress_callback: Optional[Callable] = None
        self._status_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        self._progress_callback = callback

    def set_status_callback(self, callback: Callable):
        self._status_callback = callback

