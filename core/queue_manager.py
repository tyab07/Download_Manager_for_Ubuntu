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
