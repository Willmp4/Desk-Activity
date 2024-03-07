import pytest
from unittest.mock import patch
from mouse_keyboard_activity import send_data_to_server

@pytest.mark.parametrize("status_code, expected_call_count", [
    (200, 1),  # Test case for successful server response
    (500, 1)   # Test case for failure server response
])
def test_send_data_to_server(status_code, expected_call_count):
    data = {"test": "data"}

    with patch('mouse_keyboard_activity.requests.post') as mock_post:
        mock_post.return_value.status_code = status_code

        send_data_to_server(data)

        assert mock_post.call_count == expected_call_count
        mock_post.assert_called_once_with("http://localhost:5000/upload_events", json=data)
        assert mock_post.return_value.status_code == status_code
