import csv
import time

class Logger:
    def __init__(self, filename="interview_log.csv"):
        self.filename = filename
        with open(self.filename, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Emotion", "Gaze", "Score", "Blink Rate", "Yaw"])

    def log(self, emotion, gaze, score, blink_rate=None, yaw=None):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filename, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, emotion, gaze, score, blink_rate, yaw])
