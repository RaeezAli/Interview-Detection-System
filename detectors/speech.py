import re
import math
import time
import numpy as np
import whisper
from collections import Counter

# Load Whisper model (use "base" for speed; switch to "small" or "medium" for better accuracy)
model = whisper.load_model("base")

# Comprehensive filler words list
FILLER_WORDS = [
    "uh", "um", "like", "you know", "so", "actually",
    "basically", "literally", "right", "okay", "well",
    "kind of", "sort of", "i mean", "you see", "honestly",
    "seriously", "whatever", "anyway", "hmm", "er"
]


def transcribe_audio(audio_path):
    """
    Transcribes an audio/video file using OpenAI Whisper.
    Returns full text, segments with timestamps, detected language, and duration.
    """
    try:
        result = model.transcribe(audio_path, verbose=False)
        
        # Total duration from last segment's end time
        duration = result["segments"][-1]["end"] if result["segments"] else 0

        return {
            "text": result.get("text", "").strip(),
            "segments": result.get("segments", []),
            "language": result.get("language", "en"),
            "duration": duration
        }
    except Exception as e:
        return {
            "text": "",
            "segments": [],
            "language": "unknown",
            "duration": 0,
            "error": f"Transcription failed: {str(e)}"
        }


def detect_filler_words(transcription_text, segments):
    """
    Detects filler words in transcribed text using regex.
    Returns word counts, timestamps, and a filler score.
    """
    text_lower = transcription_text.lower()
    filler_counts = {}
    filler_timestamps = {}

    for filler in FILLER_WORDS:
        # Use word boundary matching for single words, phrase matching for multi-word fillers 
        pattern = r'\b' + re.escape(filler) + r'\b'
        matches = re.findall(pattern, text_lower)
        
        if matches:
            filler_counts[filler] = len(matches)
            
            # Find timestamps for each occurrence in segments
            timestamps = []
            for seg in segments:
                seg_text = seg.get("text", "").lower()
                if re.search(pattern, seg_text):
                    timestamps.append(round(seg.get("start", 0), 1))
            filler_timestamps[filler] = timestamps

    total = sum(filler_counts.values())

    # Filler score
    if total == 0: filler_score = 100
    elif total <= 3: filler_score = 90
    elif total <= 7: filler_score = 75
    elif total <= 12: filler_score = 55
    elif total <= 20: filler_score = 35
    else: filler_score = 15

    return {
        "filler_word_counts": filler_counts,
        "total_filler_count": total,
        "filler_timestamps": filler_timestamps,
        "filler_score": filler_score
    }


def analyze_speech_pace(segments, total_duration):
    """
    Calculates speech pace (WPM), classifies it, and detects long pauses.
    """
    if total_duration <= 0 or not segments:
        return {
            "words_per_minute": 0, "pace_label": "Unavailable",
            "pace_score": 0, "total_words": 0,
            "long_pauses": [], "long_pause_count": 0,
            "feedback": "Unable to analyze pace — no audio segments."
        }

    # Count total words across all segments
    total_words = sum(len(seg.get("text", "").split()) for seg in segments)
    wpm = math.ceil((total_words / total_duration) * 60)

    # Pace label and score
    if wpm < 100:
        pace_label, pace_score = "Too Slow", 40
        feedback = "Your speech was too slow. This can make you appear less confident or engaged."
    elif wpm <= 130:
        pace_label, pace_score = "Slightly Slow", 75
        feedback = "Your speech was slightly slow. Try to maintain a more natural conversational pace."
    elif wpm <= 170:
        pace_label, pace_score = "Normal Pace", 100
        feedback = "Your speech pace was natural and easy to follow."
    elif wpm <= 200:
        pace_label, pace_score = "Slightly Fast", 75
        feedback = "You spoke slightly fast at times. Try to slow down for clarity."
    else:
        pace_label, pace_score = "Too Fast", 40
        feedback = "You spoke too fast throughout the interview. Slow down so the interviewer can follow you clearly."

    # Detect long pauses (gaps > 3 seconds between consecutive segments)
    long_pauses = []
    for i in range(1, len(segments)):
        gap = segments[i]["start"] - segments[i - 1]["end"]
        if gap > 3.0:
            long_pauses.append({
                "timestamp": round(segments[i - 1]["end"], 1),
                "duration": round(gap, 1)
            })

    return {
        "words_per_minute": wpm,
        "pace_label": pace_label,
        "pace_score": pace_score,
        "total_words": total_words,
        "long_pauses": long_pauses,
        "long_pause_count": len(long_pauses),
        "feedback": feedback
    }


