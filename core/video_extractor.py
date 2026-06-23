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

    def get_best_formats(self, url: str) -> list:
        """Get simplified list of best format options."""
        info = self.extract_info(url)
        if "error" in info:
            return []

        seen = set()
        best = []
        for f in info.get("formats", []):
            res = f.get("resolution", "audio only")
            ext = f.get("ext", "")
            key = f"{res}_{ext}"
            if key not in seen:
                seen.add(key)
                size = f.get("filesize", 0)
                best.append({
                    "format_id": f["format_id"],
                    "label": f"{res} ({ext}) - {self._format_size(size)}" if size else f"{res} ({ext})",
                    "ext": ext,
                    "resolution": res,
                    "filesize": size,
                })
        return best

    def download_video(self, url: str, format_id: str = "best",
                       output_dir: str = None, download_id: int = 0) -> dict:
        """Download video with selected format."""
        output = output_dir or self.download_dir
        os.makedirs(output, exist_ok=True)

        def progress_hook(d):
            if d["status"] == "downloading" and self._progress_callback:
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                self._progress_callback(download_id, downloaded, total)
            elif d["status"] == "finished" and self._status_callback:
                self._status_callback(download_id, "completed")

        ydl_opts = {
            "format": format_id,
            "outtmpl": os.path.join(output, "%(title)s.%(ext)s"),
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return {
                    "success": True,
                    "filename": os.path.basename(filename),
                    "path": filename,
                    "title": info.get("title", ""),
                }
        except Exception as e:
            if self._status_callback:
                self._status_callback(download_id, "error", str(e))
            return {"success": False, "error": str(e)}

    def extract_playlist(self, url: str) -> dict:
        """Extract playlist info — returns list of video entries."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "ignoreerrors": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    return {"error": "Could not extract playlist info"}

                entries = []
                for entry in info.get("entries", []) or []:
                    if entry is None:
                        continue
                    entries.append({
                        "url": entry.get("url") or entry.get("webpage_url", ""),
                        "title": entry.get("title", "Unknown"),
                        "duration": entry.get("duration", 0),
                        "id": entry.get("id", ""),
                    })

                return {
                    "title": info.get("title", "Playlist"),
                    "uploader": info.get("uploader", "Unknown"),
                    "count": len(entries),
                    "entries": entries,
                }
        except Exception as e:
            return {"error": str(e)}

