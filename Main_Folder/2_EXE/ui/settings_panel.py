"""
ui/settings_panel.py
Modal settings dialog (opened from sidebar).
"""

import tkinter as tk
from tkinter import messagebox
import json, os


class SettingsPanel:
    def __init__(self, parent, theme, settings: dict, on_save):
        self.T        = theme
        self.settings = settings
        self.on_save  = on_save
        self._build(parent)

    def _build(self, parent):
        T    = self.T
        win  = tk.Toplevel(parent)
        win.title("Settings — SignBridge Pro")
        win.geometry("480x580")
        win.configure(bg=T.BG_BASE)
        win.resizable(False, False)
        win.transient(parent)
        win.grab_set()

        tk.Label(win, text="⚙️  Settings",
                 font=("Segoe UI", 18, "bold"),
                 bg=T.BG_BASE, fg=T.TEXT, pady=20).pack()

        frame = tk.Frame(win, bg=T.BG_BASE, padx=28)
        frame.pack(fill="both", expand=True)

        # Confidence threshold
        self._conf_var = tk.DoubleVar(value=self.settings.get("confidence_threshold", 0.80))
        self._make_slider(frame, "Confidence Threshold",
                          self._conf_var, 0.5, 1.0, 0.05)

        # Display interval
        self._interval_var = tk.DoubleVar(value=self.settings.get("display_interval", 2.5))
        self._make_slider(frame, "Display Interval (s)",
                          self._interval_var, 0.5, 5.0, 0.5)

        # Camera index
        cam_f = tk.Frame(frame, bg=T.BG_BASE)
        cam_f.pack(fill="x", pady=8)
        tk.Label(cam_f, text="Camera Index:",
                 font=("Segoe UI", 11), bg=T.BG_BASE, fg=T.TEXT2).pack(anchor="w")
        self._cam_var = tk.IntVar(value=self.settings.get("camera_index", 0))
        tk.Spinbox(cam_f, from_=0, to=5, textvariable=self._cam_var,
                   font=("Segoe UI", 11),
                   bg=T.BG_CARD2, fg=T.TEXT, relief="flat",
                   buttonbackground=T.BG_CARD3).pack(fill="x", pady=4)

        # Toggles
        self._auto_save_var  = tk.BooleanVar(value=self.settings.get("auto_save", True))
        self._show_conf_var  = tk.BooleanVar(value=self.settings.get("show_confidence", True))

        for label, var in [
            ("Auto-save translations", self._auto_save_var),
            ("Show confidence scores", self._show_conf_var),
        ]:
            tk.Checkbutton(frame, text=label, variable=var,
                           font=("Segoe UI", 11),
                           bg=T.BG_BASE, fg=T.TEXT2,
                           selectcolor=T.BG_CARD2,
                           activebackground=T.BG_BASE).pack(anchor="w", pady=4)

        # Buttons
        btn_f = tk.Frame(win, bg=T.BG_BASE, pady=16)
        btn_f.pack()
        tk.Button(btn_f, text="💾  Save",
                  font=("Segoe UI", 11, "bold"),
                  bg=T.ACCENT, fg="#000", relief="flat",
                  padx=24, pady=8, cursor="hand2",
                  command=lambda: self._save(win)).pack(side="left", padx=8)
        tk.Button(btn_f, text="✕  Cancel",
                  font=("Segoe UI", 11, "bold"),
                  bg=T.ACCENT3, fg="#FFF", relief="flat",
                  padx=24, pady=8, cursor="hand2",
                  command=win.destroy).pack(side="left", padx=8)

    def _make_slider(self, parent, label, var, from_, to, resolution):
        T = self.T
        f = tk.Frame(parent, bg=T.BG_BASE)
        f.pack(fill="x", pady=8)
        tk.Label(f, text=f"{label}:", font=("Segoe UI", 11),
                 bg=T.BG_BASE, fg=T.TEXT2).pack(anchor="w")
        tk.Scale(f, from_=from_, to=to, resolution=resolution,
                 orient="horizontal", variable=var,
                 bg=T.BG_BASE, fg=T.ACCENT,
                 troughcolor=T.BG_CARD2,
                 highlightthickness=0, relief="flat").pack(fill="x")

    def _save(self, win):
        self.settings.update({
            "confidence_threshold": self._conf_var.get(),
            "display_interval":     self._interval_var.get(),
            "camera_index":         self._cam_var.get(),
            "auto_save":            self._auto_save_var.get(),
            "show_confidence":      self._show_conf_var.get(),
        })
        self.on_save(self.settings)
        messagebox.showinfo("Settings", "Settings saved!")
        win.destroy()
