"""
core/camera.py
Handles webcam capture in a background thread.
Calls gesture_handler.process_frame() for every frame.
"""

import cv2
import threading
import time
from typing import Optional, Callable


class CameraManager:
    def __init__(self, gesture_handler):
        self.gesture_handler = gesture_handler
        self.cap: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.camera_index = 0
        self.fps_target = 30
        self.current_fps = 0.0

        # Callbacks the UI can hook into
        self.on_frame: Optional[Callable] = None      # (frame_bgr) -> None
        self.on_fps_update: Optional[Callable] = None # (fps: float) -> None
        self.on_error: Optional[Callable] = None      # (msg: str) -> None
        self.on_stopped: Optional[Callable] = None    # () -> None

    # ── PUBLIC ──────────────────────────────────────────────────
    def start(self, camera_index: int = 0) -> bool:
        if self._running:
            return True
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            if self.on_error:
                self.on_error(f"Cannot open camera (index {camera_index}). "
                              "Check camera permissions or try a different index.")
            return False

        # Request HD
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS,          30)

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        print(f"[Camera] Started on index {camera_index}")
        return True

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        print("[Camera] Stopped")
        if self.on_stopped:
            self.on_stopped()

    @property
    def is_running(self) -> bool:
        return self._running

    # ── PRIVATE ─────────────────────────────────────────────────
    def _capture_loop(self):
        fps_counter = 0
        fps_timer   = time.time()

        while self._running:
            ret, frame = self.cap.read()
            if not ret:
                if self.on_error:
                    self.on_error("Camera read failed — frame dropped.")
                break

            # Pass frame to gesture handler
            annotated = self.gesture_handler.process_frame(frame)

            # Deliver annotated frame to UI
            if self.on_frame and annotated is not None:
                self.on_frame(annotated)

            # FPS tracking
            fps_counter += 1
            elapsed = time.time() - fps_timer
            if elapsed >= 1.0:
                self.current_fps = fps_counter / elapsed
                fps_counter = 0
                fps_timer   = time.time()
                if self.on_fps_update:
                    self.on_fps_update(self.current_fps)

        self._running = False
        if self.cap:
            self.cap.release()
        if self.on_stopped:
            self.on_stopped()
