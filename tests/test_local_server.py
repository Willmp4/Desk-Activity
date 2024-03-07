import requests

def test_upload_events():
    url = "http://localhost:5000/upload_events"
    data = {
        "user_id": "test_user",
        "events": [
            {"event": "test_event", "timestamp": "2023-01-01T00:00:00"}
        ]
    }

    response = requests.post(url, json=data)

    # Assert the request responded with a 200 OK status code
    assert response.status_code == 200

    # Additional assertions can be made here depending on what the API returns
    # For example, if the API returns a JSON response with a success status, you might check:
    # response_data = response.json()
    # assert response_data['success'] is True
