import unittest
from unittest.mock import patch
from data_uploader import DataUploader

class TestDataUploader(unittest.TestCase):
    def setUp(self):
        self.api_url = "https://example.com/upload"
        self.api_key = "fake_api_key"
        self.data_uploader = DataUploader(self.api_url, self.api_key)

    @patch('data_uploader.requests.post')
    def test_send_data(self, mock_post):
        # Setup mock response
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Success"}

        # Data to be uploaded
        user_id = "test_user"
        event_buffer = [{"event": "test_event", "timestamp": "2024-03-07T12:00:00"}]

        # Invoke the method
        response = self.data_uploader.send_data(user_id, event_buffer)

        # Assertions
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        mock_post.assert_called_once_with(
            self.api_url,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            },
            json={
                'user_id': user_id,
                'events': event_buffer
            }
        )

if __name__ == '__main__':
    unittest.main()
