import numpy as np
import datetime
from collections import Counter

# ──────────────────────────────────────────────
# SCORING WEIGHTS
# Adjust these values to change scoring emphasis.
# All weights must sum to 1.0.
# ──────────────────────────────────────────────
WEIGHTS = {
    "eye_contact":  0.25,
    "emotion":      0.25,
    "posture":      0.20,
    "speech_pace":  0.15,
    "filler_words": 0.15,
}

# Priority ordering for sorting recommendations
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


# ──────────────────────────────────────────────────────────────
# 1. WEIGHTED CONFIDENCE SCORE
# ──────────────────────────────────────────────────────────────
def calculate_confidence_score(gaze_summary, emotion_summary, posture_summary, speech_analysis):
    """
    Calculates the overall interview confidence score using weighted sub-scores
    from all four detector modules.
    """
    eye_contact_score  = gaze_summary.get("average_score", 0)
    emotion_score      = emotion_summary.get("average_score", 0)
    posture_score      = posture_summary.get("average_score", 0)
    speech_pace_score  = speech_analysis.get("pace_analysis", {}).get("pace_score", 0)
    filler_score       = speech_analysis.get("filler_analysis", {}).get("filler_score", 0)

    overall_score = round(
        eye_contact_score  * WEIGHTS["eye_contact"]  +
        emotion_score      * WEIGHTS["emotion"]       +
        posture_score      * WEIGHTS["posture"]       +
        speech_pace_score  * WEIGHTS["speech_pace"]   +
        filler_score       * WEIGHTS["filler_words"],
        2
    )

    # Performance Label
    if overall_score >= 90:   performance_label = "Outstanding Performance"
    elif overall_score >= 75: performance_label = "Strong Performance"
    elif overall_score >= 60: performance_label = "Good Performance"
    elif overall_score >= 45: performance_label = "Fair Performance"
    elif overall_score >= 30: performance_label = "Needs Improvement"
    else:                     performance_label = "Significant Improvement Needed"

    # Performance Color for Frontend
    if overall_score >= 75:   performance_color = "green"
    elif overall_score >= 45: performance_color = "yellow"
    else:                     performance_color = "red"

    return {
        "overall_score": overall_score,
        "performance_label": performance_label,
        "performance_color": performance_color,
        "individual_scores": {
            "eye_contact":  round(eye_contact_score, 2),
            "emotion":      round(emotion_score, 2),
            "posture":      round(posture_score, 2),
            "speech_pace":  round(speech_pace_score, 2),
            "filler_words": round(filler_score, 2),
        },
        "weights_used": WEIGHTS
    }


