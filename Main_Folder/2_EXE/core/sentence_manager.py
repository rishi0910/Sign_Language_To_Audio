"""
core/sentence_manager.py
Manages the growing translated sentence.
Keeps history of past sentences for the session.
"""

from datetime import datetime
from typing import Optional, Callable


class SentenceManager:
    MAX_HISTORY = 200

    def __init__(self):
        self._words:   list[str] = []
        self._history: list[dict] = []
        self.on_update: Optional[Callable] = None   # (sentence: str)

    # ── PUBLIC ──────────────────────────────────────────────────
    def add_word(self, word: str):
        self._words.append(word)
        if self.on_update:
            self.on_update(self.current_sentence)

    @property
    def current_sentence(self) -> str:
        return " ".join(self._words)

    @property
    def word_count(self) -> int:
        return len(self._words)

    @property
    def char_count(self) -> int:
        return len(self.current_sentence)

    def commit_sentence(self):
        """Archive current sentence and start fresh."""
        if self._words:
            self._history.append({
                "text":       self.current_sentence,
                "timestamp":  datetime.now().strftime("%H:%M:%S"),
                "word_count": self.word_count,
            })
            if len(self._history) > self.MAX_HISTORY:
                self._history.pop(0)
            self._words.clear()
            if self.on_update:
                self.on_update("")

    def clear(self):
        self._words.clear()
        if self.on_update:
            self.on_update("")

    @property
    def history(self) -> list[dict]:
        return list(self._history)

    def export_text(self) -> str:
        lines = []
        for i, item in enumerate(self._history, 1):
            lines.append(f"[{item['timestamp']}]  {item['text']}")
        return "\n".join(lines)
