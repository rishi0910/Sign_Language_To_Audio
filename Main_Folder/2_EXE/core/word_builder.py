"""
core/word_builder.py
Accumulates single-character gestures into words.
Special gestures: 'space' → commit word, 'del' → backspace, 'nothing' → period.
"""

from typing import Optional, Callable


class WordBuilder:
    SPECIAL = {"space", "del", "nothing"}

    def __init__(self):
        self._buffer: list[str] = []
        self.on_char_update: Optional[Callable] = None  # (current_partial: str)

    # ── PUBLIC ──────────────────────────────────────────────────
    def push(self, label: str) -> Optional[str]:
        """
        Feed a recognised gesture label.
        Returns a completed word string when the word is finalised,
        or None if still building.
        """
        label = label.strip().lower()

        if label == "del":
            if self._buffer:
                self._buffer.pop()
            self._notify()
            return None

        if label == "space":
            return self._commit(suffix="")

        if label == "nothing":
            return self._commit(suffix=".")

        # Regular letter
        self._buffer.append(label.upper())
        self._notify()
        return None

    def reset(self):
        self._buffer.clear()
        self._notify()

    @property
    def partial(self) -> str:
        return "".join(self._buffer)

    # ── PRIVATE ─────────────────────────────────────────────────
    def _commit(self, suffix: str) -> Optional[str]:
        if not self._buffer:
            return None
        word = "".join(self._buffer) + suffix
        self._buffer.clear()
        self._notify()
        return word

    def _notify(self):
        if self.on_char_update:
            self.on_char_update(self.partial)
