"""
Download queue manager with concurrent download limits.
"""
import asyncio
from typing import Optional, Callable
from core.downloader import DownloadEngine, DownloadTask
from core.database import DownloadDatabase
