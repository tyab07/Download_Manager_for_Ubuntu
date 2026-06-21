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
