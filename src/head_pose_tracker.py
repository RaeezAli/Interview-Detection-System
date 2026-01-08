import mediapipe as mp
import numpy as np
import cv2

class HeadPoseTracker:
    def __init__(self):
        self.mp_face = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)
        self.image_points_indices = [33, 263, 1, 61, 291, 199]  # nose tip, eyes, mouth corners

    def get_head_pose(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.mp_face.process(rgb)
        if not results.multi_face_landmarks:
            return None, None, None

        mesh = results.multi_face_landmarks[0].landmark
        image_points = np.array([
            [mesh[i].x * frame.shape[1], mesh[i].y * frame.shape[0]] for i in self.image_points_indices
        ], dtype="double")

        model_points = np.array([
            (0.0, 0.0, 0.0),
            (0.0, -63.6, -12.5),
            (-43.3, 32.7, -26.0),
            (43.3, 32.7, -26.0),
            (-28.9, -28.9, -24.1),
            (28.9, -28.9, -24.1)
        ])

        size = frame.shape
        focal_length = size[1]
        center = (size[1]/2, size[0]/2)
        camera_matrix = np.array([[focal_length,0,center[0]],[0,focal_length,center[1]],[0,0,1]], dtype="double")
        dist_coeffs = np.zeros((4,1))

        success, rotation_vector, translation_vector = cv2.solvePnP(
            model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )

        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        sy = np.sqrt(rotation_matrix[0,0] ** 2 + rotation_matrix[1,0] ** 2)
        pitch = np.arctan2(-rotation_matrix[2,0], sy)
        yaw = np.arctan2(rotation_matrix[1,0], rotation_matrix[0,0])
        roll = np.arctan2(rotation_matrix[2,1], rotation_matrix[2,2])

        return np.degrees(yaw), np.degrees(pitch), np.degrees(roll)
