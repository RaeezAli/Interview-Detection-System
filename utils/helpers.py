"""
utils/helpers.py
================
Shared utility library for the InterviewAI Flask application.
Contains video, file, data formatting, report, and color helper functions
used across app.py and all detector modules.
"""

import cv2
import numpy as np
import os
import base64
import json
import math
import re
import datetime
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
# 1. VIDEO UTILITIES
# ═══════════════════════════════════════════════════════════════

def extract_frames(video_path: str, every_n_frames: int = 3) -> dict | None:
    """
    Extracts every nth frame from a video file.

    Args:
        video_path (str): Absolute or relative path to the video file.
        every_n_frames (int): Sample interval — 1 means every frame, 3 means every 3rd.

    Returns:
        dict with keys: frames, total_frames, fps, duration_seconds,
                        width, height, sampled_frames.
        Returns None if the video cannot be opened.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[extract_frames] ERROR: Could not open video at '{video_path}'")
        return None

    total_frames  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps           = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width         = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height        = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_secs = total_frames / fps

    frames = []
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % every_n_frames == 0:
            frames.append(frame)
        frame_idx += 1

    cap.release()

    return {
        "frames":          frames,
        "total_frames":    total_frames,
        "fps":             fps,
        "duration_seconds": round(duration_secs, 2),
        "width":           width,
        "height":          height,
        "sampled_frames":  len(frames),
    }


def extract_audio_from_video(video_path: str, output_audio_path: str = None) -> str | None:
    """
    Extracts the audio track from a video file using ffmpeg.
    NOTE: ffmpeg must be installed and available on the system PATH.

    Args:
        video_path (str): Path to the input video.
        output_audio_path (str): Optional output path for the .wav file.
                                  Auto-generated if not provided.

    Returns:
        str: Path to the extracted audio file, or None on failure.
    """
    if output_audio_path is None:
        output_audio_path = os.path.splitext(video_path)[0] + ".wav"

    command = f'ffmpeg -i "{video_path}" -q:a 0 -map a "{output_audio_path}" -y'
    result = os.system(command)

    if result == 0 and os.path.exists(output_audio_path):
        return output_audio_path
    else:
        print(f"[extract_audio_from_video] ERROR: ffmpeg failed with code {result}")
        return None


def resize_frame(frame: np.ndarray, width: int = 640, height: int = 480) -> np.ndarray:
    """
    Resizes a frame to the specified dimensions using area interpolation.

    Args:
        frame (np.ndarray): Input frame from OpenCV.
        width (int): Target width in pixels.
        height (int): Target height in pixels.

    Returns:
        np.ndarray: Resized frame.
    """
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)


def frame_to_base64(frame: np.ndarray) -> str:
    """
    Encodes an OpenCV frame (numpy array) to a base64 data URI string.

    Args:
        frame (np.ndarray): Input frame.

    Returns:
        str: Data URI string in the format "data:image/jpeg;base64,<data>".
    """
    _, buffer = cv2.imencode(".jpg", frame)
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


def base64_to_frame(base64_string: str) -> np.ndarray | None:
    """
    Decodes a base64 image string to an OpenCV frame (numpy array).

    Args:
        base64_string (str): Base64 string (with or without data URI prefix).

    Returns:
        np.ndarray: Decoded frame, or None on failure.
    """
    try:
        # Strip data URI prefix if present
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        img_bytes = base64.b64decode(base64_string)
        np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"[base64_to_frame] ERROR: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# 2. FILE UTILITIES
# ═══════════════════════════════════════════════════════════════

def get_file_size_mb(file_path: str) -> float:
    """
    Returns the size of a file in megabytes.

    Args:
        file_path (str): Path to the file.

    Returns:
        float: File size in MB, rounded to 2 decimal places.
    """
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)


def cleanup_old_files(folder_path: str, max_age_hours: int = 24) -> int:
    """
    Deletes files in a folder that are older than max_age_hours.

    Args:
        folder_path (str): Path to the folder to clean up.
        max_age_hours (int): Maximum file age in hours before deletion.

    Returns:
        int: Number of files deleted.
    """
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(hours=max_age_hours)
    deleted = 0

    for file_path in Path(folder_path).iterdir():
        if not file_path.is_file():
            continue
        file_mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
        if file_mtime < cutoff:
            file_path.unlink()
            deleted += 1

    print(f"[cleanup_old_files] Deleted {deleted} file(s) from '{folder_path}'")
    return deleted


def generate_unique_filename(original_filename: str) -> str:
    """
    Creates a timestamped unique filename to prevent collisions.

    Args:
        original_filename (str): The original file name (e.g., "interview.mp4").

    Returns:
        str: Unique filename like "20260228_004937_interview.mp4".
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^\w.\-]", "_", original_filename)
    return f"{timestamp}_{safe_name}"


