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

def find_python():
    for cmd in ["python3", "python"]:
        try:
            out = subprocess.check_output(
                [cmd, "-c",
                 "import sys; v=sys.version_info; "
                 "print(v.major, v.minor, v.patch if hasattr(v,'patch') else 0)"],
                text=True, stderr=subprocess.DEVNULL
            ).split()
            major, minor = int(out[0]), int(out[1])
            if major >= 3 and minor >= 10:
                return cmd
        except Exception:
            pass
    return None

def copy_tree(src: Path, dst: Path):
    for item in src.iterdir():
        if item.name in ("__pycache__", "venv", ".git"):
            continue
        if item.suffix in (".db", ".tar.gz"):
            continue
        target = dst / item.name
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            copy_tree(item, target)
        else:
            shutil.copy2(item, target)

# ── Main GUI class ────────────────────────────────────────────────────────────
class InstallerApp(tk.Tk):
    BG       = "#12132a"
    FG       = "#e0e0e0"
    ACCENT   = "#6C63FF"
    SUCCESS  = "#4CAF50"
    ERROR    = "#F44336"
    FG_DIM   = "#888888"

    def __init__(self):
        super().__init__()
        self.title("TDDownloader — Installer")
        self.configure(bg=self.BG)
        self.resizable(False, False)

        # Center window  640 × 440
        W, H = 640, 440
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI ────────────────────────────────────────────────────────────────────
