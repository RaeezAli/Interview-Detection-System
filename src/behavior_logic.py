class BehaviorAnalysis:
    def __init__(self):
        self.score = 100
        self.logs = []

    def evaluate(self, emotion, gaze, blink_rate=None, yaw=None):
        if gaze in ["Looking Left", "Looking Right"]:
            self.score -= 2
        else:
            self.score += 0.2

        if emotion in ["Anger", "Fear"]:
            self.score -= 1
            self.logs.append(f"Stress detected: {emotion}")

        if blink_rate:
            if blink_rate > 25:
                self.score -= 1
            elif blink_rate < 8:
                self.score -= 0.5

        if yaw:
            if yaw > 20 or yaw < -20:
                self.score -= 1

        self.score = max(0, min(100, self.score))
        return round(self.score, 1)