import time
from pynput import keyboard, mouse
from threading import Thread
import tkinter as tk
from datetime import datetime
import json
import boto3
import getpass
event_buffer = []
focus_level_submitted = False  # Flag to track if the focus level has been submitted

def log_event(event_type, data):
    global event_buffer
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    event_buffer.append(event)

# def write_events_to_buffer():
#     global focus_level_submitted
#     if event_buffer and focus_level_submitted:  # Only write to buffer if focus level has been submitted
#         filename = f'action_log_{datetime.now().isoformat().replace(":", "-")}.json'
#         with open(filename, 'w') as f:
#             json.dump(event_buffer, f)

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
user_id = getpass.getuser()
s3_client = boto3.client('s3')
bucket_name = 'desk-top-activity'

def upload_data_to_s3(data, user_id):
    """Upload the event data to S3 under the user's directory."""
    now = datetime.now()
    print(now)
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
        print(f"Uploading {len(event_buffer)} events to S3")
        upload_data_to_s3(event_buffer, user_id)
        event_buffer.clear()  # Clear the buffer after upload
        
def ask_focus_level():
    global focus_level_submitted  # Use global instead of nonlocal
    while True:
        time.sleep(15)  # Consider adjusting or removing this for testing
        focus_level_submitted = False  # Reset the flag each time asking for focus level
        root = tk.Tk()
        root.title("Focus Level")

        def submit():
            global focus_level_submitted  # Corrected to global
            focus_level = scale.get()  # Get the focus level from the slider
            log_event('focus_level', {'level': focus_level})
            focus_level_submitted = True  # Set the flag to True after submission
            root.destroy()
            write_events_to_buffer_and_upload() 
        tk.Label(root, text="Rate your focus level:").pack()
        scale = tk.Scale(root, from_=0, to=10, orient='horizontal')
        scale.pack()
        tk.Button(root, text="Submit", command=submit).pack()

        root.mainloop()

keyboard_listener = keyboard.Listener(on_press=on_press)
mouse_listener = mouse.Listener(on_click=on_click)

def start_monitoring():
    keyboard_listener.start()
    mouse_listener.start()
    focus_thread = Thread(target=ask_focus_level)
    focus_thread.start()
    write_thread = Thread(target=write_events_to_buffer_and_upload)
    write_thread.start()
    

def main_gui():
    root = tk.Tk()
    root.title("Activity Monitor")
    start_button = tk.Button(root, text="Start Monitoring", command=start_monitoring)
    start_button.pack()
    root.mainloop()

main_gui()