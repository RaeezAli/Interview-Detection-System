import cv2
import numpy as np
import math
from collections import Counter
import mediapipe.python.solutions.pose as pose_module
import mediapipe.python.solutions.drawing_utils as drawing_utils_module

pose = pose_module.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def calculate_angle(a, b, c):
    """
    Calculates the angle at point b between lines ba and bc.
    Points are [x, y]. returns angle in degrees.
    """
    a = np.array(a) # Point A
    b = np.array(b) # Point B (vertex)
    c = np.array(c) # Point C

    radians = math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

def calculate_distance(point1, point2):
    """Calculates Euclidean distance between two [x, y] points."""
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def detect_posture(frame):
    """
    Detects posture quality using MediaPipe Pose.
    Checks for slouching, leaning, uneven shoulders, and head position.
    """
    if frame is None:
        return {"posture_label": "No Frame", "score": 0, "issues": [], "is_upright": False}

    # PERFORMANCE: Resize if too large
    if frame.shape[1] > 640:
        frame = cv2.resize(frame, (640, 480))

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)

    if not results.pose_landmarks:
        return {
            "posture_label": "No Person Detected",
            "score": 0,
            "issues": [],
            "is_upright": False
        }

    landmarks = results.pose_landmarks.landmark
    img_h, img_w, _ = frame.shape

    def get_coords(idx):
        return [landmarks[idx].x, landmarks[idx].y]

    # Required Landmarks
    l_shoulder = get_coords(11)
    r_shoulder = get_coords(12)
    l_ear = get_coords(7)
    r_ear = get_coords(8)
    l_hip = get_coords(23)
    r_hip = get_coords(24)
    nose = get_coords(0)

    issues = []

    # CHECK 1: Shoulder Level (Unevenness)
    shoulder_level_diff = abs(l_shoulder[1] - r_shoulder[1])
    if shoulder_level_diff > 0.05:
        issues.append("Uneven Shoulders")

    # CHECK 2: Slouching Detection (Ear-Shoulder-Hip Angle)
    # Using only the more visible side or average
    l_angle = calculate_angle(l_ear, l_shoulder, l_hip)
    r_angle = calculate_angle(r_ear, r_shoulder, r_hip)
    avg_angle = (l_angle + r_angle) / 2

    if avg_angle < 140:
        issues.append("Severe Slouching")
    elif avg_angle < 160:
        issues.append("Mild Slouching")

    # CHECK 3: Forward Head Posture (Ear vs Shoulder X-pos)
    # Ear should be roughly vertically aligned with shoulder
    ear_shoulder_x_diff = abs((l_ear[0] + r_ear[0])/2 - (l_shoulder[0] + r_shoulder[0])/2)
    if ear_shoulder_x_diff > 0.05:
        issues.append("Forward Head Posture")

    # CHECK 4: Leaning Detection
    sh_midpoint_x = (l_shoulder[0] + r_shoulder[0]) / 2
    hip_midpoint_x = (l_hip[0] + r_hip[0]) / 2
    leaning_diff = sh_midpoint_x - hip_midpoint_x

    if leaning_diff > 0.08:
        issues.append("Leaning Right")
    elif leaning_diff < -0.08:
        issues.append("Leaning Left")

    # CHECK 5: Camera Distance
    shoulder_width = calculate_distance(l_shoulder, r_shoulder)
    if shoulder_width < 0.2:
        issues.append("Too Far from Camera")
    elif shoulder_width > 0.8:
        issues.append("Too Close to Camera")

    # Scoring Logic
    num_issues = len(issues)
    score = 100
    if num_issues == 1: score = 75
    elif num_issues == 2: score = 55
    elif num_issues == 3: score = 35
    elif num_issues >= 4: score = 15

    # Posture Label
    if score >= 80: posture_label = "Excellent Posture"
    elif score >= 60: posture_label = "Good Posture"
    elif score >= 40: posture_label = "Fair Posture"
    else: posture_label = "Poor Posture"

    return {
        "posture_label": posture_label,
        "score": score,
        "issues": issues,
        "is_upright": score >= 60,
        "shoulder_angle_left": round(l_angle, 1),
        "shoulder_angle_right": round(r_angle, 1),
        "shoulder_level_diff": round(shoulder_level_diff, 3),
        "landmarks": {
            "l_shoulder": l_shoulder, "r_shoulder": r_shoulder,
            "l_ear": l_ear, "r_ear": r_ear,
            "l_hip": l_hip, "r_hip": r_hip
        }
    }

def get_posture_summary(posture_results_list):
    """Summarizes posture results over a session."""
    if not posture_results_list:
        return {"error": "No data"}

    valid_results = [r for r in posture_results_list if r["posture_label"] != "No Person Detected"]
    if not valid_results:
        return {"error": "No person detected during assessment."}

    avg_score = np.mean([r["score"] for r in valid_results])
    
    labels = [r["posture_label"] for r in valid_results]
    most_common_label = Counter(labels).most_common(1)[0][0]
    
    all_issues = []
    for r in valid_results:
        all_issues.extend(r["issues"])
    
    issues_counts = dict(Counter(all_issues))
    most_frequent_issue = Counter(all_issues).most_common(1)[0][0] if all_issues else "None"
    
    good_frames = sum(1 for r in valid_results if r["score"] >= 60)
    good_posture_percentage = (good_frames / len(valid_results)) * 100

    # Feedback Logic
    if avg_score >= 80:
        feedback = "Excellent posture throughout the interview. Well done!"
    elif avg_score >= 60:
        feedback = f"Generally good posture. Watch out for {most_frequent_issue}."
    elif avg_score >= 40:
        feedback = f"Fair posture detected. Focus on sitting upright and avoid {most_frequent_issue}."
    else:
        feedback = f"Poor posture detected. Practice sitting upright with your back straight before your next interview."

    return {
        "average_score": int(avg_score),
        "most_common_label": most_common_label,
        "good_posture_percentage": round(good_posture_percentage, 1),
        "issues_detected": issues_counts,
        "most_frequent_issue": most_frequent_issue,
        "total_frames": len(posture_results_list),
        "feedback": feedback
    }

def draw_posture_overlay(frame, posture_result):
    """Draws posture landmarks and labels on the frame."""
    if posture_result["posture_label"] == "No Person Detected":
        return frame

    annotated_frame = frame.copy()
    h, w, _ = frame.shape
    
    score = posture_result["score"]
    if score >= 60: color = (0, 255, 0)      # Green
    elif score >= 40: color = (0, 255, 255)  # Yellow
    else: color = (0, 0, 255)               # Red

    # Draw specific landmarks
    if "landmarks" in posture_result:
        for name, pt in posture_result["landmarks"].items():
            cv2.circle(annotated_frame, (int(pt[0]*w), int(pt[1]*h)), 5, color, -1)

    # Label
    cv2.putText(annotated_frame, f"Posture: {posture_result['posture_label']}", (30, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    # Draw Issues
    for i, issue in enumerate(posture_result["issues"]):
        cv2.putText(annotated_frame, f"- {issue}", (30, 130 + (i * 25)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

    return annotated_frame
