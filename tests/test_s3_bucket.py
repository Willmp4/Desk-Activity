import boto3
from moto import mock_aws
import pytest
import json
from datetime import datetime
#append to parent directory
import sys
sys.path.append('..')
from lambda_function import upload_data_to_s3

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    return {
        "aws_access_key_id": "testing",
        "aws_secret_access_key": "testing",
        "aws_session_token": "testing",
    }

@pytest.fixture
def s3(aws_credentials):
    with mock_aws():
        yield boto3.client("s3", region_name="eu-west-2", **aws_credentials)

def test_upload_data_to_s3(s3):
    bucket_name = 'desk-top-activity'
    user_id = 'will'
    data = [{"event": "test_event", "timestamp": "2024-03-07T12:00:00"}]

    # Create the mocked bucket
    s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})
    
    # Now call your function to upload data to S3
    upload_data_to_s3(data, user_id)
    
    # Assert the file was created and contains the correct data
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    key = f"{user_id}/{date_str}/activity_log.json"
    response = s3.get_object(Bucket=bucket_name, Key=key)
    response_data = response['Body'].read().decode("utf-8")
    
    assert data == json.loads(response_data)

