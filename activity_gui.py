import tkinter as tk
from threading import Thread
import time

class ActivityMonitorGUI:
    def __init__(self, activity_monitor):
        self.activity_monitor = activity_monitor
        self.root = tk.Tk()
        self.root.title("Activity Monitor")
        self.countdown_time = self.activity_monitor.ASK_FOCUS_LEVEL_INTERVAL 
        self.setup_ui()

    def setup_ui(self):
        self.countdown_label = tk.Label(self.root, text="Starting...", font=("Helvetica", 16))
        self.countdown_label.pack()

        start_button = tk.Button(self.root, text="Start Monitoring", command=self.start_monitoring_with_countdown)
        start_button.pack()

        stop_button = tk.Button(self.root, text="Stop Monitoring", command=self.activity_monitor.stop_monitoring)
        stop_button.pack()

    def run(self):
        self.root.mainloop()

    def start_monitoring_with_countdown(self):
        self.activity_monitor.start_monitoring()
        self.start_countdown()

    def start_countdown(self):
        # Reset the countdown time at the start
        self.countdown_time = self.activity_monitor.ASK_FOCUS_LEVEL_INTERVAL
        self.update_countdown_label()
        self.countdown()

    def countdown(self):
        if self.countdown_time > 0:
            self.countdown_time -= 1
            self.update_countdown_label()
            # Schedule the countdown method to be called after 1 second
            self.root.after(200, self.countdown)
        else:
            # When countdown reaches zero, reset it
            self.start_countdown()

    def update_countdown_label(self):
        self.countdown_label.config(text=f"Time until next focus check: {self.countdown_time} seconds")
