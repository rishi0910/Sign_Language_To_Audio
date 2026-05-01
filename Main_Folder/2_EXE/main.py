"""
SignBridge Pro v2.0 — Main Entry Point
Real-time Sign Language to Voice & Text Translator
"""

import sys
import os

# ── PATH BOOTSTRAP ──────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_PATH)

# ── IMPORTS ─────────────────────────────────────────────────────
import tkinter as tk
from tkinter import messagebox
import threading
from datetime import datetime

from core.camera          import CameraManager
from core.gesture_handler import GestureHandler
from core.word_builder    import WordBuilder
from core.sentence_manager import SentenceManager
from core.tts_controller  import TTSController
from core.obs_bridge      import OBSBridge
from core.hotkey_manager  import HotkeyManager
from core.language_switcher import LanguageSwitcher
from ui.main_window       import MainWindow
from ui.theme             import Theme

# ── STARTUP ─────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  🤟  SignBridge Pro v2.0  —  Starting Up")
    print("=" * 55)
    print(f"  Base path : {BASE_PATH}")
    print(f"  Time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    # Build the component graph
    theme            = Theme()
    lang_switcher    = LanguageSwitcher(default="en")
    word_builder     = WordBuilder()
    sentence_mgr     = SentenceManager()
    tts              = TTSController()
    obs              = OBSBridge(base_path=BASE_PATH)
    gesture_handler  = GestureHandler(base_path=BASE_PATH,
                                      word_builder=word_builder,
                                      sentence_mgr=sentence_mgr,
                                      tts=tts,
                                      obs=obs)
    camera_mgr       = CameraManager(gesture_handler=gesture_handler)
    hotkeys          = HotkeyManager(camera_mgr=camera_mgr,
                                     tts=tts,
                                     sentence_mgr=sentence_mgr)

    # Create and run main window
    app = MainWindow(
        base_path      = BASE_PATH,
        camera_mgr     = camera_mgr,
        gesture_handler= gesture_handler,
        word_builder   = word_builder,
        sentence_mgr   = sentence_mgr,
        tts            = tts,
        obs            = obs,
        hotkeys        = hotkeys,
        lang_switcher  = lang_switcher,
        theme          = theme,
    )
    app.run()


if __name__ == "__main__":
    main()
