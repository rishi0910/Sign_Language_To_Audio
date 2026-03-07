"""tests/test_camera.py — tests CameraManager without a real webcam"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, patch
from core.camera import CameraManager


def test_start_fail_no_camera():
    mock_handler = MagicMock()
    cam = CameraManager(gesture_handler=mock_handler)
    errors = []
    cam.on_error = lambda msg: errors.append(msg)

    with patch("cv2.VideoCapture") as MockCap:
        instance = MockCap.return_value
        instance.isOpened.return_value = False
        result = cam.start(camera_index=99)

    assert result is False
    assert len(errors) == 1
    print("✅ test_start_fail_no_camera passed")

def test_stop_when_not_running():
    cam = CameraManager(gesture_handler=MagicMock())
    cam.stop()   # should not raise
    print("✅ test_stop_when_not_running passed")

def test_is_running_default_false():
    cam = CameraManager(gesture_handler=MagicMock())
    assert cam.is_running is False
    print("✅ test_is_running_default_false passed")


if __name__ == "__main__":
    test_start_fail_no_camera()
    test_stop_when_not_running()
    test_is_running_default_false()
    print("\n🎉 All camera tests passed!")
