"""
InterviewAI - Main Flask Application (Final Integrated Version)
Wires all detectors (Gaze, Emotion, Posture, Speech, Confidence Score)
into a fully working interview analysis pipeline with Socket.IO support.
"""

import os
import cv2
import time
import uuid
import json
import threading
import eventlet
import numpy as np
from flask import (Flask, render_template, request, redirect,
                   url_for, jsonify, session)
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

# Detector imports
from detectors.gaze import detect_gaze, get_eye_contact_summary, draw_gaze_overlay
from detectors.emotion import detect_emotion, get_emotion_summary, draw_emotion_overlay
from detectors.posture import detect_posture, get_posture_summary, draw_posture_overlay
from detectors.speech import analyze_full_speech
from detectors.confidence_score import generate_full_report

# Utility helpers
from utils.helpers import (
    extract_audio_from_video,
    prepare_chart_data,
    generate_report_summary_text,
    validate_report_data,
    ensure_folder_exists,
    cleanup_old_files,
    base64_to_frame
)

# Config
from config import Config

eventlet.monkey_patch()

# ──────────────────────────────────────────────
# APP CONFIGURATION
# ──────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config["UPLOAD_FOLDER"] = Config.UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}

socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

# Ensure required folders exist
ensure_folder_exists(app.config["UPLOAD_FOLDER"])

# ──────────────────────────────────────────────
# GLOBAL STATE
# ──────────────────────────────────────────────
analysis_store: dict = {}
live_analysis_running: bool = False
live_session_id: str = ""
live_results: dict = {
    "gaze_results": [],
    "emotion_results": [],
    "posture_results": []
}


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ──────────────────────────────────────────────
# BACKGROUND VIDEO PROCESSING THREAD
# ──────────────────────────────────────────────
def process_video_file(video_path: str, session_id: str):
    """
    Background thread: processes all frames through detectors,
    handles speech transcription, generates full report and stores it.
    """
    try:
        # Auto-cleanup old uploads before starting new analysis
        cleanup_old_files(app.config["UPLOAD_FOLDER"], max_age_hours=Config.CLEANUP_AFTER_HOURS)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            socketio.emit("analysis_error", {"error": "Could not open video file."})
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25

        gaze_results, emotion_results, posture_results = [], [], []
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            if frame_count % Config.ANALYSIS_FRAME_INTERVAL == 0:
                gaze_results.append(detect_gaze(frame))
                emotion_results.append(detect_emotion(frame))
                posture_results.append(detect_posture(frame))

            progress = round((frame_count / total_frames) * 100, 1) if total_frames > 0 else 0
            socketio.emit("analysis_progress", {
                "progress": progress,
                "current_step": f"Analyzing frame {frame_count} of {total_frames}",
                "session_id": session_id
            })
            eventlet.sleep(0.01)

        cap.release()

        # Summaries
        socketio.emit("analysis_progress", {"progress": 100, "current_step": "Generating summaries...", "session_id": session_id})
        gaze_summary    = get_eye_contact_summary(gaze_results)
        emotion_summary = get_emotion_summary(emotion_results)
        posture_summary = get_posture_summary(posture_results)

        # Speech — extract audio first for better Whisper accuracy
        socketio.emit("analysis_progress", {"progress": 100, "current_step": "Analyzing speech and audio...", "session_id": session_id})
        audio_path = extract_audio_from_video(video_path)
        speech_input = audio_path if audio_path else video_path
        speech_analysis = analyze_full_speech(speech_input)

        # Confidence score + full report
        socketio.emit("analysis_progress", {"progress": 100, "current_step": "Calculating confidence score...", "session_id": session_id})
        interview_duration = total_frames / fps

        report = generate_full_report(
            gaze_summary, emotion_summary, posture_summary, speech_analysis,
            gaze_results, emotion_results, posture_results,
            interview_duration
        )

        # Enrich report with chart and summary data
        report["chart_data"]   = prepare_chart_data(report)
        report["summary_text"] = generate_report_summary_text(report)

        # Validate before storing
        is_valid, err = validate_report_data(report)
        if not is_valid:
            socketio.emit("analysis_error", {"error": f"Report validation failed: {err}"})
            return

        analysis_store[session_id] = report

        socketio.emit("analysis_complete", {
            "session_id": session_id,
            "redirect": "/report"
        })

    except Exception as e:
        socketio.emit("analysis_error", {"error": f"Video processing failed: {str(e)}"})


# ──────────────────────────────────────────────
# LIVE ANALYSIS FINALIZER
# ──────────────────────────────────────────────
def finalize_live_analysis():
    global live_results, live_session_id
    try:
        gaze_results    = live_results["gaze_results"]
        emotion_results = live_results["emotion_results"]
        posture_results = live_results["posture_results"]

        gaze_summary    = get_eye_contact_summary(gaze_results)
        emotion_summary = get_emotion_summary(emotion_results)
        posture_summary = get_posture_summary(posture_results)

        speech_analysis = {
            "overall_speech_score": 0,
            "transcription": "Speech analysis not available for live sessions.",
            "filler_analysis": {"filler_score": 0, "filler_word_counts": {}, "total_filler_count": 0},
            "pace_analysis": {
                "pace_score": 0, "pace_label": "Not analyzed", "words_per_minute": 0,
                "long_pauses": [], "long_pause_count": 0,
                "feedback": "Speech analysis requires an uploaded video file."
            },
            "clarity_analysis": {"clarity_score": 0, "feedback": "N/A"}
        }

        interview_duration = len(gaze_results) / 10

        report = generate_full_report(
            gaze_summary, emotion_summary, posture_summary, speech_analysis,
            gaze_results, emotion_results, posture_results,
            interview_duration
        )

        report["chart_data"]   = prepare_chart_data(report)
        report["summary_text"] = generate_report_summary_text(report)

        analysis_store[live_session_id] = report
        socketio.emit("analysis_complete", {"session_id": live_session_id, "redirect": "/report"})

    except Exception as e:
        socketio.emit("analysis_error", {"error": f"Live analysis finalization failed: {str(e)}"})


