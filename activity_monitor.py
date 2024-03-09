import time
from pynput import keyboard, mouse
from threading import Thread, Event
import tkinter as tk
from datetime import datetime, timedelta
import getpass
import pygetwindow as gw
import requests

class ActivityMonitor:
    KEYBOARD_SESSION_TIMEOUT = timedelta(seconds=3)

    def __init__(self, data_uploader):
        self.data_uploader = data_uploader
        self.user_id = getpass.getuser()
        self.event_buffer = []
        self.keyboard_activity_buffer = []
        self.last_keyboard_activity_time = None
        self.focus_level_submitted = False
        self.monitoring_active = Event()
        self.mouse_position_buffer = []
        self.monitoring_active.set()
        self.last_event_time = None
        self.current_focus_level = None

    def log_event(self, event_type, data):
        current_time = datetime.now()
        timestamp = current_time.isoformat()
        
        # Initialize the time delta as None for the first event
        time_delta = None
        
        # Calculate time delta if this is not the first event
        if self.last_event_time is not None:
            time_delta = (current_time - self.last_event_time).total_seconds()
        
        # Create the event dictionary, including the time delta if available
        event = {
            "timestamp": timestamp,
            "type": event_type,
            "data": data
        }
        if time_delta is not None:
            event['time_delta'] = time_delta
        
        # Append the event to the event buffer
        self.event_buffer.append(event)
        
        # Update the last_event_time to the current event's timestamp
        self.last_event_time = current_time

    def get_active_window_title(self):
        window = gw.getActiveWindow()
        if window:
            return window.title
        else:
            return None

    def log_active_window_periodically(self):
        last_active_window_title = None
        while self.monitoring_active.is_set():
            active_window_title = self.get_active_window_title()
            if active_window_title and active_window_title != last_active_window_title:
                self.log_event("active_window", {"title": active_window_title})
                last_active_window_title = active_window_title
            time.sleep(1)

    def log_mouse_movement_periodically(self):
        while self.monitoring_active.is_set():
            if self.mouse_position_buffer:
                start_position = self.mouse_position_buffer[0]
                end_position = self.mouse_position_buffer[-1]
                if start_position != end_position:
                    self.log_event('mouse_movement', {'start_position': start_position, 'end_position': end_position})
                self.mouse_position_buffer.clear()
            time.sleep(1)

    def log_keyboard_activity(self):
        while self.monitoring_active.is_set():
            if self.keyboard_activity_buffer and self.last_keyboard_activity_time:
                if datetime.now() - self.last_keyboard_activity_time >= self.KEYBOARD_SESSION_TIMEOUT:
                    # Typing session ended, log the session
                    start_time = self.keyboard_activity_buffer[0]["timestamp"]
                    end_time = self.keyboard_activity_buffer[-1]["timestamp"]
                    self.log_event("keyboard_activity_session", {"start_time": start_time, "end_time": end_time, "key_strokes": len(self.keyboard_activity_buffer)})
                    self.keyboard_activity_buffer.clear()  # Clear buffer for the next session
            time.sleep(1)  # Check every second

    def on_press(self, key):
        if not self.monitoring_active.is_set():
            return False
        timestamp = datetime.now().isoformat()
        self.keyboard_activity_buffer.append({"timestamp": timestamp, "key": str(key)})
        self.last_keyboard_activity_time = datetime.now()

    def on_click(self, x, y, button, pressed):
        if not self.monitoring_active.is_set() or not pressed:
            return False
        if pressed:
            self.log_event('mouse_event', {'position': (x,y), 'button': str(button)})

    def on_move(self,x, y):
        if not self.monitoring_active.is_set():
            return False
        self.mouse_position_buffer.append((x, y))

    def submit(self, focus_level):
        self.current_focus_level = focus_level
        self.log_event('focus_level', {'level': focus_level})

    def write_events_to_buffer_and_upload(self):
        if self.event_buffer and self.data_uploader:
            print(f"Uploading {len(self.event_buffer)} events to the server")
            # Use the DataUploader instance to send data
            response = self.data_uploader.send_data(self.user_id, self.event_buffer)
            if response:
                print("Upload successful")
            else:
                print("Upload failed")
            self.event_buffer.clear()

    def ask_focus_level(self):
        while True:
            time.sleep(60*30)
            self.focus_level_submitted = False
            root = tk.Tk()
            root.attributes('-topmost', True)
            root.focus_force()
            root.title("Focus Level")

            def on_submit():
                focus_level = scale.get()  # Get the value from the scale widget
                self.submit(focus_level)  # Call the outer submit function with the focus level
                self.focus_level_submitted = True
                root.destroy()
                self.write_events_to_buffer_and_upload()

            tk.Label(root, text="Rate your focus level:").pack()
            scale = tk.Scale(root, from_=0, to=10, orient='horizontal')
            scale.pack()
            tk.Button(root, text="Submit", command=on_submit).pack()  # Use the local on_submit function

            root.mainloop()

    def start_monitoring(self):
        self.monitoring_active.set()
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)
        self.keyboard_listener.start()
        self.mouse_listener.start()
        self.window_thread = Thread(target=self.log_active_window_periodically, daemon=True)
        self.window_thread.start()
        self.mouse_movement_thread = Thread(target=self.log_mouse_movement_periodically, daemon=True)
        self.mouse_movement_thread.start()
        self.keyboard_activity_thread = Thread(target=self.log_keyboard_activity, daemon=True)
        self.keyboard_activity_thread.start()
        self.focus_thread = Thread(target=self.ask_focus_level, daemon=True)
        self.focus_thread.start()

    def stop_monitoring(self):
        self.monitoring_active.clear()  # Signal all threads to stop
        self.keyboard_listener.stop()
        self.mouse_listener.stop()