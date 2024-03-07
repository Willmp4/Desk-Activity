from flask import Flask, request, jsonify
import json
import boto3
from datetime import datetime

app = Flask(__name__)

s3_client = boto3.client('s3')
bucket_name = 'desk-top-activity'

def file_exists_in_s3(bucket, key):
    """Check if the file exists in S3 bucket."""
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=key)
    for obj in response.get('Contents', []):
        if obj['Key'] == key:
            return True
    return False

def append_data_to_s3(bucket, key, new_data):
    """Append new data to an existing S3 file."""
    # Download the existing data
    existing_data_obj = s3_client.get_object(Bucket=bucket, Key=key)
    existing_data = json.load(existing_data_obj['Body'])
    
    # Append new data
    existing_data.extend(new_data)
    
    # Upload the updated data
    s3_client.put_object(Bucket=bucket, Key=key, Body=json.dumps(existing_data, indent=2))
    print(f"Data appended successfully to {bucket}/{key}")

def upload_data_to_s3(data, user_id):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    key_prefix = f"{user_id}/{date_str}"
    key = f"{key_prefix}/activity_log.json"
    
    # Check if a file for the current day already exists
    if file_exists_in_s3(bucket_name, key):
        # If exists, append data to the existing file
        append_data_to_s3(bucket_name, key, data)
    else:
        # If not, create a new file for the current day
        try:
            s3_client.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(data, indent=2))
            print(f"Data uploaded successfully to {bucket_name}/{key}")
        except Exception as e:
            print(f"Failed to upload data to S3: {e}")


@app.route('/upload_events', methods=['POST'])
def upload_events():
    data = request.json

    print("events uploaded to s3")
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)