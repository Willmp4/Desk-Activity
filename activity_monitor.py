from threading import Thread, Event, Lock
import queue
import time
from datetime import datetime
import getpass
import tkinter as tk
from pynput import keyboard, mouse
import pygetwindow as gw
import cv2
from gaze_predictor import GazePredictor

class ActivityMonitor:
    MOUSE_MOVE_THROTTLE = 0.5
    ASK_FOCUS_LEVEL_INTERVAL = 30
    KEYBOARD_SESSION_TIMEOUT = 1
    GAZE_MONITOR_INTERVAL = 3

    def __init__(self, data_uploader):
        self.data_uploader = data_uploader
        self.user_id = getpass.getuser()
        self.monitoring_active = Event()
        self.monitoring_active.set()
        self.event_queue = queue.Queue()
        self.event_queue_lock = Lock()
        self.last_mouse_event_time = time.time()
        self.mouse_start_position = None
        self.keyboard_activity_buffer = []
        self.last_keyboard_activity_time = None
        self.window_activity_thread = None
        self.gaze_start_time = None
        self.gaze_start_position = None
        self.gaze_predictor = GazePredictor(
            model_path='./eye_gaze_v31_20.h5',
            adjustment_model_path='./adjustment_model.pkl',
            shape_predictor_path='./shape_predictor_68_face_landmarks.dat',
        )


    def log_event(self, event_type, data):
        timestamp = datetime.now().isoformat()
        event = {"timestamp": timestamp, "type": event_type, "data": data}
        with self.event_queue_lock:
            self.event_queue.put(event)

    def on_press(self, key):
        print(f"Key pressed: {key}")  # Debug: Check if key press is detected
        if not self.monitoring_active.is_set():
            return False
        print("Monitoring is active.")  # Debug: Confirm monitoring is active
        if not self.keyboard_activity_buffer:
            self.keyboard_activity_buffer.append({"timestamp": datetime.now().isoformat(), "key": str(key)})
            self.last_keyboard_activity_time = time.time()
        else:
            # If the last keyboard activity was within the timeout, append to the buffer
            if time.time() - self.last_keyboard_activity_time <= self.KEYBOARD_SESSION_TIMEOUT:
                self.keyboard_activity_buffer.append({"timestamp": datetime.now().isoformat(), "key": str(key)})
                self.last_keyboard_activity_time = time.time()
            else:
                # Log the session and start a new one
                self.log_event('keyboard_session', {
                    'start_time': self.keyboard_activity_buffer[0]["timestamp"],
                    'end_time': self.keyboard_activity_buffer[-1]["timestamp"],
                    'key_strokes': len(self.keyboard_activity_buffer)
                })
                print(f"Keyboard session logged: {self.keyboard_activity_buffer}")  # Debug: Check session logging
                self.keyboard_activity_buffer = [{"timestamp": datetime.now().isoformat(), "key": str(key)}]
                self.last_keyboard_activity_time = time.time()

    def on_click(self, x, y, button, pressed):
        if not self.monitoring_active.is_set():
            return False
        if pressed:
            self.log_event('mouse_click', {'position': (x, y), 'button': str(button)})
            self.mouse_start_position = (x, y)
        else:
            if self.mouse_start_position:
                self.log_event('mouse_movement', {'start_position': self.mouse_start_position, 'end_position': (x, y)})
                self.mouse_start_position = None

    def on_move(self, x, y):
        if not self.monitoring_active.is_set():
            return False
        current_time = time.time()
        if current_time - self.last_mouse_event_time >= self.MOUSE_MOVE_THROTTLE:
            if not self.mouse_start_position:
                self.mouse_start_position = (x, y)
            self.last_mouse_event_time = current_time

    def log_active_window_periodically(self):
        last_active_window_title = None
        while self.monitoring_active.is_set():
            active_window_title = gw.getActiveWindow().title if gw.getActiveWindow() else None
            if active_window_title and active_window_title != last_active_window_title:
                self.log_event("active_window", {"title": active_window_title})
                last_active_window_title = active_window_title
            time.sleep(2)

    def monitor_gaze(self):
        cap = cv2.VideoCapture(0)
        while self.monitoring_active.is_set():
            ret, frame = cap.read()
            if not ret:
                break

            gaze_x, gaze_y, adjusted_x, adjusted_y = self.gaze_predictor.predict_gaze(frame)
            if gaze_x is not None and self.gaze_start_time is None:
                # Mark the start of a new gaze period
                self.gaze_start_time = time.time()
                self.gaze_start_position = (adjusted_x, adjusted_y)

            current_time = time.time()
            if self.gaze_start_time and current_time - self.gaze_start_time >= self.GAZE_MONITOR_INTERVAL:
                # Log the end of the gaze period
                self.log_event('gaze_period', {
                    'start_position': self.gaze_start_position,
                    'end_position': (adjusted_x, adjusted_y),
                    'start_time': self.gaze_start_time,
                    'end_time': current_time
                })
                # Reset for the next period
                self.gaze_start_time = None
                self.gaze_start_position = None

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()

    def ask_focus_level(self):
        while self.monitoring_active.is_set():
            time.sleep(self.ASK_FOCUS_LEVEL_INTERVAL)
            root = tk.Tk()
            root.attributes('-topmost', True)
            root.focus_force()
            root.title("Focus Level")

            def on_submit():
                focus_level = scale.get()
                self.log_event('focus_level', {'level': focus_level})
                root.destroy()
                self.upload_events_batch()

            tk.Label(root, text="Rate your focus level:").pack()
            scale = tk.Scale(root, from_=0, to=10, orient='horizontal')
            scale.pack()
            tk.Button(root, text="Submit", command=on_submit).pack()

            root.mainloop()

    def upload_events_batch(self):
        event_batch = []
        with self.event_queue_lock:
            while not self.event_queue.empty():
                event = self.event_queue.get_nowait()
                event_batch.append(event)
                self.event_queue.task_done()
        if event_batch:
            self.data_uploader.send_data(self.user_id, event_batch)


    def start_monitoring(self):
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)
        
        self.keyboard_listener.start()
        self.mouse_listener.start()
        
        self.focus_thread = Thread(target=self.ask_focus_level, daemon=True)
        self.focus_thread.start()

        self.window_activity_thread = Thread(target=self.log_active_window_periodically, daemon=True)
        self.window_activity_thread.start()

        self.gaze_monitoring_thread = Thread(target=self.monitor_gaze, daemon=True)
        self.gaze_monitoring_thread.start()

    def stop_monitoring(self):
        self.monitoring_active.clear()
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
