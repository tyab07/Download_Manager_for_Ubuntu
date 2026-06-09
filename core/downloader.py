"""
Multi-threaded segmented download engine using aiohttp with HTTP Range headers.
Supports pause, resume, and concurrent segment downloading.
"""
import asyncio
import aiohttp
import os
import time
import tempfile
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field


@dataclass
class SegmentInfo:
    index: int
    start: int
    end: int
    downloaded: int = 0
    temp_file: str = ""


@dataclass
class DownloadTask:
    download_id: int
    url: str
    filename: str
    save_path: str
    file_size: int = 0
    downloaded: int = 0
    segments: int = 8
    speed: float = 0.0
    status: str = "queued"  # queued, downloading, paused, completed, error
    resumable: bool = False
    error: str = ""
    _pause_event: asyncio.Event = field(default_factory=asyncio.Event)
    _cancel: bool = False
    _segment_infos: list = field(default_factory=list)

    def __post_init__(self):
        self._pause_event.set()  # Not paused initially


class DownloadEngine:
    """Async multi-segment downloader with pause/resume support."""

    CHUNK_SIZE = 1024 * 64  # 64KB chunks

    def __init__(self):
        self._active_tasks: dict[int, DownloadTask] = {}
        self._progress_callback: Optional[Callable] = None
        self._status_callback: Optional[Callable] = None
        self._session: Optional[aiohttp.ClientSession] = None

    def set_progress_callback(self, callback: Callable):
        self._progress_callback = callback

    def set_status_callback(self, callback: Callable):
        self._status_callback = callback

    async def _get_session(self):
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=None, connect=30)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
            )
        return self._session

    async def get_file_info(self, url: str) -> tuple[int, bool, str]:
        """Get file size, resume support, and filename from URL."""
        session = await self._get_session()
        try:
            async with session.head(url, allow_redirects=True) as resp:
                file_size = int(resp.headers.get("Content-Length", 0))
                accept_ranges = resp.headers.get("Accept-Ranges", "none")
                resumable = accept_ranges.lower() == "bytes" and file_size > 0
                content_disp = resp.headers.get("Content-Disposition", "")
                filename = ""
                if "filename=" in content_disp:
                    filename = content_disp.split("filename=")[-1].strip('"').strip("'")
                if not filename:
                    filename = url.split("/")[-1].split("?")[0]
                if not filename:
                    filename = "download"
                return file_size, resumable, filename
        except Exception:
            return 0, False, url.split("/")[-1].split("?")[0] or "download"

