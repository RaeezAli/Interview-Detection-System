import cv2
import numpy as np
from collections import Counter

# MediaPipe new Tasks API for Python 3.13 compatibility
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# We'll use FaceLandmarker instead of deprecated FaceMesh solutions
# Download the model file first - we handle this below
import urllib.request
import os

MODEL_PATH = "face_landmarker.task"

# Auto download the model if not present
if not os.path.exists(MODEL_PATH):
    print("Downloading face landmarker model...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        MODEL_PATH
    )
    print("Model downloaded successfully.")

# Initialize FaceLandmarker
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=False,
    output_facial_transformation_matrixes=False,
    num_faces=1
)
face_landmarker = vision.FaceLandmarker.create_from_options(options)


def detect_gaze(frame):
    if frame is None:
        return {"gaze_direction": "No Frame", "eye_contact": False, "score": 0}

    # PERFORMANCE: Resize if too large
    if frame.shape[1] > 640:
        frame = cv2.resize(frame, (640, 480))

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    results = face_landmarker.detect(mp_image)

    if not results.face_landmarks:
        return {
            "gaze_direction": "No Face Detected",
            "eye_contact": False,
            "score": 0
        }

    face_landmarks = results.face_landmarks[0]
    img_h, img_w, _ = frame.shape

    def get_coords(idx):
        lm = face_landmarks[idx]
        return lm.x * img_w, lm.y * img_h

    # Left eye corners: 33, 133 | Left iris: 468
    # Right eye corners: 362, 263 | Right iris: 473
    l_iris = get_coords(468)
    l_left = get_coords(33)
    l_right = get_coords(133)

    r_iris = get_coords(473)
    r_left = get_coords(362)
    r_right = get_coords(263)

    l_ratio = (l_iris[0] - l_left[0]) / (l_right[0] - l_left[0] + 1e-6)
    r_ratio = (r_iris[0] - r_left[0]) / (r_right[0] - r_left[0] + 1e-6)
    avg_ratio = (l_ratio + r_ratio) / 2

    avg_y_iris = (l_iris[1] + r_iris[1]) / 2
    avg_y_corners = ((l_left[1] + l_right[1]) / 2 + (r_left[1] + r_right[1]) / 2) / 2
    vertical_diff = (avg_y_iris - avg_y_corners) / img_h

    gaze_direction = "Looking at Camera"
    eye_contact = True
    score = 100

    if avg_ratio < 0.35:
        gaze_direction = "Looking Left"
        eye_contact = False
    elif avg_ratio > 0.65:
        gaze_direction = "Looking Right"
        eye_contact = False
    elif vertical_diff < -0.005:
        gaze_direction = "Looking Up"
        eye_contact = False
    elif vertical_diff > 0.005:
        gaze_direction = "Looking Down"
        eye_contact = False

    if not eye_contact:
        if (0.30 <= avg_ratio < 0.35) or (0.65 < avg_ratio <= 0.70):
            score = 60
        else:
            score = 20

    return {
        "gaze_direction": gaze_direction,
        "eye_contact": eye_contact,
        "score": score,
        "left_iris_ratio": round(l_ratio, 2),
        "right_iris_ratio": round(r_ratio, 2),
        "iris_coords": {"left": l_iris, "right": r_iris}
    }


def get_eye_contact_summary(gaze_results_list):
    if not gaze_results_list:
        return {"error": "No data to analyze"}

    total_frames = len(gaze_results_list)
    eye_contact_frames = sum(1 for r in gaze_results_list if r.get("eye_contact"))
    eye_contact_percentage = (eye_contact_frames / total_frames) * 100 if total_frames > 0 else 0
    avg_score = np.mean([r.get("score", 0) for r in gaze_results_list])
    directions = [r.get("gaze_direction") for r in gaze_results_list]
    most_common_direction = Counter(directions).most_common(1)[0][0]

    if eye_contact_percentage >= 70:
        feedback = "Good eye contact maintained throughout the interview."
    elif eye_contact_percentage >= 40:
        feedback = "Moderate eye contact, try to focus more on the camera."
    else:
        feedback = "Poor eye contact detected, practice looking directly at the camera."

    return {
        "eye_contact_percentage": round(eye_contact_percentage, 1),
        "average_score": int(avg_score),
        "most_common_direction": most_common_direction,
        "total_frames": total_frames,
        "eye_contact_frames": eye_contact_frames,
        "feedback": feedback
    }


def draw_gaze_overlay(frame, gaze_result):
    annotated_frame = frame.copy()

    if "iris_coords" in gaze_result:
        color = (0, 255, 0) if gaze_result["eye_contact"] else (0, 0, 255)
        l_iris = gaze_result["iris_coords"]["left"]
        r_iris = gaze_result["iris_coords"]["right"]
        cv2.circle(annotated_frame, (int(l_iris[0]), int(l_iris[1])), 3, color, -1)
        cv2.circle(annotated_frame, (int(r_iris[0]), int(r_iris[1])), 3, color, -1)

    label = f"Gaze: {gaze_result['gaze_direction']}"
    text_color = (0, 255, 0) if gaze_result["eye_contact"] else (0, 0, 255)
    cv2.putText(annotated_frame, label, (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2, cv2.LINE_AA)

    return annotated_frame