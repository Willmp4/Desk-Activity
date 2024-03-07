import unittest
from unittest.mock import patch, MagicMock

#add parent directory to path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mouse_keyboard_activity  # replace 'your_module' with the name of the file containing your functions

class TestLambdaDataUpload(unittest.TestCase):
    @patch('mouse_keyboard_activity.boto3.client')
    def test_send_data_to_lambda(self, mock_boto3_client):
        # Arrange
        lambda_client_mock = MagicMock()
        mock_boto3_client.return_value = lambda_client_mock
        data = {"test": "data"}
        
        # Act
        mouse_keyboard_activity.send_data_to_lambda(data, lambda_client=lambda_client_mock)
        
        # Assert
        lambda_client_mock.invoke.assert_called_once_with(
            FunctionName='upload_s3_bucket',
            InvocationType='RequestResponse',
            Payload='{"test": "data"}',
        )


#     @patch('mouse_keyboard_activity.send_data_to_lambda')
#     def test_write_events_to_buffer_and_upload(self, mock_send_data_to_lambda):
#         # Arrange
#         mouse_keyboard_activity.event_buffer = [{'event': 'test_event'}]  # Simulate an event in the buffer
#         mouse_keyboard_activity.user_id = 'test_user'  # Set a test user ID

#         # Act
#         mouse_keyboard_activity.write_events_to_buffer_and_upload()
        
#         # Assert
#         mock_send_data_to_lambda.assert_called_once()
#         data_sent = mock_send_data_to_lambda.call_args[0][0]
#         self.assertEqual(data_sent['user_id'], 'test_user')
#         self.assertEqual(data_sent['events'], [{'event': 'test_event'}])
#         self.assertEqual(len(mouse_keyboard_activity.event_buffer), 0)  # Check if the buffer is cleared

if __name__ == '__main__':
    unittest.main()
