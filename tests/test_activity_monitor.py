import unittest
from unittest.mock import patch
from datetime import datetime
from mouse_keyboard_activity import activity_monitor

class TestActivityMonitor(unittest.TestCase):
    def test_log_event(self):
        """Test that log_event adds an event correctly."""
        event_type = "test_event"
        data = {"key": "value"}
        
        # Reset event buffer for a clean test environment
        activity_monitor.event_buffer = []

        activity_monitor.log_event(event_type, data)
        
        self.assertEqual(len(activity_monitor.event_buffer), 1)
        logged_event = activity_monitor.event_buffer[0]
        
        self.assertEqual(logged_event["type"], event_type)
        self.assertEqual(logged_event["data"], data)
        self.assertTrue("timestamp" in logged_event)

    @patch('activity_monitor.requests.post')
    def test_send_data_to_server(self, mock_post):
        """Test sending data to server with mocked requests."""
        mock_post.return_value.status_code = 200

        data = {"test": "data"}
        activity_monitor.send_data_to_server(data)

        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_kwargs["json"], data)
        self.assertEqual(called_args[0], "http://localhost:5000/upload_events")

if __name__ == '__main__':
    unittest.main()
