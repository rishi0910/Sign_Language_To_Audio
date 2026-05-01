# 🤟 SignBridge Pro — EXE Application

Real-time sign language → audio + text translator with OBS integration.

---

## 📁 Folder Structure

```
2_EXE_App/
├── core/               Business logic (camera, model, TTS, OBS, etc.)
├── ui/                 Tkinter UI windows and panels
├── config/             User settings (JSON)
├── assets/             Icons, sounds, fonts
├── model/              AI model files (place here)
├── logs/               Runtime logs
├── tests/              Unit tests + dummy model generator
├── installer/          PyInstaller spec + NSIS scripts
├── dist/               caption_output.txt written here (OBS reads it)
├── build/              PyInstaller working dir (gitignored)
└── main.py             Entry point
```

---

## 🚀 Quick Start (Development)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate dummy model (for testing without real weights)
python tests/mock_model.py

# 3. Run the app
python main.py
```

---

## 🧠 Adding the Real Model

Place these files in `model/`:
```
model/
├── sign_model.h5      ← Keras model (from teammate's 1_Models/ folder)
└── label_map.npy      ← {label: index} dict saved with np.save()
```

---

## 🏗️ Build EXE

```bash
cd installer
build_exe.bat
# Output: dist/SignBridgePro/SignBridgePro.exe
```

---

## 📺 OBS Integration

**Option A — Window Capture (easiest):**
1. Add Window Capture source in OBS → select this app window
2. Crop/resize as needed

**Option B — Text File (most reliable):**
1. Add Text (GDI+) source in OBS
2. Check "Read from file"
3. Point to `dist/caption_output.txt`

**Option C — WebSocket:**
Click "Connect to OBS" in the OBS panel (requires obs-websocket-py)

---

## ⌨️ Keyboard Shortcuts

| Key        | Action               |
|------------|----------------------|
| F5         | Start translation    |
| Escape     | Stop translation     |
| Enter      | Speak current text   |
| Ctrl+S     | Save translation     |
| Ctrl+N     | Clear                |
| F1         | Help / Instructions  |

---

## 🧪 Running Tests

```bash
python tests/test_word_builder.py
python tests/test_tts_controller.py
python tests/test_camera.py
```

---

## 🌐 Language Support

Switch between **English** and **हिंदी** from the startup splash or the top bar.
Sign language modes: **ASL** (American) and **ISL** (Indian).
