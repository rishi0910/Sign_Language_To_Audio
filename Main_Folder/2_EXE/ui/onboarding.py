"""
ui/onboarding.py
First-launch onboarding wizard (3 steps).
"""

import tkinter as tk
from tkinter import ttk


STEPS = [
    {
        "icon":  "🤟",
        "title": "Welcome to SignBridge Pro",
        "body":  (
            "SignBridge Pro translates your sign language gestures "
            "into spoken audio and live on-screen captions — in real time.\n\n"
            "It works with OBS Studio so your words appear on any "
            "video call platform like Zoom, Meet, or Teams."
        ),
    },
    {
        "icon":  "📷",
        "title": "Camera Setup",
        "body":  (
            "Make sure your webcam is connected and unobstructed.\n\n"
            "• Ensure good, even lighting on your hands.\n"
            "• Keep your hand within the camera frame.\n"
            "• The app supports ASL and ISL — choose your mode from the sidebar.\n\n"
            "Press F5 or click 'Start Translation' to begin."
        ),
    },
    {
        "icon":  "📺",
        "title": "OBS Integration",
        "body":  (
            "To show captions on video calls:\n\n"
            "1. Open OBS Studio.\n"
            "2. Add a Window Capture source → select this app's window.\n"
            "3. OR add a Text (GDI+) source → point it to the caption_output.txt file.\n"
            "4. Enable OBS Virtual Camera.\n"
            "5. Select 'OBS Virtual Camera' in Zoom / Meet.\n\n"
            "Click 'Connect to OBS' in the OBS panel to use WebSocket control."
        ),
    },
]


class OnboardingWizard:
    def __init__(self, parent, theme, on_done):
        self.T       = theme
        self.on_done = on_done
        self._step   = 0
        self._build(parent)

    def _build(self, parent):
        T = self.T
        self._win = tk.Toplevel(parent)
        self._win.title("SignBridge Pro — Getting Started")
        self._win.geometry("540x420")
        self._win.resizable(False, False)
        self._win.configure(bg=T.BG_BASE)
        self._win.transient(parent)
        self._win.grab_set()

        # Icon
        self._lbl_icon = tk.Label(self._win, font=("Segoe UI", 48),
                                   bg=T.BG_BASE, fg=T.ACCENT, pady=16)
        self._lbl_icon.pack()

        # Title
        self._lbl_title = tk.Label(self._win, font=("Segoe UI", 18, "bold"),
                                    bg=T.BG_BASE, fg=T.TEXT)
        self._lbl_title.pack()

        # Body
        self._lbl_body = tk.Label(self._win, font=("Segoe UI", 11),
                                   bg=T.BG_BASE, fg=T.TEXT2,
                                   wraplength=460, justify="left", pady=16)
        self._lbl_body.pack(fill="x", padx=40)

        # Dots indicator
        dots_f = tk.Frame(self._win, bg=T.BG_BASE)
        dots_f.pack(pady=8)
        self._dots = []
        for i in range(len(STEPS)):
            d = tk.Label(dots_f, text="●", font=("Segoe UI", 10),
                         bg=T.BG_BASE, fg=T.TEXT3)
            d.pack(side="left", padx=4)
            self._dots.append(d)

        # Buttons
        btn_f = tk.Frame(self._win, bg=T.BG_BASE, pady=16)
        btn_f.pack(side="bottom")
        self._btn_prev = tk.Button(btn_f, text="← Back",
                                    font=("Segoe UI", 11, "bold"),
                                    bg=T.BG_CARD2, fg=T.TEXT,
                                    relief="flat", padx=20, pady=8,
                                    cursor="hand2",
                                    command=self._prev)
        self._btn_prev.pack(side="left", padx=8)
        self._btn_next = tk.Button(btn_f, text="Next →",
                                    font=("Segoe UI", 11, "bold"),
                                    bg=T.ACCENT, fg="#000",
                                    relief="flat", padx=20, pady=8,
                                    cursor="hand2",
                                    command=self._next)
        self._btn_next.pack(side="left", padx=8)

        self._refresh()

    def _refresh(self):
        T    = self.T
        step = STEPS[self._step]
        self._lbl_icon.config(text=step["icon"])
        self._lbl_title.config(text=step["title"])
        self._lbl_body.config(text=step["body"])

        for i, dot in enumerate(self._dots):
            dot.config(fg=T.ACCENT if i == self._step else T.TEXT3)

        last = self._step == len(STEPS) - 1
        self._btn_next.config(text="🚀 Get Started" if last else "Next →",
                               bg=T.ACCENT if last else T.ACCENT)
        self._btn_prev.config(state="disabled" if self._step == 0 else "normal")

    def _next(self):
        if self._step < len(STEPS) - 1:
            self._step += 1
            self._refresh()
        else:
            self._win.destroy()
            self.on_done()

    def _prev(self):
        if self._step > 0:
            self._step -= 1
            self._refresh()
