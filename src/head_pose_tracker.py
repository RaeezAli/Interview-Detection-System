import cv2
import numpy as np

class HeadPoseTracker:
    def __init__(self):
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0

    def get_head_pose(self, frame):
        # Placeholder: return random small angles
        # Optional: implement full PnP using facial landmarks if needed
        h, w, _ = frame.shape
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        return self.yaw, self.pitch, self.roll
