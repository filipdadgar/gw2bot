"""Example usage of the host bridge system."""

from src.adapters.bridge_factory import get_capture_bridge, get_input_bridge, get_bridges
import time


def example_1_basic_capture():
    """Example 1: Capture a frame and print info."""
    print("=" * 60)
    print("Example 1: Basic Frame Capture")
    print("=" * 60)
    
    capture = get_capture_bridge()
    frame_data = capture.capture()
    
    print(f"Captured frame: {frame_data.width}x{frame_data.height}")
    print(f"Frame type: {type(frame_data.frame)}")
    print(f"Frame shape: {frame_data.frame.shape}")
    print()


def example_2_input_automation():
    """Example 2: Send input commands."""
    print("=" * 60)
    print("Example 2: Input Automation")
    print("=" * 60)
    
    input_bridge = get_input_bridge()
    
    # Type text (uncomment to test)
    # input_bridge.type_text("Hello from gw2bot!")
    
    # Send key presses
    # input_bridge.press('space')
    # input_bridge.press('enter')
    
    # Click at position
    # input_bridge.click(x=100, y=100, button='left')
    
    print("Input commands prepared (commented out to avoid accidental execution)")
    print("Uncomment to test with your application")
    print()


def example_3_continuous_monitoring():
    """Example 3: Capture frames continuously."""
    print("=" * 60)
    print("Example 3: Continuous Monitoring (5 frames)")
    print("=" * 60)
    
    capture = get_capture_bridge()
    
    for i in range(5):
        frame_data = capture.capture()
        print(f"Frame {i+1}: {frame_data.width}x{frame_data.height} pixels")
        time.sleep(0.5)
    
    print()


def example_4_integrated_workflow():
    """Example 4: Integrated capture + input workflow."""
    print("=" * 60)
    print("Example 4: Integrated Workflow")
    print("=" * 60)
    
    # Get both bridges
    capture, input_bridge = get_bridges()
    
    # Capture initial state
    frame1 = capture.capture()
    print(f"Initial frame: {frame1.width}x{frame1.height}")
    
    # Simulate some action
    print("Sending input command...")
    # input_bridge.press('space')  # Uncomment to test
    
    # Capture result
    time.sleep(0.5)
    frame2 = capture.capture()
    print(f"After action: {frame2.width}x{frame2.height}")
    print()


def example_5_frame_processing():
    """Example 5: Process captured frame with OpenCV."""
    print("=" * 60)
    print("Example 5: Frame Processing")
    print("=" * 60)
    
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("OpenCV not installed. Install with: pip install opencv-python")
        return
    
    capture = get_capture_bridge()
    frame_data = capture.capture()
    
    # Convert RGB to BGR for OpenCV
    frame_bgr = cv2.cvtColor(frame_data.frame, cv2.COLOR_RGB2BGR)
    
    # Get grayscale
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    
    print(f"Original frame: {frame_data.frame.shape}")
    print(f"Grayscale frame: {gray.shape}")
    
    # Detect edges
    edges = cv2.Canny(gray, 100, 200)
    print(f"Edge detection: {edges.shape}")
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Found {len(contours)} contours")
    print()


def example_6_window_specific_capture():
    """Example 6: Attempt window-specific capture."""
    print("=" * 60)
    print("Example 6: Window-Specific Capture")
    print("=" * 60)
    
    # Try to capture specific window
    # Note: On macOS, this may fall back to full screen
    try:
        capture = get_capture_bridge(window_title="Guild Wars 2")
        frame = capture.capture()
        print(f"Captured window: {frame.width}x{frame.height}")
    except Exception as e:
        print(f"Window capture failed: {e}")
    
    print()


def example_7_performance_measurement():
    """Example 7: Measure performance."""
    print("=" * 60)
    print("Example 7: Performance Measurement")
    print("=" * 60)
    
    import time
    
    capture = get_capture_bridge()
    input_bridge = get_input_bridge()
    
    # Measure capture
    start = time.perf_counter()
    frame = capture.capture()
    capture_time = time.perf_counter() - start
    print(f"Capture time: {capture_time*1000:.2f}ms")
    
    # Measure click
    start = time.perf_counter()
    # input_bridge.click(100, 100)  # Uncomment to test
    click_time = time.perf_counter() - start
    print(f"Click time: {click_time*1000:.2f}ms")
    
    # Measure key press
    start = time.perf_counter()
    # input_bridge.press('space')  # Uncomment to test
    key_time = time.perf_counter() - start
    print(f"Key press time: {key_time*1000:.2f}ms")
    
    print()


if __name__ == "__main__":
    print("\nHost Bridge System - Usage Examples\n")
    
    examples = [
        ("Basic Capture", example_1_basic_capture),
        ("Input Automation", example_2_input_automation),
        ("Continuous Monitoring", example_3_continuous_monitoring),
        ("Integrated Workflow", example_4_integrated_workflow),
        ("Frame Processing", example_5_frame_processing),
        ("Window-Specific Capture", example_6_window_specific_capture),
        ("Performance Measurement", example_7_performance_measurement),
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"Example '{name}' failed: {e}\n")
    
    print("Examples completed!")
