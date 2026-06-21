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

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                filename TEXT NOT NULL,
                save_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                downloaded_size INTEGER DEFAULT 0,
                status TEXT DEFAULT 'queued',
                speed REAL DEFAULT 0,
                segments INTEGER DEFAULT 8,
                date_added TEXT DEFAULT CURRENT_TIMESTAMP,
                date_completed TEXT,
                mime_type TEXT DEFAULT '',
                resumable INTEGER DEFAULT 0,
                error_message TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # Default download directory
        default_dl_dir = str(Path.home() / "TDdownloader")
        os.makedirs(default_dl_dir, exist_ok=True)

        # Insert default settings
        defaults = {
            "download_dir": default_dl_dir,
            "max_concurrent": "3",
            "segments": "8",
            "server_port": "5000",
            "theme": "dark",
            "max_speed": "0",
        }
        for key, value in defaults.items():
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        conn.commit()
        conn.close()

    # ─── Download CRUD ───────────────────────────────────────

    def add_download(self, url, filename, save_path, file_size=0, segments=8, mime_type="", resumable=False):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO downloads (url, filename, save_path, file_size, segments, mime_type, resumable)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (url, filename, save_path, file_size, segments, mime_type, int(resumable)),
        )
        download_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return download_id

    def update_progress(self, download_id, downloaded_size, speed=0):
        conn = self._get_conn()
        conn.execute(
            "UPDATE downloads SET downloaded_size=?, speed=?, status='downloading' WHERE id=?",
            (downloaded_size, speed, download_id),
        )
        conn.commit()
        conn.close()

    def set_status(self, download_id, status, error_message=""):
        conn = self._get_conn()
        extra = ""
        params = [status, error_message, download_id]
        if status == "completed":
            extra = ", date_completed=?"
            params = [status, error_message, datetime.now().isoformat(), download_id]
        conn.execute(
            f"UPDATE downloads SET status=?, error_message=?{extra} WHERE id=?",
            params,
        )
        conn.commit()
        conn.close()

    def get_download(self, download_id):
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM downloads WHERE id=?", (download_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_downloads(self):
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM downloads ORDER BY date_added DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_downloads_by_status(self, status):
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM downloads WHERE status=? ORDER BY date_added DESC", (status,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_download(self, download_id):
        conn = self._get_conn()
        conn.execute("DELETE FROM downloads WHERE id=?", (download_id,))
        conn.commit()
        conn.close()

    def clear_completed(self):
        conn = self._get_conn()
        conn.execute("DELETE FROM downloads WHERE status='completed'")
        conn.commit()
        conn.close()

    def update_file_size(self, download_id, file_size, resumable):
        conn = self._get_conn()
        conn.execute(
            "UPDATE downloads SET file_size=?, resumable=? WHERE id=?",
            (file_size, int(resumable), download_id),
        )
        conn.commit()
        conn.close()
