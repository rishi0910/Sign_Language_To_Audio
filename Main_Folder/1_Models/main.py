import cv2
import threading
import mediapipe as mp
import numpy as np
import joblib
import pyttsx3
from collections import Counter
# Importing your custom math logic
from sign_utils import normalize_landmarks

# --- 1. GLOBAL INITIALIZATION (PERSISTENT CONNECTION) ---
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine_lock = threading.Lock() 

# 2. Load the 'Brain' and 'Dictionary'
try:
    model = joblib.load('model_v132.joblib')
    label_encoder = joblib.load('label_encoder_v132.joblib')
    print("✓ [STATUS] SignBridge Brain (v132) Loaded Successfully!")
except Exception as e:
    print(f"❌ [CRITICAL ERROR] Failed to load models: {e}")
    exit()

# 3. MediaPipe Configuration
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False, 
    max_num_hands=1, 
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# 4. State Variables
sentence = ""
prediction_buffer = [] 
BUFFER_SIZE = 20        

cap = cv2.VideoCapture(0)
print("\n--- SignBridge LIVE INITIALIZED ---")
print("Instructions: Press 'Space' gesture to speak. Press 'q' to exit.\n")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    H, W, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    current_pred = "No Hand Detected"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # --- 5. MATH LOGIC CALL (Clean & Modular) ---
            # Using the function from your sign_utils.py file
            landmarks = normalize_landmarks(hand_landmarks)

            # 6. Prediction Engine
            prediction = model.predict([landmarks])
            current_pred = label_encoder.inverse_transform(prediction)[0]

            # 7. Stability Logic
            prediction_buffer.append(current_pred)
            if len(prediction_buffer) > BUFFER_SIZE:
                prediction_buffer.pop(0)

            most_common = Counter(prediction_buffer).most_common(1)[0]
            if most_common[1] >= 15:
                stable_char = most_common[0]

                # --- GLOBAL THREADED ENGINE CALL ---
                if stable_char.lower() == 'space':
                    if sentence.strip() != "":
                        print(f"🔊 Speaking: {sentence}")
                        
                        def speak_task(text_to_say):
                            with engine_lock:
                                try:
                                    engine.say(text_to_say)
                                    engine.runAndWait()
                                except Exception as e:
                                    print(f"Audio Error: {e}")

                        threading.Thread(target=speak_task, args=(sentence,), daemon=True).start()
                        
                        sentence = "" 
                        prediction_buffer = []
                
                elif stable_char.lower() in ['nothing', 'none']:
                    pass 
                
                else:
                    if not sentence or sentence[-1] != stable_char:
                        sentence += stable_char

    # 8. UI Overlay
    cv2.rectangle(frame, (0, 0), (W, 90), (45, 45, 45), -1) 
    cv2.putText(frame, f"SIGN: {current_pred}", (15, 35), 
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, f"TEXT: {sentence}", (15, 75), 
                cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2)

    cv2.imshow('SignBridge Final Demo', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()