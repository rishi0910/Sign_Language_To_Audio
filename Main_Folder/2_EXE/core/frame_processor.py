"""
core/frame_processor.py
Preprocessing utilities: extract hand ROI, normalise for model input.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, Tuple


class FrameProcessor:
    """Wraps MediaPipe hand detection and ROI extraction."""

    IMG_SIZE = 64

    def __init__(self):
        mp_hands = mp.solutions.hands
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.70,
            min_tracking_confidence=0.70,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_hands = mp_hands

    # ── PUBLIC ──────────────────────────────────────────────────
    def process(self, frame_bgr: np.ndarray) -> Tuple[Optional[np.ndarray],
                                                       Optional[np.ndarray],
                                                       Optional[object]]:
        """
        Returns:
            roi_input   – (1, 64, 64, 1) float32 ready for model.predict()
            annotated   – frame with landmarks + bounding box drawn
            landmarks   – raw mediapipe hand_landmarks (or None)
        """
        h, w, _ = frame_bgr.shape
        rgb      = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result   = self.hands.process(rgb)
        annotated = frame_bgr.copy()
        roi_input  = None
        landmarks  = None

        if result.multi_hand_landmarks:
            for hand_lm in result.multi_hand_landmarks:
                landmarks = hand_lm

                # Draw skeleton
                self.mp_draw.draw_landmarks(
                    annotated, hand_lm,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=(0, 255, 160), thickness=2, circle_radius=3),
                    self.mp_draw.DrawingSpec(color=(80, 200, 255), thickness=2),
                )

                # Bounding box with padding
                xs = [lm.x for lm in hand_lm.landmark]
                ys = [lm.y for lm in hand_lm.landmark]
                pad = 30
                x1 = max(int(min(xs) * w) - pad, 0)
                x2 = min(int(max(xs) * w) + pad, w)
                y1 = max(int(min(ys) * h) - pad, 0)
                y2 = min(int(max(ys) * h) + pad, h)

                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 230, 140), 2)

                roi = frame_bgr[y1:y2, x1:x2]
                if roi.size > 0:
                    gray      = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    resized   = cv2.resize(gray, (self.IMG_SIZE, self.IMG_SIZE))
                    normed    = resized / 255.0
                    roi_input = normed.reshape(1, self.IMG_SIZE, self.IMG_SIZE, 1).astype(np.float32)
                break  # one hand only

        return roi_input, annotated, landmarks

    def release(self):
        self.hands.close()
