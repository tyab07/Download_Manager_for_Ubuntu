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

