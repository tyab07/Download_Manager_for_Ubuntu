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

    async def start_download(self, task: DownloadTask):
        """Start or resume a segmented download."""
        self._active_tasks[task.download_id] = task
        task.status = "downloading"

        if self._status_callback:
            self._status_callback(task.download_id, "downloading")

        try:
            # Get file info if we don't have it
            if task.file_size == 0:
                file_size, resumable, _ = await self.get_file_info(task.url)
                task.file_size = file_size
                task.resumable = resumable

            if task.resumable and task.file_size > 0 and task.segments > 1:
                await self._segmented_download(task)
            else:
                await self._single_download(task)

            if not task._cancel:
                task.status = "completed"
                if self._status_callback:
                    self._status_callback(task.download_id, "completed")

        except asyncio.CancelledError:
            task.status = "paused"
            if self._status_callback:
                self._status_callback(task.download_id, "paused")
        except Exception as e:
            task.status = "error"
            task.error = str(e)
            if self._status_callback:
                self._status_callback(task.download_id, "error", str(e))
        finally:
            if task.download_id in self._active_tasks and task.status in ("completed", "error"):
                del self._active_tasks[task.download_id]

    async def _segmented_download(self, task: DownloadTask):
        """Download file in multiple segments concurrently."""
        segment_size = task.file_size // task.segments
        temp_dir = tempfile.mkdtemp(prefix=f"dl_{task.download_id}_")

        # Create segment infos
        segments = []
        for i in range(task.segments):
            start = i * segment_size
            end = task.file_size - 1 if i == task.segments - 1 else (i + 1) * segment_size - 1
            temp_file = os.path.join(temp_dir, f"segment_{i}.tmp")

            # Check for existing partial segment
            existing_downloaded = 0
            if os.path.exists(temp_file):
                existing_downloaded = os.path.getsize(temp_file)

            seg = SegmentInfo(
                index=i,
                start=start + existing_downloaded,
                end=end,
                downloaded=existing_downloaded,
                temp_file=temp_file,
            )
            segments.append(seg)

        task._segment_infos = segments

        # Download all segments concurrently
        sem = asyncio.Semaphore(task.segments)
        download_tasks = [
            self._download_segment(task, seg, sem) for seg in segments
        ]
        await asyncio.gather(*download_tasks)

        if task._cancel:
            return

        # Merge segments into final file
        output_path = os.path.join(task.save_path, task.filename)
        os.makedirs(task.save_path, exist_ok=True)
        with open(output_path, "wb") as outfile:
            for seg in sorted(segments, key=lambda s: s.index):
                with open(seg.temp_file, "rb") as infile:
                    while True:
                        chunk = infile.read(self.CHUNK_SIZE)
                        if not chunk:
                            break
                        outfile.write(chunk)
                os.remove(seg.temp_file)

        # Cleanup temp dir
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass

    async def _download_segment(self, task: DownloadTask, seg: SegmentInfo, sem: asyncio.Semaphore):
        """Download a single segment with Range header."""
        async with sem:
            session = await self._get_session()
            headers = {"Range": f"bytes={seg.start}-{seg.end}"}

            async with session.get(task.url, headers=headers) as resp:
                mode = "ab" if seg.downloaded > 0 else "wb"
                with open(seg.temp_file, mode) as f:
                    async for chunk in resp.content.iter_chunked(self.CHUNK_SIZE):
                        # Check for pause
                        await task._pause_event.wait()
                        if task._cancel:
                            return

                        f.write(chunk)
                        seg.downloaded += len(chunk)
                        task.downloaded = sum(s.downloaded for s in task._segment_infos)

                        if self._progress_callback:
                            self._progress_callback(task.download_id, task.downloaded, task.file_size)

    async def _single_download(self, task: DownloadTask):
        """Single-stream download for non-resumable files."""
        session = await self._get_session()
        output_path = os.path.join(task.save_path, task.filename)
        os.makedirs(task.save_path, exist_ok=True)

        start_time = time.time()
        last_update = start_time

        async with session.get(task.url) as resp:
            if task.file_size == 0:
                task.file_size = int(resp.headers.get("Content-Length", 0))

            with open(output_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(self.CHUNK_SIZE):
                    await task._pause_event.wait()
                    if task._cancel:
                        return

                    f.write(chunk)
                    task.downloaded += len(chunk)

                    now = time.time()
                    if now - last_update > 0.25:
                        elapsed = now - start_time
                        task.speed = task.downloaded / elapsed if elapsed > 0 else 0
                        last_update = now
                        if self._progress_callback:
                            self._progress_callback(task.download_id, task.downloaded, task.file_size)

