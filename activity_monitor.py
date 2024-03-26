from threading import Thread, Event, Lock
import queue
import time
from datetime import datetime
import getpass
import tkinter as tk
from pynput import keyboard, mouse

class ActivityMonitor:
    MOUSE_MOVE_THROTTLE = 0.1
    ASK_FOCUS_LEVEL_INTERVAL = 10

    def __init__(self, data_uploader):
        self.data_uploader = data_uploader
        self.user_id = getpass.getuser()
        self.monitoring_active = Event()
        self.monitoring_active.set()
        self.event_queue = queue.Queue()
        self.event_queue_lock = Lock()
        self.last_mouse_event_time = time.time()

    def log_event(self, event_type, data):
        timestamp = datetime.now().isoformat()
        event = {"timestamp": timestamp, "type": event_type, "data": data}
        with self.event_queue_lock:
            self.event_queue.put(event)

    def on_press(self, key):
        if not self.monitoring_active.is_set():
            return False
        self.log_event('keyboard_event', {'key': str(key)})

    def on_click(self, x, y, button, pressed):
        if not self.monitoring_active.is_set():
            return False
        if pressed:
            self.log_event('mouse_click', {'position': (x, y), 'button': str(button)})

    def on_move(self, x, y):
        if not self.monitoring_active.is_set():
            return False
        current_time = time.time()
        if current_time - self.last_mouse_event_time >= self.MOUSE_MOVE_THROTTLE:
            self.log_event('mouse_move', {'position': (x, y)})
            self.last_mouse_event_time = current_time

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

    def stop_monitoring(self):
        self.monitoring_active.clear()
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
