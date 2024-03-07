import boto3
import json
import pytest

# Assuming boto3 is already configured with AWS credentials

@pytest.fixture(scope="module")
def lambda_client():
    """Fixture to initialize and return a boto3 client for AWS Lambda."""
    return boto3.client('lambda', region_name='eu-west-2')

def test_invoke_lambda_with_test_data(lambda_client):
    test_data = {
        "user_id": "erykah",
        "events": [
            {
                "timestamp": "2024-03-07T12:00:00",
                "type": "keyboard_activity_session",
                "data": {
                    "start_time": "2024-03-07T12:00:00",
                    "end_time": "2024-03-07T12:01:00",
                    "key_strokes": 50
                }
            },
            {
                "timestamp": "2024-03-07T12:05:00",
                "type": "mouse_movement",
                "data": {
                    "start_position": (100, 100),
                    "end_position": (200, 200)
                }
            }
        ]
    }

    try:
        response = lambda_client.invoke(
            FunctionName='upload_s3_bucket',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_data),
        )

        # Decode the response payload
        response_payload = json.load(response['Payload'])
        assert 'Data uploaded successfully to S3' in response_payload['body']
        print("Lambda invocation response:", response_payload)
    except Exception as e:
        pytest.fail(f"Error invoking Lambda function: {e}")
