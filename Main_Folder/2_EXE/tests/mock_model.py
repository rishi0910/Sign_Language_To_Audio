"""
tests/mock_model.py
Generates dummy model files (sign_model.h5 + label_map.npy)
so the EXE can be tested WITHOUT real training data.

Run:
    python tests/mock_model.py

It will create:
    model/sign_model.h5
    model/label_map.npy
"""

import os
import sys
import numpy as np

# Path bootstrap
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

MODEL_DIR = os.path.join(BASE, "model")
os.makedirs(MODEL_DIR, exist_ok=True)

# ── LABEL MAP ────────────────────────────────────────────────────
labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["space", "del", "nothing"]
label_map = {label: i for i, label in enumerate(labels)}
label_map_path = os.path.join(MODEL_DIR, "label_map.npy")
np.save(label_map_path, label_map)
print(f"✅ label_map.npy saved → {label_map_path}")
print(f"   Classes: {list(label_map.keys())}")

# ── DUMMY KERAS MODEL ────────────────────────────────────────────
try:
    import tensorflow as tf
    from tensorflow.keras import layers, models

    IMG_SIZE    = 64
    NUM_CLASSES = len(labels)

    model = models.Sequential([
        layers.Input(shape=(IMG_SIZE, IMG_SIZE, 1)),
        layers.Conv2D(16, (3, 3), activation="relu", padding="same"),
        layers.MaxPooling2D(),
        layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
        layers.MaxPooling2D(),
        layers.Flatten(),
        layers.Dense(64, activation="relu"),
        layers.Dense(NUM_CLASSES, activation="softmax"),
    ])

    model.compile(optimizer="adam",
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])

    # Quick dummy training so weights are non-zero
    X_dummy = np.random.rand(50, IMG_SIZE, IMG_SIZE, 1).astype(np.float32)
    y_dummy = np.random.randint(0, NUM_CLASSES, 50)
    model.fit(X_dummy, y_dummy, epochs=1, verbose=0)

    model_path = os.path.join(MODEL_DIR, "sign_model.h5")
    model.save(model_path)
    print(f"✅ sign_model.h5 saved → {model_path}")
    print(f"   Input: (1, {IMG_SIZE}, {IMG_SIZE}, 1)")
    print(f"   Output: {NUM_CLASSES} classes")
    print()
    print("⚠️  This is a DUMMY model — predictions are random.")
    print("   Replace with your trained model for real use.")

except ImportError:
    print("⚠️  TensorFlow not installed.")
    print("   Dummy .h5 not created.")
    print("   The app will run in DEMO mode (random predictions).")
except Exception as e:
    print(f"❌ Error creating dummy model: {e}")


if __name__ == "__main__":
    print("\nDone. Now run:  python main.py")
