import time
from pynput import keyboard, mouse
from threading import Thread, Event
import tkinter as tk
from datetime import datetime, timedelta
import getpass
import pygetwindow as gw
import requests
import sys
import json
import boto3

user_id = getpass.getuser()
event_buffer = []
keyboard_activity_buffer = []
last_keyboard_activity_time = None
KEYBOARD_SESSION_TIMEOUT = timedelta(seconds=2)
focus_level_submitted = False
monitoring_active = Event()
mouse_position_buffer = []
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
    if window:
        return window.title
    else:
        return None

def log_active_window_periodically():
    last_active_window_title = None
    while monitoring_active.is_set():
        active_window_title = get_active_window_title()
        if active_window_title and active_window_title != last_active_window_title:
            log_event("active_window", {"title": active_window_title})
            last_active_window_title = active_window_title
        time.sleep(1)

def log_mouse_movement_periodically():
    global mouse_position_buffer
    while monitoring_active.is_set():
        if mouse_position_buffer:
            start_position = mouse_position_buffer[0]
            end_position = mouse_position_buffer[-1]
            if start_position != end_position:
                log_event('mouse_movement', {'start_position': start_position, 'end_position': end_position})
            mouse_position_buffer.clear()
        time.sleep(1)

def log_keyboard_activity():
    global keyboard_activity_buffer, last_keyboard_activity_time
    while monitoring_active.is_set():
        if keyboard_activity_buffer and last_keyboard_activity_time:
            if datetime.now() - last_keyboard_activity_time >= KEYBOARD_SESSION_TIMEOUT:
                # Typing session ended, log the session
                start_time = keyboard_activity_buffer[0]["timestamp"]
                end_time = keyboard_activity_buffer[-1]["timestamp"]
                log_event("keyboard_activity_session", {"start_time": start_time, "end_time": end_time, "key_strokes": len(keyboard_activity_buffer)})
                keyboard_activity_buffer.clear()  # Clear buffer for the next session
        time.sleep(1)  # Check every second

def on_press(key):
    global last_keyboard_activity_time, keyboard_activity_buffer
    if not monitoring_active.is_set():
        return False
    timestamp = datetime.now().isoformat()
    keyboard_activity_buffer.append({"timestamp": timestamp, "key": str(key)})
    last_keyboard_activity_time = datetime.now()

def on_click(x, y, button, pressed):
    if not monitoring_active.is_set() or not pressed:
        return False
    if pressed:
        log_event('mouse_event', {'position': (x,y), 'button': str(button)})

def on_move(x, y):
    global mouse_position_buffer
    if not monitoring_active.is_set():
        return False
    mouse_position_buffer.append((x, y))

def submit(focus_level):
    log_event('focus_level', {'level': focus_level})

def send_data_to_lambda(data, lambda_client=None):
    if lambda_client is None:
        lambda_client = boto3.client('lambda', region_name='eu-west-2')
    # rest of the code remains the same

    response = lambda_client.invoke(
        FunctionName='upload_s3_bucket',  # Replace with your Lambda function's name
        InvocationType='RequestResponse',
        Payload=json.dumps(data),
    )
    return response

def write_events_to_buffer_and_upload():
    global event_buffer
    if event_buffer:
        print(f"Uploading {len(event_buffer)} events to S3")
        data = {
            "user_id": user_id,
            "events": event_buffer
        }
        send_data_to_lambda(data)
        event_buffer.clear()

def ask_focus_level():
    global focus_level_submitted
    while True:
        time.sleep(15)
        focus_level_submitted = False
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.focus_force()
        root.title("Focus Level")

        def submit():
            global focus_level_submitted
            focus_level = scale.get()
            log_event('focus_level', {'level': focus_level})
            focus_level_submitted = True
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
    mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
    keyboard_listener.start()
    mouse_listener.start()
    focus_thread = Thread(target=ask_focus_level)
    focus_thread.start()
    window_thread = Thread(target=log_active_window_periodically)
    window_thread.start()
    mouse_movement_thread = Thread(target=log_mouse_movement_periodically)
    mouse_movement_thread.start()
    keyboard_activity_thread = Thread(target=log_keyboard_activity)  # Log keyboard activity
    keyboard_activity_thread.start()

def stop_monitoring():
    global monitoring_active
    monitoring_active.clear()  # Signal all threads to stop
    sys.exit()  # Terminate the program
    
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
