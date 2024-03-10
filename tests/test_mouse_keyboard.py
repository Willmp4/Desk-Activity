import unittest
from unittest.mock import Mock, patch
import sys
sys.path.append('..')
from activity_monitor import ActivityMonitor
from pynput.keyboard import Key
import threading
import json

class TestActivityMonitorStressTest(unittest.TestCase):
    def setUp(self):
        self.mock_data_uploader = Mock()
        self.mock_data_uploader.send_data = Mock(return_value=True)

        self.monitor = ActivityMonitor(self.mock_data_uploader)
        self.monitor.start_monitoring()

    def simulate_keyboard_events(self, num_events):
        for _ in range(num_events):
            self.monitor.on_press(Key.space)
            self.monitor.on_press(Key.esc)

    def simulate_mouse_events(self, num_events):
        for _ in range(num_events):
            self.monitor.on_click(100, 100, 1, True)
            self.monitor.on_move(200, 200)

    def test_queue_stress(self):
        num_events = 30
        threads = []

        # Simulate keyboard events in a separate thread
        keyboard_thread = threading.Thread(target=self.simulate_keyboard_events, args=(num_events,))
        threads.append(keyboard_thread)

        # Simulate mouse events in a separate thread
        mouse_thread = threading.Thread(target=self.simulate_mouse_events, args=(num_events,))
        threads.append(mouse_thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
            
        # Give some time for the event processing thread to process all events
        self.monitor.event_queue.join()


        expected_num_events = num_events * 4  # 2 from keyboard, 2 from mouse per loop
        
        # Pretty print the event buffer
        print("Event buffer (pretty-printed):")
        print(json.dumps(self.monitor.event_buffer, indent=4))
        self.assertEqual(len(self.monitor.event_buffer), expected_num_events)

    def tearDown(self):
        self.monitor.stop_monitoring()

if __name__ == '__main__':
    unittest.main()
