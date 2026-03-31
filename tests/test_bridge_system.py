"""Unit tests for host bridge system."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from src.adapters.bridge_factory import (
    get_bridges,
    get_capture_bridge,
    get_input_bridge,
    get_platform,
)
from src.adapters.bridge_interfaces import FrameCapture


class TestPlatformDetection(unittest.TestCase):
    """Tests for platform detection."""

    @patch("platform.system")
    def test_detect_macos(self, mock_system):
        """Test macOS detection."""
        mock_system.return_value = "Darwin"
        assert get_platform() == "macos"

    @patch("platform.system")
    def test_detect_windows(self, mock_system):
        """Test Windows detection."""
        mock_system.return_value = "Windows"
        assert get_platform() == "windows"

    @patch("platform.system")
    def test_detect_linux(self, mock_system):
        """Test Linux detection."""
        mock_system.return_value = "Linux"
        assert get_platform() == "linux"

    @patch("platform.system")
    def test_detect_unknown(self, mock_system):
        """Test unknown platform detection."""
        mock_system.return_value = "UnknownOS"
        assert get_platform() == "unknown"


class TestFrameCapture(unittest.TestCase):
    """Tests for FrameCapture data structure."""

    def test_frame_capture_creation(self):
        """Test creating a FrameCapture object."""
        frame_array = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame = FrameCapture(frame=frame_array, width=1280, height=720)

        assert frame.width == 1280
        assert frame.height == 720
        assert frame.frame.shape == (720, 1280, 3)

    def test_frame_capture_basic(self):
        """Test FrameCapture with different array types."""
        frame_array = np.ones((480, 640, 3), dtype=np.uint8) * 255
        frame = FrameCapture(frame=frame_array, width=640, height=480)

        assert frame.width == 640
        assert frame.height == 480
        assert frame.frame.mean() > 200


@patch("platform.system")
class TestBridgeFactory(unittest.TestCase):
    """Tests for bridge factory functions."""

    @patch("src.adapters.macos_capture_bridge.MacOSCaptureBridge")
    def test_get_capture_bridge_macos(self, mock_bridge, mock_system):
        """Test getting macOS capture bridge."""
        mock_system.return_value = "Darwin"
        capture = get_capture_bridge()
        assert capture is not None

    @patch("src.adapters.macos_input_bridge.MacOSInputBridge")
    def test_get_input_bridge_macos(self, mock_bridge, mock_system):
        """Test getting macOS input bridge."""
        mock_system.return_value = "Darwin"
        input_bridge = get_input_bridge()
        assert input_bridge is not None

    @patch("src.adapters.macos_capture_bridge.MacOSCaptureBridge")
    @patch("src.adapters.macos_input_bridge.MacOSInputBridge")
    def test_get_bridges_macos(self, mock_input, mock_capture, mock_system):
        """Test getting both bridges together."""
        mock_system.return_value = "Darwin"
        capture, input_bridge = get_bridges()
        assert capture is not None
        assert input_bridge is not None

    def test_unsupported_platform(self, mock_system):
        """Test error handling for unsupported platform."""
        mock_system.return_value = "UnknownOS"
        with self.assertRaises(NotImplementedError):
            get_capture_bridge()


class TestMacOSCaptureBridge(unittest.TestCase):
    """Tests for macOS capture bridge."""

    @patch("PIL.ImageGrab.grab")
    def test_capture_succeeds(self, mock_grab):
        """Test successful frame capture."""
        from src.adapters.macos_capture_bridge import MacOSCaptureBridge


class TestWindowsCaptureBridge(unittest.TestCase):
    """Tests for Windows capture bridge."""

    @patch("PIL.ImageGrab.grab")
    def test_capture_succeeds(self, mock_grab):
        """Test successful frame capture on Windows."""
        from src.adapters.windows_capture_bridge import WindowsCaptureBridge

        # Mock PIL ImageGrab to return a test image
        mock_image = MagicMock()
        mock_image.size = (1920, 1080)
        mock_grab.return_value = mock_image

        with patch("numpy.array", return_value=np.zeros((1080, 1920, 3), dtype=np.uint8)):
            bridge = WindowsCaptureBridge()
            result = bridge.capture()

            assert result.width == 1920
            assert result.height == 1080
            assert result.frame.shape == (1080, 1920, 3)

    @patch("PIL.ImageGrab.grab")
    def test_capture_failure(self, mock_grab):
        """Test capture error handling on Windows."""
        from src.adapters.windows_capture_bridge import WindowsCaptureBridge

        mock_grab.side_effect = Exception("Capture failed")

        bridge = WindowsCaptureBridge()
        with self.assertRaises(Exception):
            bridge.capture()


class TestWindowsInputBridge(unittest.TestCase):
    """Tests for Windows input bridge."""

    @patch("src.adapters.windows_input_bridge.MouseController")
    @patch("src.adapters.windows_input_bridge.KeyboardController")
    def test_press_single_char(self, mock_kb_class, mock_mouse_class):
        """Test pressing a single character key on Windows."""
        from src.adapters.windows_input_bridge import WindowsInputBridge

        mock_kb = MagicMock()
        mock_kb_class.return_value = mock_kb
        mock_mouse_class.return_value = MagicMock()

        bridge = WindowsInputBridge()
        bridge.press("a")

        mock_kb.press.assert_called_once()

    @patch("src.adapters.windows_input_bridge.MouseController")
    @patch("src.adapters.windows_input_bridge.KeyboardController")
    def test_press_special_key(self, mock_kb_class, mock_mouse_class):
        """Test pressing a special key on Windows."""
        from src.adapters.windows_input_bridge import WindowsInputBridge

        mock_kb = MagicMock()
        mock_kb_class.return_value = mock_kb
        mock_mouse_class.return_value = MagicMock()

        bridge = WindowsInputBridge()
        bridge.press("enter")

        mock_kb.press.assert_called_once()

    @patch("src.adapters.windows_input_bridge.KeyboardController")
    @patch("src.adapters.windows_input_bridge.MouseController")
    def test_click(self, mock_mouse_class, mock_kb_class):
        """Test mouse click on Windows."""
        from src.adapters.windows_input_bridge import WindowsInputBridge

        mock_mouse = MagicMock()
        mock_mouse_class.return_value = mock_mouse
        mock_kb_class.return_value = MagicMock()

        bridge = WindowsInputBridge()
        bridge.click(100, 200, button="left")

        # Check that mouse click was called
        mock_mouse.click.assert_called_once()

    @patch("src.adapters.windows_input_bridge.MouseController")
    @patch("src.adapters.windows_input_bridge.KeyboardController")
    def test_type_text(self, mock_kb_class, mock_mouse_class):
        """Test typing text on Windows."""
        from src.adapters.windows_input_bridge import WindowsInputBridge

        mock_kb = MagicMock()
        mock_kb_class.return_value = mock_kb
        mock_mouse_class.return_value = MagicMock()

        bridge = WindowsInputBridge()
        bridge.type_text("hello")

        # Should call type for each character (5 times for "hello")
        assert mock_kb.type.call_count == 5


class TestMacOSInputBridge(unittest.TestCase):
    """Tests for macOS input bridge."""

    @patch("src.adapters.macos_input_bridge.MouseController")
    @patch("src.adapters.macos_input_bridge.KeyboardController")
    def test_press_single_char(self, mock_kb_class, mock_mouse_class):
        """Test pressing a single character key."""
        from src.adapters.macos_input_bridge import MacOSInputBridge

        mock_kb = MagicMock()
        mock_kb_class.return_value = mock_kb
        mock_mouse_class.return_value = MagicMock()

        bridge = MacOSInputBridge()
        bridge.press("a")

        mock_kb.press.assert_called_once()
        mock_kb.release.assert_called_once()

    @patch("src.adapters.macos_input_bridge.MouseController")
    @patch("src.adapters.macos_input_bridge.KeyboardController")
    def test_press_special_key(self, mock_kb_class, mock_mouse_class):
        """Test pressing a special key."""
        from src.adapters.macos_input_bridge import MacOSInputBridge

        mock_kb = MagicMock()
        mock_kb_class.return_value = mock_kb
        mock_mouse_class.return_value = MagicMock()

        bridge = MacOSInputBridge()
        bridge.press("space")

        mock_kb.press.assert_called_once()
        mock_kb.release.assert_called_once()

    @patch("src.adapters.macos_input_bridge.KeyboardController")
    @patch("src.adapters.macos_input_bridge.MouseController")
    def test_click(self, mock_mouse_class, mock_kb_class):
        """Test mouse click."""
        from src.adapters.macos_input_bridge import MacOSInputBridge

        mock_mouse = MagicMock()
        mock_mouse_class.return_value = mock_mouse
        mock_kb_class.return_value = MagicMock()

        bridge = MacOSInputBridge()
        bridge.click(100, 200, button="left")

        # Check that mouse click was called
        mock_mouse.click.assert_called_once()

    @patch("src.adapters.macos_input_bridge.MouseController")
    @patch("src.adapters.macos_input_bridge.KeyboardController")
    def test_type_text(self, mock_kb_class, mock_mouse_class):
        """Test typing text."""
        from src.adapters.macos_input_bridge import MacOSInputBridge

        mock_kb = MagicMock()
        mock_kb_class.return_value = mock_kb
        mock_mouse_class.return_value = MagicMock()

        bridge = MacOSInputBridge()
        bridge.type_text("hello")

        # Should call type for each character (5 times for "hello")
        assert mock_kb.type.call_count == 5


class TestBridgeIntegration(unittest.TestCase):
    """Integration tests for bridge system."""

    @patch("platform.system")
    def test_full_workflow_mock(self, mock_system):
        """Test full workflow with mocks."""
        mock_system.return_value = "Darwin"

        with patch("PIL.ImageGrab.grab") as mock_grab, patch(
            "pynput.keyboard.Controller"
        ) as mock_kb_class, patch("pynput.mouse.Controller") as mock_mouse_class:

            # Setup mocks
            mock_image = MagicMock()
            mock_grab.return_value = mock_image

            with patch("numpy.array", return_value=np.zeros((720, 1280, 3), dtype=np.uint8)):
                capture, input_bridge = get_bridges()

                # Capture
                frame = capture.capture()
                assert frame is not None

                # Input (would normally interact with UI)
                # input_bridge.click(100, 100)


if __name__ == "__main__":
    unittest.main()
