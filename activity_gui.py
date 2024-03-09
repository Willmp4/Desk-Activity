import tkinter as tk
class ActivityMonitorGUI:
    def __init__(self, activity_monitor):
        self.activity_monitor = activity_monitor
        self.root = tk.Tk()
        self.root.title("Activity Monitor")
        self.setup_ui()

    def setup_ui(self):
        start_button = tk.Button(self.root, text="Start Monitoring", command=self.activity_monitor.start_monitoring)
        start_button.pack()

        stop_button = tk.Button(self.root, text="Stop Monitoring", command=self.activity_monitor.stop_monitoring)
        stop_button.pack()

    def run(self):
        self.root.mainloop()
