"""
Multi-threaded segmented download engine using aiohttp with HTTP Range headers.
Supports pause, resume, and concurrent segment downloading.
"""
import asyncio
import aiohttp
import os
import time
import tempfile
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field


