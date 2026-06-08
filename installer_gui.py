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
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=self.ACCENT, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="TDDownloader", bg=self.ACCENT, fg="white",
                 font=("Segoe UI", 22, "bold")).pack(side="left", padx=24)
        tk.Label(hdr, text="v2.0  ·  Linux Installer", bg=self.ACCENT,
                 fg="rgba(255,255,255,0.7)", font=("Segoe UI", 11)).pack(
                 side="left", padx=4, pady=26)

        # Body
        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True, padx=32, pady=20)

        # Description
        tk.Label(body,
                 text="This will install TDDownloader on your system,\n"
                      "set up the launcher, and create a desktop shortcut.",
                 bg=self.BG, fg=self.FG_DIM, font=("Segoe UI", 11),
                 justify="left").pack(anchor="w", pady=(0, 18))

        # --- Current step label ---
        self.step_var = tk.StringVar(value="Ready to install…")
        tk.Label(body, textvariable=self.step_var, bg=self.BG, fg=self.FG,
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x")

        # Progress bar
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TD.Horizontal.TProgressbar",
                         troughcolor="#2a2b4a",
                         background=self.ACCENT,
                         borderwidth=0, thickness=10)
        self.pbar = ttk.Progressbar(body, style="TD.Horizontal.TProgressbar",
                                     maximum=len(STEPS), length=576)
        self.pbar.pack(pady=(8, 4))

        # Log output
        self.log = tk.Text(body, bg="#0e0f20", fg=self.FG_DIM,
                           font=("Monospace", 9), relief="flat",
                           height=10, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True, pady=(12, 16))

        # Footer buttons
        btn_frame = tk.Frame(self, bg=self.BG)
        btn_frame.pack(fill="x", padx=32, pady=(0, 20))

        self.close_btn = tk.Button(btn_frame, text="Cancel",
                                   bg="#2a2b4a", fg=self.FG,
                                   activebackground="#3a3b5a",
                                   relief="flat", padx=20, pady=8,
                                   font=("Segoe UI", 10),
                                   command=self._on_close)
        self.close_btn.pack(side="right", padx=(8, 0))

        self.install_btn = tk.Button(btn_frame, text="  Install  ",
                                     bg=self.ACCENT, fg="white",
                                     activebackground="#7B73FF",
                                     relief="flat", padx=20, pady=8,
                                     font=("Segoe UI", 10, "bold"),
                                     command=self._start_install)
        self.install_btn.pack(side="right")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _log(self, msg, color=None):
        self.log.configure(state="normal")
        tag = None
        if color:
            tag = color
            self.log.tag_configure(tag, foreground=color)
        self.log.insert("end", msg + "\n", tag or ())
        self.log.see("end")
        self.log.configure(state="disabled")

    def _step(self, name, index):
        self.step_var.set(f"[{index+1}/{len(STEPS)}]  {name}…")
        self.pbar["value"] = index
        self.update_idletasks()
        self._log(f"  →  {name}")

    def _done(self):
        self.pbar["value"] = len(STEPS)
        self.step_var.set("✓  Installation complete!")
        self._log("\n✓  TDDownloader has been installed successfully!", self.SUCCESS)
        self._log(f"\n  Launcher:   tddownloader", "#aaaaff")
        self._log(f"  Downloads:  {DOWNLOAD_DIR}", "#aaaaff")
        self._log(
            f"\n  Chrome Extension:\n"
            f"    1. Open  chrome://extensions\n"
            f"    2. Enable Developer mode\n"
            f"    3. Click Load unpacked\n"
            f"    4. Select: {INSTALL_DIR}/chrome_extension",
            "#aaaaff"
        )
        self.install_btn.configure(state="disabled")
        self.close_btn.configure(text="Close", bg=self.SUCCESS,
                                  fg="white", activebackground="#66BB6A")

    def _fail(self, msg):
        self.step_var.set("✗  Installation failed")
        self._log(f"\n✗  Error: {msg}", self.ERROR)
        self.install_btn.configure(state="normal", text="  Retry  ")
        messagebox.showerror("Installation Failed",
                             f"An error occurred:\n{msg}")

    # ── Install logic (runs in a thread) ─────────────────────────────────────
    def _start_install(self):
        self.install_btn.configure(state="disabled")
        threading.Thread(target=self._install_thread, daemon=True).start()

    def _install_thread(self):
        try:
            # Step 0: Check Python
            self.after(0, self._step, STEPS[0], 0)
            python = find_python()
            if not python:
                raise RuntimeError(
                    "Python 3.10+ not found.\n"
                    "Install it: sudo apt install python3 python3-venv python3-pip")
            self._log(f"     Found Python: {python}")

            # Check / install tkinter notice
            try:
                subprocess.check_call(
                    [python, "-c", "import pip"], stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                raise RuntimeError(
                    "pip is not available.\n"
                    "Run: sudo apt install python3-pip python3-venv")

            # Step 1: Install system dependencies
            self.after(0, self._step, STEPS[1], 1)
            if not shutil.which("ffmpeg"):
                self._log("     ffmpeg not found. Attempting to install...")
                try:
                    subprocess.run(
                        ["x-terminal-emulator", "-e", "sudo apt-get update && sudo apt-get install -y ffmpeg"],
                        check=False
                    )
                except Exception:
                    pass
                if not shutil.which("ffmpeg"):
                    self._log("     WARNING: ffmpeg could not be installed. YouTube audio merging will fail!", self.ERROR)
            else:
                self._log("     Found ffmpeg")

            # Step 2: Create directories
            self.after(0, self._step, STEPS[2], 2)
            for d in [INSTALL_DIR / "core", INSTALL_DIR / "gui",
                       INSTALL_DIR / "chrome_extension" / "icons",
                       INSTALL_DIR / "assets"]:
                d.mkdir(parents=True, exist_ok=True)

            # Step 3: Copy files
            self.after(0, self._step, STEPS[3], 3)
            file_roots = ["main.py", "requirements.txt", "uninstall.sh"]
            for f in file_roots:
                src = SCRIPT_DIR / f
                if src.exists():
                    shutil.copy2(src, INSTALL_DIR / f)
            for folder in ["core", "gui", "chrome_extension"]:
                src = SCRIPT_DIR / folder
                if src.exists():
                    copy_tree(src, INSTALL_DIR / folder)

            # Copy desktop
            desk_src = SCRIPT_DIR / "tddownloader.desktop"
            if desk_src.exists():
                shutil.copy2(desk_src, INSTALL_DIR / "tddownloader.desktop")

            # Step 4: Create venv
            self.after(0, self._step, STEPS[4], 4)
            venv = INSTALL_DIR / "venv"
            subprocess.check_call(
                [python, "-m", "venv", str(venv)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Step 5: Install deps
            self.after(0, self._step, STEPS[5], 5)
            pip = venv / "bin" / "pip"
            req = INSTALL_DIR / "requirements.txt"
            subprocess.check_call(
                [str(pip), "install", "--upgrade", "pip", "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.check_call(
                [str(pip), "install", "-r", str(req), "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Step 6: Launcher
            self.after(0, self._step, STEPS[6], 6)
            BIN_DIR.mkdir(parents=True, exist_ok=True)
            launcher = BIN_DIR / "tddownloader"
            launcher.write_text(
                f"#!/usr/bin/env bash\n"
                f"cd {INSTALL_DIR}\n"
                f"exec {venv}/bin/python main.py \"$@\"\n"
            )
            launcher.chmod(0o755)

            # Make sure ~/.local/bin is in PATH
            for rc in [Path.home() / ".bashrc", Path.home() / ".zshrc"]:
                if rc.exists():
                    content = rc.read_text()
                    if str(BIN_DIR) not in content:
                        rc.write_text(
                            content +
                            f'\nexport PATH="{BIN_DIR}:$PATH"  # TDDownloader\n')
                    break

            # Step 7: Desktop shortcut
            self.after(0, self._step, STEPS[7], 7)
            DESKTOP_DIR.mkdir(parents=True, exist_ok=True)

            icon_path = INSTALL_DIR / "assets" / "tddownloader.svg"
            icon_path.write_text(SVG_ICON)

            desktop_content = (
                "[Desktop Entry]\n"
                "Name=TDDownloader\n"
                "Comment=IDM-like Download Manager for Linux\n"
                f"Exec={launcher}\n"
                f"Icon={icon_path}\n"
                "Type=Application\n"
                "Categories=Network;FileTransfer;\n"
                "Terminal=false\n"
                "StartupNotify=true\n"
            )
            desktop_file = DESKTOP_DIR / "tddownloader.desktop"
            desktop_file.write_text(desktop_content)
            desktop_file.chmod(0o755)

            subprocess.run(
                ["update-desktop-database", str(DESKTOP_DIR)],
                stderr=subprocess.DEVNULL)

            # Step 8: Downloads folder
            self.after(0, self._step, STEPS[8], 8)
            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

            # Step 9: Done
            self.after(0, self._step, STEPS[9], 9)
            self.after(0, self._done)

        except Exception as e:
            self.after(0, self._fail, str(e))

    def _on_close(self):
        if not messagebox.askokcancel("Exit", "Cancel installation?"):
            return
        self.destroy()

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
