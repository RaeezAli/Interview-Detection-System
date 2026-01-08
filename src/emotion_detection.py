import cv2
import tensorflow as tf
import numpy as np
from tensorflow.keras.utils import img_to_array
import mediapipe as mp

class EmotionDetector:
    def __init__(self, model_path):
        self.model = tf.keras.models.load_model(model_path)
        self.labels = ['Surprise', 'Fear', 'Disgust', 'Happy',
                       'Sadness', 'Anger', 'Neutral']
        self.mp_face = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)
    
    def predict_emotion(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.mp_face.process(rgb)

        if not results.detections:
            return "No Face", 0.0

        # Take first face
        bboxC = results.detections[0].location_data.relative_bounding_box
        h, w, _ = frame.shape
        x1 = max(0, int(bboxC.xmin * w))
        y1 = max(0, int(bboxC.ymin * h))
        x2 = min(w, int((bboxC.xmin + bboxC.width) * w))
        y2 = min(h, int((bboxC.ymin + bboxC.height) * h))

        face_crop = frame[y1:y2, x1:x2]
        face_resized = cv2.resize(face_crop, (128, 128))
        img = img_to_array(face_resized)
        img = np.expand_dims(img, axis=0)
        img = img / 255.0

        preds = self.model.predict(img, verbose=0)
        idx = np.argmax(preds)
        return self.labels[idx], float(preds[0][idx])