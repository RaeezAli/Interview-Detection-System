import cv2
import numpy as np
from fer import FER
from collections import Counter

# Initialize the FER detector
# mtcnn=True provides better accuracy but is slightly slower
detector = FER(mtcnn=True)

# Mapping standard FER emotions to interview-friendly labels
EMOTION_MAP = {
    "happy": "Confident & Friendly",
    "neutral": "Calm & Composed",
    "surprise": "Engaged",
    "sad": "Low Energy",
    "angry": "Stressed",
    "fear": "Nervous",
    "disgust": "Uncomfortable"
}

# Mapping emotions to performance scores
EMOTION_SCORES = {
    "happy": 95,
    "neutral": 80,
    "surprise": 70,
    "sad": 40,
    "angry": 30,
    "fear": 25,
    "disgust": 20
}

def get_emotion_color(emotion):
    """Returns a BGR color tuple for a given emotion."""
    colors = {
        "happy": (0, 255, 0),        # Green
        "neutral": (255, 255, 0),    # Cyan
        "surprise": (0, 255, 255),   # Yellow
        "fear": (0, 0, 255),         # Red
        "angry": (0, 0, 200),        # Dark Red
        "sad": (255, 0, 0),          # Blue
        "disgust": (0, 128, 255),    # Orange
    }
    return colors.get(emotion, (255, 255, 255)) # Default White

def detect_emotion(frame):
    """
    Detects facial emotions using FER and returns detailed results.
    """
    if frame is None:
        return {
            "dominant_emotion": "No Frame",
            "emotions": {},
            "score": 0,
            "interview_label": "Unknown"
        }

    # FER detects emotions and returns a list of dictionaries (one for each face)
    results = detector.detect_emotions(frame)

    if not results:
        return {
            "dominant_emotion": "No Face Detected",
            "emotions": {},
            "score": 0,
            "interview_label": "Unknown"
        }

    # Extract info for the first (primary) face detected
    first_face = results[0]
    box = first_face["box"] # [x, y, w, h]
    emotions = first_face["emotions"]
    
    # Get dominant emotion using simple max
    dominant_emotion = max(emotions, key=emotions.get)
    
    # Map to interview labels
    interview_label = EMOTION_MAP.get(dominant_emotion, "Analyzing...")
    
    # Calculate score
    score = EMOTION_SCORES.get(dominant_emotion, 0)
    
    return {
        "dominant_emotion": dominant_emotion,
        "interview_label": interview_label,
        "emotions": emotions,
        "score": score,
        "box": box,
        "face_confidence": 1.0 # FER doesn't give box confidence directly in same return
    }

def get_emotion_summary(emotion_results_list):
    """
    Aggregates emotion results into a session summary.
    """
    if not emotion_results_list:
        return {"error": "No data to analyze"}

    valid_results = [r for r in emotion_results_list if r.get("dominant_emotion") != "No Face Detected"]
    
    if not valid_results:
        return {"error": "No faces detected in the provided timeframe."}

    total_frames = len(valid_results)
    
    # Count occurrences of dominate emotions
    emotion_counts = Counter(r["dominant_emotion"] for r in valid_results)
    dominant_overall = emotion_counts.most_common(1)[0][0]
    
    # Calculate average score
    avg_score = np.mean([r["score"] for r in valid_results])
    
    # Calculate percentage distribution
    distribution = {}
    for emotion, count in Counter(r["interview_label"] for r in valid_results).items():
        distribution[emotion] = round((count / total_frames) * 100, 1)

    # Feedback logic
    feedback_map = {
        "happy": "You appeared confident and friendly throughout the interview. Great job!",
        "neutral": "You maintained a calm and composed expression. Try smiling more to appear friendlier.",
        "fear": "You appeared nervous during the interview. Practice relaxation techniques before your next interview.",
        "sad": "You appeared low energy during the interview. Try to show more enthusiasm.",
        "angry": "You appeared stressed or tense. Try to relax your facial muscles during the interview.",
        "surprise": "You appeared engaged and attentive. Good energy overall.",
        "disgust": "You appeared uncomfortable at times. Try to maintain a neutral or positive expression."
    }
    
    feedback = feedback_map.get(dominant_overall, "The analysis shows a varied emotional range.")

    return {
        "dominant_emotion_overall": dominant_overall,
        "interview_label_overall": EMOTION_MAP.get(dominant_overall, "Varied"),
        "average_score": int(avg_score),
        "emotion_distribution": distribution,
        "total_frames": len(emotion_results_list),
        "feedback": feedback
    }

def draw_emotion_overlay(frame, emotion_result):
    """
    Draws face bounding box and emotion labels on the frame.
    """
    if not emotion_result or emotion_result.get("dominant_emotion") == "No Face Detected":
        return frame

    annotated_frame = frame.copy()
    box = emotion_result.get("box")
    dominant = emotion_result.get("dominant_emotion")
    label = emotion_result.get("interview_label")
    score = emotion_result.get("score")
    emotions = emotion_result.get("emotions", {})

    if box:
        x, y, w, h = box
        color = get_emotion_color(dominant)
        
        # Draw Bounding Box
        cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), color, 2)
        
        # Label Background
        cv2.rectangle(annotated_frame, (x, y - 35), (x + w, y), color, -1)
        cv2.putText(annotated_frame, f"{label} ({score})", (x + 5, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    # Mini-dashboard: Top 3 emotions
    if emotions:
        top_3 = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]
        start_y = frame.shape[0] - 80
        
        for i, (emo, val) in enumerate(top_3):
            display_text = f"{emo.capitalize()}: {int(val * 100)}%"
            cv2.putText(annotated_frame, display_text, (20, start_y + (i * 25)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return annotated_frame
