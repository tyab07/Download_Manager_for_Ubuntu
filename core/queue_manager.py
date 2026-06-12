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
