"""tests/test_word_builder.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.word_builder import WordBuilder


def test_basic_word():
    wb = WordBuilder()
    wb.push("H"); wb.push("I")
    result = wb.push("space")
    assert result == "HI", f"Expected 'HI', got '{result}'"
    print("✅ test_basic_word passed")

def test_delete():
    wb = WordBuilder()
    wb.push("H"); wb.push("E"); wb.push("del")
    assert wb.partial == "H", f"Expected 'H', got '{wb.partial}'"
    print("✅ test_delete passed")

def test_nothing_adds_period():
    wb = WordBuilder()
    wb.push("H"); wb.push("I")
    result = wb.push("nothing")
    assert result == "HI.", f"Expected 'HI.', got '{result}'"
    print("✅ test_nothing_adds_period passed")

def test_empty_space_returns_none():
    wb = WordBuilder()
    result = wb.push("space")
    assert result is None
    print("✅ test_empty_space_returns_none passed")

def test_partial_updates():
    updates = []
    wb = WordBuilder()
    wb.on_char_update = lambda p: updates.append(p)
    wb.push("A"); wb.push("B")
    assert updates == ["A", "AB"]
    print("✅ test_partial_updates passed")


if __name__ == "__main__":
    test_basic_word()
    test_delete()
    test_nothing_adds_period()
    test_empty_space_returns_none()
    test_partial_updates()
    print("\n🎉 All word_builder tests passed!")
