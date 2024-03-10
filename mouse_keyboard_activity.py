from data_uploader import DataUploader
from activity_monitor import ActivityMonitor
from activity_gui import ActivityMonitorGUI
def main():
    api_url = 'https://ygmxyfodkg.execute-api.eu-west-2.amazonaws.com/prod/events'
    api_key = 'API_KEY_PLACEHOLDER'
    data_uploader = DataUploader(api_url, api_key)
    activity_monitor = ActivityMonitor(data_uploader=data_uploader)
    gui = ActivityMonitorGUI(activity_monitor=activity_monitor)
    gui.run()

if __name__ == "__main__":
    main()