import time
from pynput import keyboard, mouse
from threading import Thread, Event
import tkinter as tk
from datetime import datetime, timedelta
import getpass
import pygetwindow as gw
import requests


user_id = getpass.getuser()
event_buffer = []
keyboard_activity_buffer = []
last_keyboard_activity_time = None
KEYBOARD_SESSION_TIMEOUT = timedelta(seconds=3)
focus_level_submitted = False
monitoring_active = Event()
mouse_position_buffer = []
monitoring_active.set()
last_event_time = None
current_focus_level = None

def log_event(event_type, data):
    global event_buffer, last_event_time
    current_time = datetime.now()
    timestamp = current_time.isoformat()
    
    # Initialize the time delta as None for the first event
    time_delta = None
    
    # Calculate time delta if this is not the first event
    if last_event_time is not None:
        time_delta = (current_time - last_event_time).total_seconds()
    
    # Create the event dictionary, including the time delta if available
    event = {
        "timestamp": timestamp,
        "type": event_type,
        "data": data
    }
    if time_delta is not None:
        event['time_delta'] = time_delta
    
    # Append the event to the event buffer
    event_buffer.append(event)
    
    # Update the last_event_time to the current event's timestamp
    last_event_time = current_time

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

def send_data_to_lambda(data):
    api_gateway_url = 'https://ygmxyfodkg.execute-api.eu-west-2.amazonaws.com/prod/events'
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': 'API_KEY_PLACEHOLDER'
    }
    response = requests.post(api_gateway_url, headers=headers, json=data)
    return response

def write_events_to_buffer_and_upload():
    global event_buffer
    if event_buffer:
        print(f"Uploading {len(event_buffer)} events to S3")
        data = {
            'user_id': user_id,
            'events': event_buffer
        }
        r = send_data_to_lambda(data)
        event_buffer.clear()


def submit(focus_level):
    global current_focus_level  # Correctly declare the global variable
    current_focus_level = focus_level  # Update the global focus level
    log_event('focus_level', {'level': focus_level})

def ask_focus_level():
    global focus_level_submitted, current_focus_level
    while True:
        time.sleep(60*30)
        focus_level_submitted = False
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.focus_force()
        root.title("Focus Level")

        def on_submit():
            focus_level = scale.get()  # Get the value from the scale widget
            submit(focus_level)  # Call the outer submit function with the focus level
            focus_level_submitted = True
            root.destroy()
            write_events_to_buffer_and_upload()

        tk.Label(root, text="Rate your focus level:").pack()
        scale = tk.Scale(root, from_=0, to=10, orient='horizontal')
        scale.pack()
        tk.Button(root, text="Submit", command=on_submit).pack()  # Use the local on_submit function

        root.mainloop()

def start_monitoring():
    global monitoring_active, last_event_time
    last_event_time = None
    monitoring_active.set()
    keyboard_listener = keyboard.Listener(on_press=on_press)
    mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
    keyboard_listener.start()
    mouse_listener.start()
    focus_thread = Thread(target=ask_focus_level, daemon=True)
    focus_thread.start()
    window_thread = Thread(target=log_active_window_periodically, daemon=True)
    window_thread.start()
    mouse_movement_thread = Thread(target=log_mouse_movement_periodically, daemon=True)
    mouse_movement_thread.start()
    keyboard_activity_thread = Thread(target=log_keyboard_activity, daemon=True)  # Log keyboard activity
    keyboard_activity_thread.start()

def stop_monitoring():
    global monitoring_active, last_event_time
    last_event_time = None
    monitoring_active.clear()  # Signal all threads to stop

def main_gui():
    root = tk.Tk()
    root.title("Activity Monitor")
    start_button = tk.Button(root, text="Start Monitoring", command=start_monitoring)
    start_button.pack()

    stop_button = tk.Button(root, text="Stop Monitoring", command=stop_monitoring)
    stop_button.pack()
    
    root.mainloop()

    def on_close():
        stop_monitoring()
        root.destroy()

def main():
    main_gui()

if __name__ == "__main__":
    main()
