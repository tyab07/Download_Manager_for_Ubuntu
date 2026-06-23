"""
yt-dlp wrapper for video extraction and downloading.
Supports YouTube, Facebook, TikTok, and other platforms.
"""
import yt_dlp
import os
import json
from typing import Optional, Callable
from pathlib import Path
