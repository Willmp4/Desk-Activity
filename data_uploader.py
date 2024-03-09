import requests
class DataUploader:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key

    def send_data(self, user_id, event_buffer):
        if event_buffer:
            print(f"Uploading {len(event_buffer)} events")
            data = {
                'user_id': user_id,
                'events': event_buffer
            }
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }
            response = requests.post(self.api_url, headers=headers, json=data)
            return response
