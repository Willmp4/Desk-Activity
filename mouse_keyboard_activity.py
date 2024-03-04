import time
from pynput import keyboard, mouse
from threading import Thread
import tkinter as tk
import datetime as datetime
import tkinter as tk
import json
import boto3
import getpass
event_buffer = []

def log_event(event_type, data):
    global event_buffer
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    event_buffer.append(event)

def write_events_to_buffer():
    if event_buffer:
        filename = f'action_log_{datetime.now().isoformat().replace(":", "-")}.json'
        with open(filename, 'w') as f:
            json.dump(event_buffer, f)
        event_buffer.clear()

def on_press(key):
    try:
        key_char = key.char  # Try to access the character of the key pressed
    except AttributeError:
        key_char = str(key)  # If it's a special key, convert the key object to string
    log_event("key_press", {'key': key_char})


def on_click(x, y, button, pressed):
    if pressed:
        log_event('mouse_event', {'position': (x,y), 'button': str(button)})

def submit(focus_level):
    log_event('focus_level', {'level': focus_level})
def ask_focus_level():
    while True:
        time.sleep(15)
        root = tk.Tk()
        root.title("Focus Level")

        def submit():
            focus_level = scale.get()  # Get the focus level from the slider
            log_event('focus_level', {'level': focus_level})
            root.destroy()

        tk.Label(root, text="Rate your focus level:").pack()
        scale = tk.Scale(root, from_=0, to=10, orient='horizontal')
        scale.pack()
        tk.Button(root, text="Submit", command=submit).pack()
        write_events_to_buffer()

        root.mainloop()
user_id = getpass.getuser()
s3_client = boto3.client('s3')
bucket_name = 'desk-top-activity'

def upload_data_to_s3(data, user_id):
    """Upload the event data to S3 under the user's directory."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y%m%d%H%M%S")
    key = f"{user_id}/{date_str}/activity_log_{timestamp_str}.json"
    
    try:
        response = s3_client.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(data))
        print(f"Data uploaded successfully to {bucket_name}/{key}")
    except Exception as e:
        print(f"Failed to upload data to S3: {e}")

def write_events_to_buffer_and_upload():
    """Serialize the buffer to JSON and upload to S3."""
    global event_buffer
    if event_buffer:
        upload_data_to_s3(event_buffer, user_id)
        event_buffer.clear()  # Clear the buffer after upload