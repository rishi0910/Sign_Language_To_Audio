"""
ui/tray_icon.py
System tray icon using pystray.
Gives quick access to Start/Stop/Quit from the taskbar.
"""

import threading
from typing import Optional


class TrayIcon:
    def __init__(self, camera_mgr, on_quit):
        self.camera_mgr = camera_mgr
        self.on_quit    = on_quit
        self._icon      = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._icon:
            self._icon.stop()

    def _run(self):
        try:
            import pystray
            from PIL import Image, ImageDraw

            # Draw a simple hand-emoji-like icon
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([8, 8, 56, 56], fill=(0, 214, 143))
            draw.text((16, 16), "🤟", fill=(0, 0, 0))

            menu = pystray.Menu(
                pystray.MenuItem("Start", lambda: self.camera_mgr.start()),
                pystray.MenuItem("Stop",  lambda: self.camera_mgr.stop()),
                pystray.MenuItem("Quit",  lambda: self.on_quit()),
            )
            self._icon = pystray.Icon("SignBridge Pro", img,
                                       "SignBridge Pro", menu)
            self._icon.run()
        except ImportError:
            print("[Tray] pystray not installed — tray icon disabled")
        except Exception as e:
            print(f"[Tray] Error: {e}")
