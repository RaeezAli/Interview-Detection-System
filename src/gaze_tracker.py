import cv2

class GazeTracker:
    def __init__(self):
        self.gaze = "Focused"

    def get_gaze_ratio(self, frame):
        # Placeholder: always return "Focused"
        # Optional: use simple eye ROI and thresholding for real detection
        return self.gaze
