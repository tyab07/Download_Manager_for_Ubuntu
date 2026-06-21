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

    def __repr__(self):
        return f"<LocalServer(port={self.port})>"

    def set_download_callback(self, callback: Callable):
        """Set callback function when new download is received."""
        self._download_callback = callback

    def _setup_routes(self):
        @self.app.get("/ping")
        async def ping():
            return {"status": "ok", "app": "UbuntuDownloader"}

        @self.app.post("/download", response_model=ServerResponse)
        async def add_download(req: DownloadRequest):
            if not req.url:
                raise HTTPException(status_code=400, detail="URL is required")

            if self._download_callback:
                try:
                    self._download_callback(
                        url=req.url,
                        filename=req.filename or "",
                        filesize=req.filesize or 0,
                        mime_type=req.mime_type or "",
                    )
                    return ServerResponse(
                        status="ok",
                        message=f"Download added: {req.filename or req.url}"
                    )
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
            else:
                raise HTTPException(status_code=503, detail="Download manager not ready")

        @self.app.get("/status")
        async def server_status():
            return {
                "status": "running",
                "port": self.port,
            }

    def start(self):
        """Start the server in a background thread."""
        config = uvicorn.Config(
            app=self.app,
            host="127.0.0.1",
            port=self.port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)

        self._server_thread = threading.Thread(
            target=self._server.run,
            daemon=True,
            name="DownloadServer",
        )
        self._server_thread.start()

    def stop(self):
        """Stop the server."""
        if self._server:
            self._server.should_exit = True
