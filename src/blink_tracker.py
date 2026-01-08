import cv2

class BlinkTracker:
    def __init__(self):
        self.blinks = 0
        self.prev_gray = None

    def update_blink(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_gray is None:
            self.prev_gray = gray
            return self.blinks

        diff = cv2.absdiff(self.prev_gray, gray)
        mean_diff = diff.mean()

        # Simple motion-based blink detection
        if mean_diff > 8:   # Threshold tuned for webcam
            self.blinks += 1

        self.prev_gray = gray
        return self.blinks
