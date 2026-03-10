from deepface import DeepFace
import cv2
import numpy as np
from collections import Counter

# DeepFace does not need initialization, it is called directly
# Do NOT try to create a DeepFace() instance - it is used as a static class

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

def default_emotion_result():
    """Returns a default neutral emotion result for fallbacks."""
    return {
        'dominant_emotion': 'neutral',
        'interview_label': 'Calm & Composed',
        'emotions': {},
        'score': 85, # Neutral is good in interviews
        'face_confidence': 0
    }

def detect_emotion(frame):
    """
    Detects facial emotions using DeepFace and returns detailed results.
    Optimized for interview context: neutral is treated as positive.
    """
    try:
        if frame is None:
            return default_emotion_result()
        
        # PERFORMANCE: Resize locally for even faster analysis if not already resized
        small_frame = cv2.resize(frame, (320, 240))
        
        result = DeepFace.analyze(
            img_path=small_frame,
            actions=['emotion'],
            enforce_detection=False,
            detector_backend='opencv',
            silent=True
        )
        
        if isinstance(result, list):
            result = result[0]
        
        emotions = result.get('emotion', {})
        dominant = result.get('dominant_emotion', 'neutral')
        
        # Improved interview emotion mapping
        # Key fix: treat neutral as positive/composed in interview context
        emotion_label_map = {
            'happy': 'Confident & Friendly',
            'neutral': 'Calm & Composed',
            'surprise': 'Engaged',
            'sad': 'Low Energy',
            'angry': 'Stressed',
            'fear': 'Nervous',
            'disgust': 'Uncomfortable'
        }
        
        # Improved scoring - give neutral a better score
        score_map = {
            'happy': 95,
            'neutral': 85,
            'surprise': 75,
            'sad': 45,
            'angry': 35,
            'fear': 30,
            'disgust': 25
        }
        
        # IMPORTANT FIX: Override misdetections of 'sad' or 'fear' 
        # when happy+neutral combined indicate a generally positive state.
        positive_score = emotions.get('happy', 0) + emotions.get('neutral', 0)
        if positive_score > 60 and dominant in ['sad', 'fear', 'disgust']:
            dominant = 'neutral'
        
        interview_label = emotion_label_map.get(dominant, 'Calm & Composed')
        score = score_map.get(dominant, 80)
        
        return {
            'dominant_emotion': dominant,
            'interview_label': interview_label,
            'emotions': emotions,
            'score': score,
            # Region info for overlay
            "box": [result.get('region', {}).get(k, 0) for k in ['x', 'y', 'w', 'h']],
            'face_confidence': result.get('face_confidence', 0.9)
        }
    
    except Exception as e:
        print(f"Emotion detection error: {e}")
        return default_emotion_result()

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
    
    # Calculate percentage distribution
    distribution = {}
    for label, count in Counter(r["interview_label"] for r in valid_results).items():
        distribution[label] = round((count / total_frames) * 100, 1)

    # Calculate average score with smoothing logic
    # Give more weight to consistent performance and ignore outlier low scores
    scores = [r.get('score', 80) for r in valid_results]
    scores.sort()
    # Trim outliers (bottom 10% and top 10% for representative average)
    trim = max(1, len(scores) // 10)
    trimmed_scores = scores[trim:-trim] if len(scores) > 10 else scores
    avg_score = int(np.mean(trimmed_scores))
    
    # Updated label mapping for overall summary (using our refined map)
    label_map = {
        'happy': 'Confident & Friendly',
        'neutral': 'Calm & Composed',
        'surprise': 'Engaged',
        'sad': 'Low Energy',
        'angry': 'Stressed',
        'fear': 'Nervous',
        'disgust': 'Uncomfortable'
    }

    # Feedback logic
    feedback_map = {
        "happy": "You appeared confident and friendly throughout the interview. Great job!",
        "neutral": "You maintained a calm and composed expression. This projects stability and professionalism.",
        "fear": "You appeared slightly nervous. Try to relax your facial muscles and breathe steadily.",
        "sad": "Your energy level appeared low. Try to show more enthusiasm for the role.",
        "angry": "You appeared somewhat stressed. Focus on maintaining a relaxed, approachable look.",
        "surprise": "You appeared highly engaged and attentive. Good energy!",
        "disgust": "Some expressions appeared uncomfortable. Practice maintaining a neutral, professional mask."
    }
    
    feedback = feedback_map.get(dominant_overall, "You maintained a professional demeanor with a varied emotional range.")

    return {
        "dominant_emotion_overall": dominant_overall,
        "interview_label_overall": label_map.get(dominant_overall, "Varied"),
        "average_score": avg_score,
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
