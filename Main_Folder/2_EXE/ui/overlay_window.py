"""
ui/overlay_window.py
Transparent always-on-top caption overlay window.
OBS captures this as a Window Source.
"""

import tkinter as tk
from typing import Optional


class OverlayWindow:
    def __init__(self, parent, theme):
        self.T    = theme
        self._win: Optional[tk.Toplevel] = None
        self._lbl: Optional[tk.Label]   = None
        self._parent = parent

    def show(self):
        if self._win and self._win.winfo_exists():
            return
        T = self.T
        self._win = tk.Toplevel(self._parent)
        self._win.title("SignBridge Overlay")
        self._win.geometry("900x120+200+800")
        self._win.configure(bg="#000001")    # near-black for chroma-key
        self._win.overrideredirect(True)     # no title bar
        self._win.attributes("-topmost", True)
        self._win.attributes("-transparentcolor", "#000001")

        self._lbl = tk.Label(
            self._win, text="",
            font=("Segoe UI", 32, "bold"),
            bg="#000001", fg="#00FF99",
            padx=24, pady=12,
            wraplength=860,
        )
        self._lbl.pack(fill="both", expand=True)

        # Drag to reposition
        self._win.bind("<Button-1>",   self._drag_start)
        self._win.bind("<B1-Motion>",  self._drag_move)
        self._lbl.bind("<Button-1>",   self._drag_start)
        self._lbl.bind("<B1-Motion>",  self._drag_move)

    def hide(self):
        if self._win:
            self._win.destroy()
            self._win = None

    def update_text(self, text: str):
        if self._lbl and self._win and self._win.winfo_exists():
            self._lbl.config(text=text)

    # ── drag ────────────────────────────────────────────────────
    def _drag_start(self, event):
        self._drag_x = event.x_root - self._win.winfo_x()
        self._drag_y = event.y_root - self._win.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self._win.geometry(f"+{x}+{y}")
