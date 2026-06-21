"""
SQLite Database Manager for download history and queue management.
"""
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads.db")


class DownloadDatabase:
    """Manages SQLite database for download records and queue."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
