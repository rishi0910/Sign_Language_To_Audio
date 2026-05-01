"""
core/tts_controller.py
Text-to-speech with pluggable engines.
Supported: pyttsx3 (offline), gTTS (online), edge-tts (online, high quality).
"""

import threading
import queue
from typing import Optional


class TTSController:
    ENGINES = ["pyttsx3", "gtts", "edge_tts", "coqui"]

    def __init__(self):
        self.engine_name = "pyttsx3"
        self.speed   = 1.0   # 0.5 – 2.0
        self.volume  = 0.8   # 0.0 – 1.0
        self.pitch   = 1.0
        self._queue  = queue.Queue()
        self._engine = None
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        self._init_engine()

    # ── PUBLIC ──────────────────────────────────────────────────
    def speak(self, text: str):
        if text.strip():
            self._queue.put(text.strip())

    def set_engine(self, name: str):
        self.engine_name = name
        self._init_engine()

    def set_speed(self, value: float):
        self.speed = max(0.5, min(2.0, value))
        self._apply_settings()

    def set_volume(self, value: float):
        self.volume = max(0.0, min(1.0, value))
        self._apply_settings()

    # ── PRIVATE ─────────────────────────────────────────────────
    def _init_engine(self):
        try:
            if self.engine_name == "pyttsx3":
                import pyttsx3
                self._engine = pyttsx3.init()
                self._apply_settings()
                print(f"[TTS] pyttsx3 engine initialised")
            else:
                self._engine = None   # lazy-init for online engines
                print(f"[TTS] Engine set to {self.engine_name} (lazy init)")
        except Exception as e:
            print(f"[TTS] Engine init failed ({self.engine_name}): {e}")
            self._engine = None

    def _apply_settings(self):
        if self._engine and self.engine_name == "pyttsx3":
            try:
                rate = int(150 * self.speed)
                self._engine.setProperty("rate",   rate)
                self._engine.setProperty("volume", self.volume)
            except Exception:
                pass

    def _worker(self):
        while True:
            text = self._queue.get()
            try:
                self._speak_now(text)
            except Exception as e:
                print(f"[TTS] Speak error: {e}")

    def _speak_now(self, text: str):
        if self.engine_name == "pyttsx3" and self._engine:
            self._engine.say(text)
            self._engine.runAndWait()

        elif self.engine_name == "gtts":
            from gtts import gTTS
            import tempfile, os, playsound
            tts = gTTS(text=text, lang="en")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                tts.save(f.name)
                playsound.playsound(f.name)
                os.unlink(f.name)

        elif self.engine_name == "edge_tts":
            import asyncio, tempfile, os, playsound, edge_tts as et
            async def _run():
                communicate = et.Communicate(text, "en-US-JennyNeural")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                    await communicate.save(f.name)
                    return f.name
            path = asyncio.run(_run())
            playsound.playsound(path)
            os.unlink(path)

        else:
            print(f"[TTS] No engine available for: {text}")
