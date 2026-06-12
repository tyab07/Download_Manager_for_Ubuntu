"""
Download queue manager with concurrent download limits.
"""
import asyncio
from typing import Optional, Callable
from core.downloader import DownloadEngine, DownloadTask
from core.database import DownloadDatabase


class QueueManager:
    """Manages download queue with concurrency control."""

    def __init__(self, db: DownloadDatabase, engine: DownloadEngine, max_concurrent: int = 3):
        self.db = db
        self.engine = engine
        self.max_concurrent = max_concurrent
        self._active_downloads: dict[int, asyncio.Task] = {}
        self._queue: list[DownloadTask] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    @property
    def active_count(self) -> int:
        return len(self._active_downloads)

    def add_to_queue(self, task: DownloadTask):
        """Add download to queue and start if slots available."""
        self._queue.append(task)
        self._try_start_next()

    def _try_start_next(self):
        """Start next queued download if concurrent limit allows."""
        while self._queue and self.active_count < self.max_concurrent:
            task = self._queue.pop(0)
            if self._loop:
                async_task = self._loop.create_task(self._run_download(task))
                self._active_downloads[task.download_id] = async_task

    async def _run_download(self, task: DownloadTask):
        """Run a download and manage queue after completion."""
        try:
            await self.engine.start_download(task)
        except Exception as e:
            task.status = "error"
            task.error = str(e)
