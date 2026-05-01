"""
core/hotkey_manager.py
Global keyboard shortcuts.
"""

from typing import Optional


class HotkeyManager:
    def __init__(self, camera_mgr, tts, sentence_mgr):
        self.camera_mgr   = camera_mgr
        self.tts          = tts
        self.sentence_mgr = sentence_mgr
        self._hotkeys: dict = {}
        self._active = False

    # ── TKINTER BINDINGS (called by MainWindow) ──────────────────
    def register_tkinter(self, root):
        """Bind keyboard shortcuts to a Tkinter root window."""
        root.bind("<F5>",    lambda e: self._on_f5())
        root.bind("<Escape>",lambda e: self._on_escape())
        root.bind("<F1>",    lambda e: self._on_f1())
        root.bind("<Control-s>", lambda e: self._on_ctrl_s())
        root.bind("<Control-n>", lambda e: self._on_ctrl_n())
        root.bind("<Return>",    lambda e: self._on_enter())
        print("[Hotkeys] Tkinter shortcuts registered")

    # ── HANDLERS ────────────────────────────────────────────────
    def _on_f5(self):
        if not self.camera_mgr.is_running:
            self.camera_mgr.start()

    def _on_escape(self):
        if self.camera_mgr.is_running:
            self.camera_mgr.stop()

    def _on_f1(self):
        pass   # UI handles showing help dialog

    def _on_ctrl_s(self):
        pass   # UI handles save

    def _on_ctrl_n(self):
        self.sentence_mgr.clear()

    def _on_enter(self):
        sentence = self.sentence_mgr.current_sentence
        if sentence:
            self.tts.speak(sentence)