def ensure_folder_exists(folder_path: str) -> str:
    """
    Creates a folder (including all parents) if it doesn't exist.

    Args:
        folder_path (str): Desired folder path.

    Returns:
        str: The folder path (created or pre-existing).
    """
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    return folder_path


# ═══════════════════════════════════════════════════════════════
# 3. DATA FORMATTING UTILITIES
# ═══════════════════════════════════════════════════════════════

def format_duration(seconds: float | int) -> str:
    """
    Converts a duration in seconds to a human-readable string.

    Args:
        seconds (float | int): Duration in seconds.

    Returns:
        str: e.g., "45s", "5m 32s", or "1h 12m 45s".
    """
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_timestamp(seconds: float) -> str:
    """
    Converts seconds to a MM:SS timestamp string.

    Args:
        seconds (float): Time in seconds.

    Returns:
        str: Timestamp like "02:34".
    """
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02}:{secs:02}"


def score_to_grade(score: float) -> str:
    """
    Maps a 0–100 score to a letter grade.

    Args:
        score (float): Score between 0 and 100.

    Returns:
        str: Letter grade (A+, A, B+, B, C, D, F).
    """
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B+"
    if score >= 60: return "B"
    if score >= 50: return "C"
    if score >= 40: return "D"
    return "F"


def score_to_emoji(score: float) -> str:
    """
    Maps a 0–100 score to a performance emoji.

    Args:
        score (float): Score between 0 and 100.

    Returns:
        str: An emoji character.
    """
    if score >= 80: return "🌟"
    if score >= 60: return "👍"
    if score >= 40: return "😐"
    return "⚠️"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculates the percentage change between two values.

    Args:
        old_value (float): Previous value.
        new_value (float): Current value.

    Returns:
        float: Percentage change, or 0.0 if old_value is zero.
    """
    if old_value == 0:
        return 0.0
    return round(((new_value - old_value) / old_value) * 100, 1)


# ═══════════════════════════════════════════════════════════════
# 4. REPORT UTILITIES
# ═══════════════════════════════════════════════════════════════

def prepare_chart_data(report: dict) -> dict:
    """
    Formats the full report dict into Chart.js-ready data structures.

    Args:
        report (dict): Complete report from confidence_score.generate_full_report().

    Returns:
        dict: Chart data for radar, doughnut, line, and emotion pie charts.
    """
    scores = report.get("individual_scores", {})
    timeline = report.get("timeline_data", {})
    emotion_dist = report.get("summaries", {}).get("emotion", {}).get("emotion_distribution", {})

    score_values = [
        scores.get("eye_contact", 0),
        scores.get("emotion", 0),
        scores.get("posture", 0),
        scores.get("speech_pace", 0),
        scores.get("filler_words", 0),
    ]

    # Emotion pie chart colors
    EMOTION_COLORS = {
        "Confident & Friendly": "#4CAF50",
        "Calm & Composed":      "#2196F3",
        "Engaged":              "#00BCD4",
        "Nervous":              "#FF5722",
        "Stressed":             "#F44336",
        "Low Energy":           "#9E9E9E",
        "Uncomfortable":        "#FF9800",
    }
    emotion_labels = list(emotion_dist.keys())
    emotion_data   = list(emotion_dist.values())
    emotion_colors = [EMOTION_COLORS.get(e, "#9C27B0") for e in emotion_labels]

    return {
        "radar_chart": {
            "labels": ["Eye Contact", "Expression", "Posture", "Speech Pace", "Filler Words"],
            "data":   score_values,
        },
        "doughnut_chart": {
            "labels": ["Eye Contact", "Expression", "Posture", "Speech Pace", "Filler Words"],
            "data":   score_values,
            "colors": ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#F44336"],
        },
        "line_chart": {
            "labels": timeline.get("labels", []),
            "datasets": [
                {"label": "Eye Contact",  "data": timeline.get("eye_contact_data", []), "borderColor": "#4CAF50"},
                {"label": "Expression",   "data": timeline.get("emotion_data", []),     "borderColor": "#2196F3"},
                {"label": "Posture",      "data": timeline.get("posture_data", []),     "borderColor": "#FF9800"},
                {"label": "Confidence",   "data": timeline.get("confidence_data", []),  "borderColor": "#9C27B0"},
            ],
        },
        "emotion_pie_chart": {
            "labels": emotion_labels,
            "data":   emotion_data,
            "colors": emotion_colors,
        },
    }


def generate_report_summary_text(report: dict) -> str:
    """
    Generates a human-readable summary paragraph from the full report.

    Args:
        report (dict): Complete report from confidence_score.generate_full_report().

    Returns:
        str: A 3–5 sentence summary paragraph.
    """
    overall  = report.get("overall", {})
    scores   = report.get("individual_scores", {})
    recs     = report.get("recommendations", [])

    score = overall.get("score", 0)
    label = overall.get("performance_label", "N/A")

    if scores:
        best_key   = max(scores, key=scores.get)
        weakest_key = min(scores, key=scores.get)
        best_label   = best_key.replace("_", " ").title()
        weakest_label = weakest_key.replace("_", " ").title()
    else:
        best_label = weakest_label = "N/A"

    top_rec = recs[0]["title"] if recs else "continue practicing"

    return (
        f"You achieved an overall confidence score of {score}/100, reflecting a '{label}'. "
        f"Your strongest area was {best_label}, while {weakest_label} has the most room for growth. "
        f"Across the session, the AI identified key behavioral patterns and generated tailored suggestions. "
        f"Our top recommendation for your next interview is to '{top_rec}'. "
        f"Review the detailed breakdown below to understand each metric and accelerate your improvement."
    )


def validate_report_data(report: dict) -> tuple[bool, str | None]:
    """
    Validates that a report dictionary contains all required keys.

    Args:
        report (dict): Report dictionary to validate.

    Returns:
        tuple: (True, None) if valid, (False, error_message) if invalid.
    """
    required_keys = ["overall", "individual_scores", "summaries", "recommendations", "timeline_data"]
    for key in required_keys:
        if key not in report:
            return False, f"Missing key: {key}"
        if report[key] is None:
            return False, f"Key '{key}' is None"
    return True, None


# ═══════════════════════════════════════════════════════════════
# 5. COLOR UTILITIES
# ═══════════════════════════════════════════════════════════════

def score_to_color_hex(score: float) -> str:
    """
    Returns a hex color string based on the score range.

    Args:
        score (float): Score from 0 to 100.

    Returns:
        str: Hex color code ("#4CAF50", "#FF9800", or "#F44336").
    """
    if score >= 75: return "#4CAF50"   # Green
    if score >= 45: return "#FF9800"   # Orange
    return "#F44336"                   # Red


def score_to_color_rgb(score: float) -> tuple[int, int, int]:
    """
    Returns an RGB color tuple based on the score range.

    Args:
        score (float): Score from 0 to 100.

    Returns:
        tuple: (R, G, B) integer values.
    """
    if score >= 75: return (76, 175, 80)    # Green
    if score >= 45: return (255, 152, 0)    # Orange
    return (244, 67, 54)                    # Red