# ──────────────────────────────────────────────────────────────
# 2. PERSONALIZED RECOMMENDATIONS
# ──────────────────────────────────────────────────────────────
def generate_recommendations(gaze_summary, emotion_summary, posture_summary, speech_analysis, overall_score):
    """
    Generates personalized AI recommendations for each performance category.
    Returns a list sorted by priority (High → Medium → Low).
    """
    recommendations = []

    # ── Eye Contact ────────────────────────────────────────────
    gaze_score = gaze_summary.get("average_score", 0)
    if gaze_score < 40:
        rec = {
            "category": "Eye Contact", "icon": "EYE",
            "title": "Improve Eye Contact", "priority": "High",
            "description": (
                "Your eye contact was poor during the interview. Practice looking directly at the camera lens "
                "as if it were the interviewer's eyes. Place a sticky note next to your camera as a reminder."
            )
        }
    elif gaze_score <= 70:
        rec = {
            "category": "Eye Contact", "icon": "EYE",
            "title": "Increase Eye Contact Consistency", "priority": "Medium",
            "description": (
                "Your eye contact was inconsistent. Try to focus on the camera more consistently, "
                "especially when answering important questions."
            )
        }
    else:
        rec = {
            "category": "Eye Contact", "icon": "EYE",
            "title": "Great Eye Contact", "priority": "Low",
            "description": "Good eye contact overall. Keep maintaining this habit in future interviews."
        }
    recommendations.append(rec)

    # ── Emotion ────────────────────────────────────────────────
    dominant_emotion = emotion_summary.get("dominant_emotion_overall", "neutral")
    if dominant_emotion in ("fear", "angry"):
        rec = {
            "category": "Expression", "icon": "FACE",
            "title": "Manage Nervousness", "priority": "High",
            "description": (
                "You appeared nervous or stressed. Practice deep breathing before interviews and "
                "remind yourself of your achievements to boost your confidence."
            )
        }
    elif dominant_emotion == "sad":
        rec = {
            "category": "Expression", "icon": "FACE",
            "title": "Increase Energy and Enthusiasm", "priority": "Medium",
            "description": (
                "You appeared low energy. Show more enthusiasm by smiling naturally "
                "and speaking with energy about your experiences."
            )
        }
    elif dominant_emotion == "neutral":
        rec = {
            "category": "Expression", "icon": "FACE",
            "title": "Show More Positive Expressions", "priority": "Low",
            "description": (
                "You were calm but try to show more positive emotions. "
                "A genuine smile can make a great impression on interviewers."
            )
        }
    else:
        rec = {
            "category": "Expression", "icon": "FACE",
            "title": "Excellent Positive Energy", "priority": "Low",
            "description": "Great positive energy throughout. Keep this up in future interviews."
        }
    recommendations.append(rec)

    # ── Posture ────────────────────────────────────────────────
    posture_issue = posture_summary.get("most_frequent_issue", "None")
    if posture_issue == "Severe Slouching":
        rec = {
            "category": "Posture", "icon": "BODY",
            "title": "Fix Severe Slouching", "priority": "High",
            "description": (
                "Severe slouching was detected. Sit at the edge of your chair with your back straight "
                "and shoulders back. Consider posture exercises before interviews."
            )
        }
    elif posture_issue == "Mild Slouching":
        rec = {
            "category": "Posture", "icon": "BODY",
            "title": "Correct Mild Slouching", "priority": "Medium",
            "description": "Mild slouching was detected. Be mindful of your back position and try to sit upright throughout."
        }
    elif posture_issue == "Forward Head Posture":
        rec = {
            "category": "Posture", "icon": "BODY",
            "title": "Correct Head Position", "priority": "Medium",
            "description": "Forward head posture was detected. Pull your chin back slightly and align your ears over your shoulders."
        }
    elif posture_issue in ("Leaning Left", "Leaning Right"):
        rec = {
            "category": "Posture", "icon": "BODY",
            "title": "Sit Centered", "priority": "Low",
            "description": "You were leaning to one side at times. Distribute your weight evenly and sit centered."
        }
    else:
        rec = {
            "category": "Posture", "icon": "BODY",
            "title": "Excellent Posture", "priority": "Low",
            "description": "Excellent posture maintained. Keep this professional body language in future interviews."
        }
    recommendations.append(rec)

    # ── Speech Pace ────────────────────────────────────────────
    pace_label = speech_analysis.get("pace_analysis", {}).get("pace_label", "Normal Pace")
    if pace_label == "Too Fast":
        rec = {
            "category": "Speech Pace", "icon": "MIC",
            "title": "Slow Down Your Speech", "priority": "High",
            "description": (
                "You spoke too quickly, which can make it hard for interviewers to follow. "
                "Pause between sentences and aim for 130–170 words per minute."
            )
        }
    elif pace_label == "Too Slow":
        rec = {
            "category": "Speech Pace", "icon": "MIC",
            "title": "Pick Up Your Speaking Pace", "priority": "High",
            "description": (
                "Your speech was too slow, which can appear as a lack of confidence. "
                "Practice speaking at a more natural conversational pace."
            )
        }
    elif pace_label in ("Slightly Fast", "Slightly Slow"):
        rec = {
            "category": "Speech Pace", "icon": "MIC",
            "title": "Calibrate Your Speed", "priority": "Medium",
            "description": "Record yourself speaking and listen back to calibrate your natural pace."
        }
    else:
        rec = {
            "category": "Speech Pace", "icon": "MIC",
            "title": "Great Speech Pace", "priority": "Low",
            "description": "Great speech pace maintained. Keep this natural rhythm in future interviews."
        }
    recommendations.append(rec)

    # ── Filler Words ───────────────────────────────────────────
    filler_count = speech_analysis.get("filler_analysis", {}).get("total_filler_count", 0)
    if filler_count > 20:
        rec = {
            "category": "Filler Words", "icon": "ABC",
            "title": "Reduce Filler Words Urgently", "priority": "High",
            "description": (
                "You used a high number of filler words like 'uh', 'um', and 'like'. "
                "Practice pausing silently instead of using fillers when gathering your thoughts."
            )
        }
    elif filler_count >= 8:
        rec = {
            "category": "Filler Words", "icon": "ABC",
            "title": "Reduce Filler Words", "priority": "Medium",
            "description": "You used a moderate number of filler words. Record practice interviews and consciously pause instead of saying 'uh' or 'um'."
        }
    elif filler_count >= 1:
        rec = {
            "category": "Filler Words", "icon": "ABC",
            "title": "Minor Filler Word Usage", "priority": "Low",
            "description": "You used very few filler words. Minor refinement will make your speech even more polished."
        }
    else:
        rec = {
            "category": "Filler Words", "icon": "ABC",
            "title": "Excellent — No Filler Words", "priority": "Low",
            "description": "Excellent! No significant filler words detected. Very professional speech."
        }
    recommendations.append(rec)

    # Sort by priority
    recommendations.sort(key=lambda r: PRIORITY_ORDER[r["priority"]])
    return recommendations


