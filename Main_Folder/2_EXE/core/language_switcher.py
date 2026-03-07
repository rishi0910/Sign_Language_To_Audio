"""
core/language_switcher.py
Manages UI language (English / Hindi) and sign language mode (ASL / ISL).
Stores string maps so the UI can query translated labels.
"""

from typing import Callable, Optional


UI_STRINGS = {
    "en": {
        "app_title":        "SignBridge Pro",
        "tagline":          "Real-time AI Sign Language Translation",
        "start":            "▶  Start Translation",
        "stop":             "■  Stop",
        "speak_now":        "🔊  Speak Now",
        "clear":            "🗑  Clear",
        "save":             "💾  Save",
        "copy":             "📋  Copy",
        "settings":         "⚙️  Settings",
        "history":          "📚  History",
        "meeting_mode":     "📺  Meeting Mode",
        "nav_live":         "Live Translate",
        "nav_meeting":      "Meeting Mode",
        "nav_voice":        "Voice Studio",
        "nav_history":      "History",
        "nav_guide":        "Gesture Guide",
        "nav_settings":     "Settings",
        "nav_analytics":    "Analytics",
        "cam_inactive":     "Camera Inactive",
        "cam_active":       "Camera Active",
        "confidence":       "Confidence",
        "hold_confirm":     "Hold to confirm",
        "no_gesture":       "No gesture",
        "translation":      "Real-time Translation",
        "words":            "Words",
        "chars":            "Chars",
        "voice_engine":     "Voice Engine",
        "speed":            "Speed",
        "volume":           "Volume",
        "obs_connect":      "Connect to OBS",
        "status_system":    "System Status",
    },
    "hi": {
        "app_title":        "साइनब्रिज प्रो",
        "tagline":          "रियल-टाइम AI सांकेतिक भाषा अनुवाद",
        "start":            "▶  अनुवाद शुरू करें",
        "stop":             "■  रोकें",
        "speak_now":        "🔊  अभी बोलें",
        "clear":            "🗑  साफ करें",
        "save":             "💾  सहेजें",
        "copy":             "📋  कॉपी",
        "settings":         "⚙️  सेटिंग्स",
        "history":          "📚  इतिहास",
        "meeting_mode":     "📺  मीटिंग मोड",
        "nav_live":         "लाइव अनुवाद",
        "nav_meeting":      "मीटिंग मोड",
        "nav_voice":        "वॉइस स्टूडियो",
        "nav_history":      "इतिहास",
        "nav_guide":        "जेस्चर गाइड",
        "nav_settings":     "सेटिंग्स",
        "nav_analytics":    "विश्लेषण",
        "cam_inactive":     "कैमरा बंद",
        "cam_active":       "कैमरा चालू",
        "confidence":       "विश्वास",
        "hold_confirm":     "पुष्टि के लिए रोकें",
        "no_gesture":       "कोई जेस्चर नहीं",
        "translation":      "रियल-टाइम अनुवाद",
        "words":            "शब्द",
        "chars":            "अक्षर",
        "voice_engine":     "वॉइस इंजन",
        "speed":            "गति",
        "volume":           "आवाज़",
        "obs_connect":      "OBS से जोड़ें",
        "status_system":    "सिस्टम स्थिति",
    },
}

SIGN_MODES = ["ASL", "ISL"]


class LanguageSwitcher:
    def __init__(self, default: str = "en"):
        self._lang = default if default in UI_STRINGS else "en"
        self._sign_mode = "ASL"
        self.on_change: Optional[Callable] = None  # () -> None

    # ── UI LANGUAGE ──────────────────────────────────────────────
    def set_lang(self, lang: str):
        if lang in UI_STRINGS:
            self._lang = lang
            if self.on_change:
                self.on_change()

    def toggle(self):
        self.set_lang("hi" if self._lang == "en" else "en")

    def t(self, key: str) -> str:
        """Translate a key to the current language."""
        return UI_STRINGS[self._lang].get(key, key)

    @property
    def lang(self) -> str:
        return self._lang

    # ── SIGN MODE ────────────────────────────────────────────────
    def set_sign_mode(self, mode: str):
        if mode in SIGN_MODES:
            self._sign_mode = mode
            if self.on_change:
                self.on_change()

    @property
    def sign_mode(self) -> str:
        return self._sign_mode