# ──────────────────────────────────────────────
# FLASK ROUTES
# ──────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/live")
def live():
    return render_template("LiveVideo.html")

@app.route("/recorded")
def recorded():
    return render_template("RecordedVideo.html")

@app.route("/loading")
def loading():
    return render_template("loading.html")


@app.route("/report")
def report():
    session_id = session.get("session_id")
    if not session_id:
        return redirect(url_for("index"))

    report_data = analysis_store.get(session_id)
    if not report_data:
        return redirect(url_for("index"))

    return render_template(
        "report.html",
        report=report_data,
        chart_data=report_data.get("chart_data", {}),
        summary_text=report_data.get("summary_text", ""),
        overall_score=report_data["overall"]["score"],
        performance_label=report_data["overall"]["performance_label"],
        performance_color=report_data["overall"]["performance_color"],
        individual_scores=report_data["individual_scores"],
        recommendations=report_data["recommendations"],
        filler_details=report_data["filler_word_details"],
        transcription=report_data["transcription"],
        generated_at=report_data["generated_at"],
        interview_duration=report_data["interview_duration"]
    )


@app.route("/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return redirect(url_for("recorded"))

    file = request.files["video"]
    if file.filename == "":
        return redirect(url_for("recorded"))

    if file and allowed_file(file.filename):
        session_id     = str(uuid.uuid4())
        safe_name      = secure_filename(file.filename)
        video_filename = f"{session_id}_{safe_name}"
        video_path     = os.path.join(app.config["UPLOAD_FOLDER"], video_filename)
        file.save(video_path)

        session["session_id"] = session_id

        thread = threading.Thread(
            target=process_video_file,
            args=(video_path, session_id),
            daemon=True
        )
        thread.start()

        return redirect(url_for("loading"))

    return "Invalid file type. Allowed: mp4, avi, mov, mkv, webm.", 400


@app.route("/get_report_data")
def get_report_data():
    """Polling fallback for loading page."""
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"ready": False})
    if analysis_store.get(session_id):
        return jsonify({"ready": True, "redirect": "/report"})
    return jsonify({"ready": False})


@app.route("/check_session")
def check_session():
    """Checks if an analysis session is currently active."""
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"active": False})
    # Active if session exists but report isn't ready yet (processing)
    # OR if report is already done
    active = session_id is not None
    return jsonify({"active": active})


@app.route("/clear_session")
def clear_session():
    """Clears session and removes report from store. Used by 'Start New Interview'."""
    session_id = session.pop("session_id", None)
    if session_id and session_id in analysis_store:
        del analysis_store[session_id]
    return redirect(url_for("index"))


# ──────────────────────────────────────────────
# ERROR HANDLERS
# ──────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("index.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("index.html"), 500


# ──────────────────────────────────────────────
# SOCKET.IO EVENTS
# ──────────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    print("[SocketIO] Client connected")
    emit("connected", {"message": "Connected to InterviewAI server"})


@socketio.on("disconnect")
def on_disconnect():
    global live_analysis_running
    print("[SocketIO] Client disconnected")
    live_analysis_running = False


@socketio.on("start_live_analysis")
def on_start_live(data=None):
    global live_analysis_running, live_session_id, live_results
    try:
        live_analysis_running = True
        live_results = {"gaze_results": [], "emotion_results": [], "posture_results": []}
        live_session_id = str(uuid.uuid4())

        # Store in Flask session for /report retrieval
        session["session_id"] = live_session_id

        emit("live_started", {"message": "Live analysis started", "session_id": live_session_id})
        print(f"[Live] Session started: {live_session_id}")
    except Exception as e:
        emit("analysis_error", {"error": str(e)})


@socketio.on("stop_live_analysis")
def on_stop_live():
    global live_analysis_running
    try:
        live_analysis_running = False
        emit("live_stopped", {"message": "Live analysis stopped. Processing results..."})
        thread = threading.Thread(target=finalize_live_analysis, daemon=True)
        thread.start()
    except Exception as e:
        emit("analysis_error", {"error": str(e)})


@socketio.on("live_frame")
def on_live_frame(data):
    """Receives base64 webcam frame, runs visual detectors, emits live_stats."""
    global live_results, live_analysis_running
    if not live_analysis_running:
        return
    try:
        frame = base64_to_frame(data.get("frame", ""))
        if frame is None:
            emit("analysis_error", {"error": "Failed to decode frame."})
            return

        gaze_result    = detect_gaze(frame)
        emotion_result = detect_emotion(frame)
        posture_result = detect_posture(frame)

        live_results["gaze_results"].append(gaze_result)
        live_results["emotion_results"].append(emotion_result)
        live_results["posture_results"].append(posture_result)

        emit("live_stats", {
            "gaze":      gaze_result,
            "emotion":   emotion_result,
            "posture":   posture_result,
            "timestamp": time.time()
        })

    except Exception as e:
        emit("analysis_error", {"error": f"Frame processing error: {str(e)}"})


# ──────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    socketio.run(app, debug=Config.FLASK_DEBUG, host="0.0.0.0", port=5000)
