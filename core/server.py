"""
FastAPI local server interceptor.
Listens on localhost for download tasks sent by the Chrome extension.
"""
import uvicorn
import threading
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Callable


class DownloadRequest(BaseModel):
    url: str
    filename: Optional[str] = ""
    filesize: Optional[int] = 0
    mime_type: Optional[str] = ""
    referrer: Optional[str] = ""


class ServerResponse(BaseModel):
    status: str
    message: str


class LocalServer:
    """FastAPI server running on localhost to receive download tasks from Chrome extension."""

    def __init__(self, port: int = 5000):
        self.port = port
        self.app = FastAPI(title="Ubuntu Download Manager API")
        self._download_callback: Optional[Callable] = None
        self._server_thread: Optional[threading.Thread] = None
        self._server: Optional[uvicorn.Server] = None

        # CORS for Chrome extension
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()
