import csv
import os
from datetime import datetime

class Logger:
    def __init__(self, filename='session_log.csv'):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'emotion', 'confidence', 'gaze', 'score', 'blink_count', 'yaw', 'pitch', 'roll'])

    def log(self, emotion, gaze, score, blink_count, yaw=0, pitch=0, roll=0, confidence=0.0):
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now(), emotion, confidence, gaze, score, blink_count, yaw, pitch, roll])
