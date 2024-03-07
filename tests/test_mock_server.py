import pytest
from moto import mock_aws  # Updated import
from server import app
import boto3
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture  # Use fixture for setup and teardown
def setup_mock_s3():
    """Create mock S3 environment."""
    with mock_aws():  # Use with statement to apply mock
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket='desk-top-activity')
        yield

def test_upload_events_success(client, setup_mock_s3):  # Include setup_mock_s3 fixture
    # No need to call setup_mock_s3 explicitly, pytest handles it via fixture

    # Example data to send
    data = {
        "user_id": "test_user",
        "events": [{"event": "test_event", "timestamp": "2023-01-01T00:00:00"}]
    }

    # Send a post request to the upload_events route
    response = client.post('/upload_events', data=json.dumps(data), content_type='application/json')
    
    # Assert response status code and data
    assert response.status_code == 200
    assert json.loads(response.data)['status'] == 'success'

    # Further, you can retrieve the object from the mock S3 to assert its existence and content
    # This part needs to be within the mock_aws context if you're querying S3 outside the initial setup
    with mock_aws():
        s3 = boto3.client('s3', region_name='us-east-1')
        obj = s3.get_object(Bucket='desk-top-activity', Key=f'{data["user_id"]}/2024-03-07/activity_log.json')
        obj_data = json.loads(obj['Body'].read())
        assert len(obj_data) == 1  # Assert that the event list has one item
        assert obj_data[0]['event'] == 'test_event'  # Assert event content