def analyze_speech_clarity(transcription_text):
    """
    Calculates a speech clarity score based on vocabulary diversity and sentence length.
    """
    if not transcription_text.strip():
        return {
            "clarity_score": 0,
            "average_sentence_length": 0,
            "vocabulary_diversity": 0,
            "feedback": "No transcription available to assess clarity."
        }

    # Sentence-level analysis
    sentences = [s.strip() for s in re.split(r'[.!?]+', transcription_text) if s.strip()]
    sentence_lengths = [len(s.split()) for s in sentences]
    avg_sentence_length = np.mean(sentence_lengths) if sentence_lengths else 0

    # Vocabulary diversity (type-token ratio)
    all_words = transcription_text.lower().split()
    unique_words = set(all_words)
    vocab_diversity = len(unique_words) / len(all_words) if all_words else 0

    # Score: ideal sentence = 10-20 words, vocab diversity > 0.5 is good
    sentence_score = 100 if 8 <= avg_sentence_length <= 20 else 70 if 5 <= avg_sentence_length <= 25 else 40
    vocab_score = 100 if vocab_diversity >= 0.5 else 75 if vocab_diversity >= 0.35 else 50
    clarity_score = int((sentence_score + vocab_score) / 2)

    if clarity_score >= 80:
        feedback = "Your speech was clear and well structured."
    elif clarity_score >= 60:
        feedback = "Your speech was fairly clear. Try to vary your vocabulary a bit more."
    else:
        feedback = "Your speech clarity needs improvement. Aim for shorter, more structured sentences."

    return {
        "clarity_score": clarity_score,
        "average_sentence_length": round(avg_sentence_length, 1),
        "vocabulary_diversity": round(vocab_diversity, 2),
        "feedback": feedback
    }


def analyze_full_speech(audio_path):
    """
    Orchestrates the full speech analysis pipeline.
    Transcribes the audio, then analyzes filler words, pace, and clarity.
    """
    # Step 1: Transcription
    transcription = transcribe_audio(audio_path)
    
    if "error" in transcription:
        return {"error": transcription["error"]}

    text = transcription["text"]
    segments = transcription["segments"]
    duration = transcription["duration"]

    # Step 2: Individual Analysis Modules
    filler_analysis = detect_filler_words(text, segments)
    pace_analysis = analyze_speech_pace(segments, duration)
    clarity_analysis = analyze_speech_clarity(text)

    # Step 3: Weighted Overall Score
    filler_score = filler_analysis["filler_score"]
    pace_score = pace_analysis["pace_score"]
    clarity_score = clarity_analysis["clarity_score"]

    overall_score = int(
        (filler_score * 0.30) +
        (pace_score * 0.40) +
        (clarity_score * 0.30)
    )

    # Overall Feedback
    if overall_score >= 80:
        overall_feedback = "Excellent speech performance. Clear, well paced, and professional."
    elif overall_score >= 60:
        overall_feedback = "Good speech performance with minor areas to improve."
    elif overall_score >= 40:
        overall_feedback = "Fair speech performance. Focus on reducing filler words and maintaining a steady pace."
    else:
        overall_feedback = "Speech needs significant improvement. Practice speaking clearly and reducing filler words."

    return {
        "transcription": text,
        "overall_speech_score": overall_score,
        "filler_analysis": filler_analysis,
        "pace_analysis": pace_analysis,
        "clarity_analysis": clarity_analysis,
        "feedback": overall_feedback
    }
