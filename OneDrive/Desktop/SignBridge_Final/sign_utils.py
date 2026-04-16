import numpy as np

def normalize_landmarks(hand_landmarks):
    """
    Standardizes hand landmarks to be wrist-relative.
    This logic must be identical for Training, main.py, and Website.
    """
    base_x = hand_landmarks.landmark[0].x
    base_y = hand_landmarks.landmark[0].y
    base_z = hand_landmarks.landmark[0].z

    landmarks = []
    for lm in hand_landmarks.landmark:
        landmarks.extend([lm.x - base_x, lm.y - base_y, lm.z - base_z])
    
    return landmarks