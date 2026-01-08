import mediapipe as mp
import cv2

class GazeTracker:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)
        self.LEFT_EYE = [33, 133]  # eye corners
        self.LEFT_IRIS = [468, 473]  # iris landmarks

    def get_gaze_ratio(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            return "No Face"

        mesh = results.multi_face_landmarks[0].landmark

        x1 = mesh[self.LEFT_EYE[0]].x
        x2 = mesh[self.LEFT_EYE[1]].x
        xi = mesh[self.LEFT_IRIS[0]].x

        ratio = (xi - x1) / (x2 - x1)

        if ratio < 0.35:
            return "Looking Left"
        elif ratio > 0.65:
            return "Looking Right"
        else:
            return "Focused"