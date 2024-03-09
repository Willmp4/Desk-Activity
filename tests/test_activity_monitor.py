import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from activity_monitor import ActivityMonitor

class TestActivityMonitor(unittest.TestCase):
    def setUp(self):
        self.data_uploader_mock = MagicMock()
        self.monitor = ActivityMonitor(data_uploader=self.data_uploader_mock)

    @patch('activity_monitor.datetime')
    def test_log_event_first_event(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2021, 1, 1, 12, 0, 0)
        mock_datetime.now.isoformat.return_value = '2021-01-01T12:00:00'
        self.monitor.log_event("test_event", {"data": "value"})
        self.assertEqual(len(self.monitor.event_buffer), 1)
        self.assertEqual(self.monitor.event_buffer[0]['type'], "test_event")
        self.assertEqual(self.monitor.event_buffer[0]['data'], {"data": "value"})
        self.assertIsNone(self.monitor.event_buffer[0].get('time_delta'))

    @patch('activity_monitor.datetime')
    def test_log_event_subsequent_event(self, mock_datetime):
        # First event
        mock_datetime.now.return_value = datetime(2021, 1, 1, 12, 0, 0)
        self.monitor.log_event("first_event", {"data": "value1"})
        # Second event, 10 seconds later
        mock_datetime.now.return_value += timedelta(seconds=10)
        self.monitor.log_event("second_event", {"data": "value2"})
        self.assertEqual(len(self.monitor.event_buffer), 2)
        self.assertEqual(self.monitor.event_buffer[1]['type'], "second_event")
        self.assertEqual(self.monitor.event_buffer[1]['time_delta'], 10)

    @patch('activity_monitor.getpass.getuser')
    def test_data_uploader_integration(self, mock_getuser):
        mock_getuser.return_value = "test_user"
        self.monitor.log_event("test_event", {"data": "value"})
        self.monitor.write_events_to_buffer_and_upload()
        self.data_uploader_mock.send_data.assert_called_once()

if __name__ == '__main__':
    unittest.main()
