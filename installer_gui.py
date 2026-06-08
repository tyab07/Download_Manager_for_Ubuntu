#!/usr/bin/env python3
"""
TDDownloader — GUI Installer
Double-click to launch. No terminal required.
Uses only Python's built-in tkinter (zero extra dependencies).
"""
import sys
import os
import subprocess
import threading
import shutil
from pathlib import Path

# ── Ensure tkinter is available ───────────────────────────────────────────────
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    subprocess.run(["bash", "-c",
        "x-terminal-emulator -e 'echo tkinter not found. "
        "Install python3-tk: sudo apt install python3-tk; read'"])
    sys.exit(1)

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent.resolve()
INSTALL_DIR   = Path.home() / ".local/share/tddownloader"
BIN_DIR       = Path.home() / ".local/bin"
DESKTOP_DIR   = Path.home() / ".local/share/applications"
ICON_DIR      = Path.home() / ".local/share/icons/hicolor/128x128/apps"
DOWNLOAD_DIR  = Path.home() / "TDdownloader"

SVG_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#6C63FF"/>
      <stop offset="100%" stop-color="#3F3D9E"/>
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="28" fill="url(#bg)"/>
  <g transform="translate(64,64)" stroke="white" stroke-width="6"
     stroke-linecap="round" stroke-linejoin="round" fill="none">
    <path d="M0,-30 L0,20"/>
    <polyline points="-15,5 0,20 15,5"/>
    <path d="M-25,30 L25,30"/>
  </g>
</svg>"""

# ── Installer steps ───────────────────────────────────────────────────────────
STEPS = [
    "Checking Python environment",
    "Installing dependencies (ffmpeg)",
    "Creating installation directory",
    "Copying application files",
    "Creating virtual environment",
    "Installing Python packages",
    "Creating launcher command",
    "Installing desktop shortcut",
    "Creating downloads folder",
    "Finalising",
]