# ──────────────────────────────────────────────────────────────
# 3. TIMELINE DATA FOR CHART.JS
# ──────────────────────────────────────────────────────────────
def generate_timeline_data(gaze_results_list, emotion_results_list, posture_results_list, interval=30):
    """
    Samples frame-level results at every `interval` frames and generates
    timeline data formatted for Chart.js line charts.
    """
    total_frames = max(len(gaze_results_list), len(emotion_results_list), len(posture_results_list), 1)
    labels, gaze_data, emotion_data, posture_data, confidence_data = [], [], [], [], []

    for i in range(0, total_frames, interval):
        chunk_end = min(i + interval, total_frames)
        
        # Time label (seconds)
        t = i // 30  # assuming ~30fps
        label = f"{t // 60}:{str(t % 60).zfill(2)}"
        labels.append(label)

        # Average scores in the chunk
        g_scores = [r.get("score", 0) for r in gaze_results_list[i:chunk_end]]
        e_scores = [r.get("score", 0) for r in emotion_results_list[i:chunk_end]]
        p_scores = [r.get("score", 0) for r in posture_results_list[i:chunk_end]]

        avg_g = int(np.mean(g_scores)) if g_scores else 0
        avg_e = int(np.mean(e_scores)) if e_scores else 0
        avg_p = int(np.mean(p_scores)) if p_scores else 0
        avg_conf = int(np.mean([avg_g, avg_e, avg_p]))

        gaze_data.append(avg_g)
        emotion_data.append(avg_e)
        posture_data.append(avg_p)
        confidence_data.append(avg_conf)

    return {
        "labels": labels,
        "eye_contact_data": gaze_data,
        "emotion_data": emotion_data,
        "posture_data": posture_data,
        "confidence_data": confidence_data,
    }


# ──────────────────────────────────────────────────────────────
# 4. FULL REPORT GENERATOR (Main Orchestrator)
# ──────────────────────────────────────────────────────────────
def generate_full_report(
    gaze_summary, emotion_summary, posture_summary, speech_analysis,
    gaze_results_list, emotion_results_list, posture_results_list,
    interview_duration
):
    """
    Orchestrates all sub-modules to produce the complete interview report dictionary,
    ready to be passed to report.html.
    """
    # 1. Confidence Score
    score_data = calculate_confidence_score(
        gaze_summary, emotion_summary, posture_summary, speech_analysis
    )
    overall_score = score_data["overall_score"]

    # 2. Recommendations
    recommendations = generate_recommendations(
        gaze_summary, emotion_summary, posture_summary, speech_analysis, overall_score
    )

    # 3. Timeline Data
    timeline_data = generate_timeline_data(
        gaze_results_list, emotion_results_list, posture_results_list
    )

    # 4. Metadata
    now = datetime.datetime.now()
    report_id = now.strftime("%Y%m%d%H%M%S")
    generated_at = now.strftime("%B %d, %Y at %I:%M %p")
    
    # Format duration as mm:ss
    dur_secs = int(interview_duration)
    duration_str = f"{dur_secs // 60:02}:{dur_secs % 60:02}"

    return {
        "overall": {
            "score": round(overall_score, 2),
            "performance_label": score_data["performance_label"],
            "performance_color": score_data["performance_color"],
        },
        "individual_scores": score_data["individual_scores"],
        "recommendations": recommendations,
        "timeline_data": timeline_data,
        "summaries": {
            "gaze": gaze_summary,
            "emotion": emotion_summary,
            "posture": posture_summary,
            "speech": speech_analysis,
        },
        "filler_word_details": speech_analysis.get("filler_analysis", {}),
        "transcription": speech_analysis.get("transcription", ""),
        "report_id": report_id,
        "generated_at": generated_at,
        "interview_duration": duration_str,
    }
