import time
from pynput import keyboard, mouse
from threading import Thread, Event
import tkinter as tk
from datetime import datetime
import json
import boto3
import getpass
import pygetwindow as gw

event_buffer = []
focus_level_submitted = False
monitoring_active = Event()
monitoring_active.set()


def log_event(event_type, data):
    global event_buffer
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    event_buffer.append(event)

def get_active_window_title():
    window = gw.getActiveWindow()
    if window:  # Check if there is an active window
        return window.title
    else:
        return None

def log_active_window_periodically():
    last_active_window_title = None  # Initialize the last active window title as None
    while monitoring_active.is_set():  # Loop while monitoring is active
        active_window_title = get_active_window_title()
        if active_window_title and active_window_title != last_active_window_title:
            # Log the event only if there is an active window and the title has changed
            log_event("active_window", {"title": active_window_title})
            last_active_window_title = active_window_title  # Update the last active window title
        time.sleep(1)  # Sleep for a second or appropriate duration to throttle checks


def write_events_to_buffer():
    global focus_level_submitted
    if event_buffer and focus_level_submitted:  # Only write to buffer if focus level has been submitted
        filename = f'action_log_{datetime.now().isoformat().replace(":", "-")}.json'
        with open(filename, 'w') as f:
            json.dump(event_buffer, f)

def on_press(_):
    if not monitoring_active.is_set():
        return False
    log_event("keyboard_activity", {'activity': 'key_press'})

def on_click(x, y, button, pressed):
    if not monitoring_active.is_set() or not pressed:
        return False
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
        root.attributes('-topmost', True)
        root.focus_force()
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

def start_monitoring():
    global monitoring_active
    monitoring_active.set()
    keyboard_listener = keyboard.Listener(on_press=on_press)
    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener.start()
    mouse_listener.start()
    focus_thread = Thread(target=ask_focus_level)
    focus_thread.start()
    window_thread = Thread(target=log_active_window_periodically)
    window_thread.start()

def stop_monitoring():
    global monitoring_active
    monitoring_active.clear()
    
def main_gui():
    root = tk.Tk()
    root.title("Activity Monitor")
    start_button = tk.Button(root, text="Start Monitoring", command=start_monitoring)
    start_button.pack()

    stop_button = tk.Button(root, text="Stop Monitoring", command=stop_monitoring)
    stop_button.pack()
    
    root.mainloop()

def main():
    main_gui()

if __name__ == "__main__":
    main()

main()