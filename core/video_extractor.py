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

    def extract_info(self, url: str) -> dict:
        """Extract video information without downloading."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    return {"error": "Could not extract info"}

                formats = []
                for f in info.get("formats", []):
                    fmt = {
                        "format_id": f.get("format_id", ""),
                        "ext": f.get("ext", ""),
                        "resolution": f.get("resolution", "audio only"),
                        "fps": f.get("fps"),
                        "vcodec": f.get("vcodec", "none"),
                        "acodec": f.get("acodec", "none"),
                        "filesize": f.get("filesize") or f.get("filesize_approx", 0),
                        "format_note": f.get("format_note", ""),
                        "quality": f.get("quality", 0),
                        "tbr": f.get("tbr", 0),
                    }
                    # Filter out storyboard / mhtml formats
                    if fmt["ext"] in ("mhtml",):
                        continue
                    formats.append(fmt)

                # Sort: video+audio first, then by quality descending
                formats.sort(key=lambda x: (
                    x["vcodec"] != "none" and x["acodec"] != "none",
                    x["tbr"] or 0
                ), reverse=True)

                return {
                    "title": info.get("title", "Unknown"),
                    "thumbnail": info.get("thumbnail", ""),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader", "Unknown"),
                    "view_count": info.get("view_count", 0),
                    "description": (info.get("description") or "")[:300],
                    "webpage_url": info.get("webpage_url", url),
                    "formats": formats,
                }
        except Exception as e:
            return {"error": str(e)}

