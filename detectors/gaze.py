import cv2
import mediapipe as mp
import numpy as np
from collections import Counter

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def detect_gaze(frame):
    """
    Detects gaze direction and eye contact score using MediaPipe Face Mesh.
    """
    if frame is None:
        return {"gaze_direction": "No Frame", "eye_contact": False, "score": 0}

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if not results.multi_face_landmarks:
        return {
            "gaze_direction": "No Face Detected",
            "eye_contact": False,
            "score": 0
        }

    face_landmarks = results.multi_face_landmarks[0].landmark
    img_h, img_w, _ = frame.shape

    # MediaPipe landmarks for eyes and irises
    # Left eye: corners 33, 133; Iris center 468
    # Right eye: corners 362, 263; Iris center 473

    def get_coords(idx):
        return face_landmarks[idx].x * img_w, face_landmarks[idx].y * img_h

    # Left eye
    l_iris = get_coords(468)
    l_left = get_coords(33)
    l_right = get_coords(133)
    
    # Right eye
    r_iris = get_coords(473)
    r_left = get_coords(362)
    r_right = get_coords(263)

    # Calculate horizontal ratio (0 = far left, 1 = far right)
    l_ratio = (l_iris[0] - l_left[0]) / (l_right[0] - l_left[0] + 1e-6)
    r_ratio = (r_iris[0] - r_left[0]) / (r_right[0] - r_left[0] + 1e-6)
    avg_ratio = (l_ratio + r_ratio) / 2

    # Calculate vertical ratio (relative to corners y-average)
    l_y_avg = (l_left[1] + l_right[1]) / 2
    r_y_avg = (r_left[1] + r_right[1]) / 2
    avg_y_iris = (l_iris[1] + r_iris[1]) / 2
    avg_y_corners = (l_y_avg + r_y_avg) / 2
    
    vertical_diff = (avg_y_iris - avg_y_corners) / img_h # normalized diff

    # Determine Gaze Direction
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

    # Score Logic
    if not eye_contact:
        # Check if slightly off
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
    """
    Provides a summary from a list of gaze result dictionaries.
    """
    if not gaze_results_list:
        return {"error": "No data to analyze"}

    total_frames = len(gaze_results_list)
    eye_contact_frames = sum(1 for r in gaze_results_list if r.get("eye_contact"))
    
    eye_contact_percentage = (eye_contact_frames / total_frames) * 100 if total_frames > 0 else 0
    avg_score = np.mean([r.get("score", 0) for r in gaze_results_list])
    
    directions = [r.get("gaze_direction") for r in gaze_results_list]
    most_common_direction = Counter(directions).most_common(1)[0][0]

    # Feedback Logic
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
    """
    Draws gaze info and iris points on the frame.
    """
    annotated_frame = frame.copy()
    
    # Draw iris landmarks
    if "iris_coords" in gaze_result:
        color = (0, 255, 0) if gaze_result["eye_contact"] else (0, 0, 255)
        
        l_iris = gaze_result["iris_coords"]["left"]
        r_iris = gaze_result["iris_coords"]["right"]
        
        cv2.circle(annotated_frame, (int(l_iris[0]), int(l_iris[1])), 3, color, -1)
        cv2.circle(annotated_frame, (int(r_iris[0]), int(r_iris[1])), 3, color, -1)

    # Draw Text Label
    label = f"Gaze: {gaze_result['gaze_direction']}"
    text_color = (0, 255, 0) if gaze_result["eye_contact"] else (0, 0, 255)
    
    cv2.putText(annotated_frame, label, (30, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2, cv2.LINE_AA)
    
    return annotated_frame
