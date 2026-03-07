"""tests/test_tts_controller.py"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tts_controller import TTSController


def test_queue_no_crash():
    tts = TTSController()
    tts.speak("Hello world")      # should not raise
    time.sleep(0.1)
    print("✅ test_queue_no_crash passed")

def test_set_speed():
    tts = TTSController()
    tts.set_speed(1.5)
    assert tts.speed == 1.5
    tts.set_speed(99)   # clamp to 2.0
    assert tts.speed == 2.0
    print("✅ test_set_speed passed")

def test_set_volume():
    tts = TTSController()
    tts.set_volume(0.5)
    assert tts.volume == 0.5
    tts.set_volume(-1)  # clamp to 0.0
    assert tts.volume == 0.0
    print("✅ test_set_volume passed")


if __name__ == "__main__":
    test_queue_no_crash()
    test_set_speed()
    test_set_volume()
    print("\n🎉 All TTS tests passed!")
