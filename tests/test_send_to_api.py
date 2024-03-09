import unittest
from unittest.mock import patch, MagicMock

#add parent directory to path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mouse_keyboard_activity

class TestLambdaDataUpload(unittest.TestCase):
    @patch('mouse_keyboard_activity.requests.post')
    def test_send_data_to_lambda(self, mock_post):
        # Arrange
        data = {"test": "data"}
        expected_url = 'https://ygmxyfodkg.execute-api.eu-west-2.amazonaws.com/prod/events'
        expected_headers = {
            'Content-Type': 'application/json',
            'x-api-key': 'API_KEY_PLACEHOLDER'
        }
        expected_response = MagicMock()

        mock_post.return_value = expected_response

        # Act
        response = mouse_keyboard_activity.send_data_to_lambda(data)

        print(response)

        # Assert
        mock_post.assert_called_once_with(expected_url, headers=expected_headers, json=data)
        self.assertEqual(response, expected_response)

class TestLambdaDataUpload(unittest.TestCase):
    @patch('mouse_keyboard_activity.requests.post')
    def test_send_data_to_lambda_403(self, mock_post):
        # Arrange
        data = {"test": "data"}
        expected_url = 'https://ygmxyfodkg.execute-api.eu-west-2.amazonaws.com/prod/events'
        expected_headers = {
            'Content-Type': 'application/json',
            'x-api-key': 'API_KEY_PLACEHOLDER'
        }

        # Mock a 403 Forbidden response
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response

        # Act
        response = mouse_keyboard_activity.send_data_to_lambda(data)

        # Assert
        mock_post.assert_called_once_with(expected_url, headers=expected_headers, json=data)
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()
