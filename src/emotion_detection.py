import cv2
import tensorflow as tf
import numpy as np

class EmotionDetector:
    def __init__(self, model_path):
        self.model = tf.keras.models.load_model(model_path)
        self.labels = ['Surprise', 'Fear', 'Disgust',
                       'Happy', 'Sadness', 'Anger', 'Neutral']

        print("Emotion model loaded. Input shape:", self.model.input_shape)

        # Smoothing buffer
        self.history = []

        # Simple face detector (FAST & STABLE)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def predict_emotion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return "No Face", 0.0

        x, y, w, h = faces[0]
        face = frame[y:y+h, x:x+w]

        face = cv2.resize(face, (128, 128))
        face = face / 255.0

        # 🔥 RGB INPUT (FIXED)
        face = np.expand_dims(face, axis=0)

        preds = self.model.predict(face, verbose=0)[0]
        idx = int(np.argmax(preds))
        conf = float(preds[idx])

        # --- SMOOTHING ---
        self.history.append(idx)
        if len(self.history) > 8:
            self.history.pop(0)

        final_idx = max(set(self.history), key=self.history.count)

        return self.labels[final_idx], conf
