import mediapipe as mp
import cv2
from scipy.spatial import distance

class BlinkTracker:
    def __init__(self):
        self.blinks = 0
        self.frames_no_blink = 0
        self.mp_face = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)
        self.LEFT_EYE = [159, 145, 153, 154, 155, 133]

    def eye_aspect_ratio(self, landmarks, eye_points, frame_shape):
        coords = [(landmarks[i].x * frame_shape[1], landmarks[i].y * frame_shape[0]) for i in eye_points]
        A = distance.euclidean(coords[1], coords[5])
        B = distance.euclidean(coords[2], coords[4])
        C = distance.euclidean(coords[0], coords[3])
        return (A + B) / (2.0 * C)

    def update_blink(self, frame, threshold=0.25):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.mp_face.process(rgb)
        if not results.multi_face_landmarks:
            return self.blinks

        landmarks = results.multi_face_landmarks[0].landmark
        ear = self.eye_aspect_ratio(landmarks, self.LEFT_EYE, frame.shape)

        if ear < threshold:
            self.frames_no_blink = 0
            self.blinks += 1
        else:
            self.frames_no_blink += 1

        return self.blinks
