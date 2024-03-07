
from flask import Flask, request, jsonify
import boto3
import json

app = Flask(__name__)
lambda_client = boto3.client('lambda')

@app.route('/upload_events', methods=['POST'])
def upload_events():
    data = request.json
    # Invoke Lambda function
    response = lambda_client.invoke(
        FunctionName='upload_s3_bucket',  # Replace with your Lambda function's name
        InvocationType='RequestResponse',
        Payload=json.dumps(data),
    )
    return jsonify({'status': 'success', 'lambda_response': response['StatusCode']})

if __name__ == '__main__':
    app.run(debug=True)
