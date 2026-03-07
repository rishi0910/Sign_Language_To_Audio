"""
core/gesture_handler.py
Loads the AI model, runs predictions, feeds results into
WordBuilder / SentenceManager / TTS / OBS.
"""

import os
import time
import numpy as np
from typing import Optional, Callable

from core.frame_processor  import FrameProcessor
from core.word_builder     import WordBuilder
from core.sentence_manager import SentenceManager
from core.tts_controller   import TTSController
from core.obs_bridge       import OBSBridge


class GestureHandler:
    FRAME_THRESHOLD = 15
    REPEAT_DELAY    = 2.0   # seconds before same gesture repeats
    CONFIDENCE_MIN  = 0.80

    def __init__(self, base_path: str,
                 word_builder:  WordBuilder,
                 sentence_mgr:  SentenceManager,
                 tts:           TTSController,
                 obs:           OBSBridge):
        self.base_path    = base_path
        self.word_builder = word_builder
        self.sentence_mgr = sentence_mgr
        self.tts          = tts
        self.obs          = obs

        self.model        = None
        self.idx_to_label = {}
        self.model_loaded = False

        self.processor      = FrameProcessor()
        self._pred_buffer   = []
        self._prev_pred     = ""
        self._last_pred_time= 0.0
        self.confidence_threshold = self.CONFIDENCE_MIN

        # UI callbacks
        self.on_prediction: Optional[Callable] = None  # (label, confidence)
        self.on_word_added:  Optional[Callable] = None  # (word)

        self._load_model()

    # ── MODEL LOADING ────────────────────────────────────────────
    def _load_model(self):
        model_file = os.path.join(self.base_path, "model", "sign_model.h5")
        label_file = os.path.join(self.base_path, "model", "label_map.npy")

        if not os.path.exists(model_file) or not os.path.exists(label_file):
            print(f"[GestureHandler] ⚠  Model files not found — running in DEMO mode")
            self._setup_demo_mode()
            return

        try:
            from tensorflow.keras.models import load_model
            self.model = load_model(model_file)
            label_map  = np.load(label_file, allow_pickle=True).item()
            self.idx_to_label = {v: k for k, v in label_map.items()}
            self.model_loaded = True
            print("[GestureHandler] ✅ Model loaded successfully")
        except Exception as e:
            print(f"[GestureHandler] ❌ Model load error: {e} — falling back to DEMO mode")
            self._setup_demo_mode()

    def _setup_demo_mode(self):
        """Fake model for testing without real weights."""
        import random
        letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["space", "del", "nothing"]
        self.idx_to_label = {i: l for i, l in enumerate(letters)}
        self.model = None
        self.model_loaded = False   # still False but we handle it below
        self._demo_mode = True
        self._demo_labels = letters
        print("[GestureHandler] 🎮 DEMO mode active — random predictions")

    # ── FRAME PROCESSING ────────────────────────────────────────
    def process_frame(self, frame_bgr):
        """Called by CameraManager for every captured frame.
        Returns annotated frame."""
        roi_input, annotated, _ = self.processor.process(frame_bgr)

        label      = "No hand"
        confidence = 0.0

        if roi_input is not None:
            label, confidence = self._predict(roi_input)
            if confidence >= self.confidence_threshold:
                self._handle_confirmed(label, confidence)

        if self.on_prediction:
            self.on_prediction(label, confidence)

        return annotated

    def _predict(self, roi_input):
        # Demo mode: return random letter with fake confidence
        if getattr(self, "_demo_mode", False):
            import random, time
            label = random.choice(self._demo_labels[:26])  # only letters in demo
            conf  = round(random.uniform(0.70, 0.99), 3)
            return label, conf

        pred       = self.model.predict(roi_input, verbose=0)
        confidence = float(np.max(pred))
        label      = self.idx_to_label[int(np.argmax(pred))]
        return label, confidence

    def _handle_confirmed(self, label: str, confidence: float):
        """Stable gesture confirmation via buffer + timing."""
        self._pred_buffer.append(label)
        if len(self._pred_buffer) > self.FRAME_THRESHOLD:
            self._pred_buffer.pop(0)

        majority = self._pred_buffer.count(label) / len(self._pred_buffer)
        if majority < 0.80:
            return

        now = time.time()
        same_as_prev = (label == self._prev_pred)
        if same_as_prev and (now - self._last_pred_time) < self.REPEAT_DELAY:
            return

        self._prev_pred      = label
        self._last_pred_time = now
        self._dispatch(label)

    def _dispatch(self, label: str):
        word = self.word_builder.push(label)
        if word:
            self.sentence_mgr.add_word(word)
            self.obs.update_caption(self.sentence_mgr.current_sentence)
            if self.on_word_added:
                self.on_word_added(word)

    # ── SETTINGS ────────────────────────────────────────────────
    def set_confidence_threshold(self, value: float):
        self.confidence_threshold = value

    def release(self):
        self.processor.release()
