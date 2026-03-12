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

# ──────────────────────────────────────────────
# APP CONFIGURATION
# ──────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "interviewai_fixed_secret_key_2025"
app.config["UPLOAD_FOLDER"] = Config.UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}

socketio = SocketIO(
    app,
    async_mode="threading",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False
)

# Ensure required folders exist
ensure_folder_exists(app.config["UPLOAD_FOLDER"])

# ──────────────────────────────────────────────
# GLOBAL STATE
# ──────────────────────────────────────────────
analysis_store: dict = {}
live_sessions_data: dict = {}  # Keyed by session_id: {gaze: [], emotion: [], posture: [], running: bool}


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

            # PERFORMANCE: Skip frames to speed up processing
            if frame_count % 10 != 0:
                continue

            # PERFORMANCE: Resize frame to speed up detector execution
            frame = cv2.resize(frame, (480, 360))

            gaze_results.append(detect_gaze(frame))
            emotion_results.append(detect_emotion(frame))
            posture_results.append(detect_posture(frame))

            # PERFORMANCE: Only emit progress every 10 processed frames (which is every 100 actual frames here, but let's stick to the 10 frames rule for emits too)
            if frame_count % 10 == 0:
                progress = round((frame_count / total_frames) * 100, 1) if total_frames > 0 else 0
                socketio.emit("analysis_progress", {
                    "progress": progress,
                    "current_step": f"Analyzing frame {frame_count} of {total_frames}...",
                    "session_id": session_id
                })
            
            # Small sleep to yield to other threads
            time.sleep(0.001)

        cap.release()

        # Summaries
        socketio.emit("analysis_progress", {"progress": 100, "current_step": "Generating summaries...", "session_id": session_id})
        gaze_summary    = get_eye_contact_summary(gaze_results)
        emotion_summary = get_emotion_summary(emotion_results)
        posture_summary = get_posture_summary(posture_results)

        # Speech — extract audio first for better Whisper accuracy
        socketio.emit("analysis_progress", {"progress": 100, "current_step": "Analyzing speech and audio...", "session_id": session_id})
        
        # After saving uploaded file (tracking progress)
        print(f"Processing video: {video_path}")
        print(f"Video file size: {os.path.getsize(video_path)} bytes")

        audio_path = extract_audio_from_video(video_path)
        
        # After extract_audio_from_video (tracking results)
        print(f"Audio extraction result: {audio_path}")
        if audio_path:
            print(f"Audio file size: {os.path.getsize(audio_path)} bytes")
            speech_input = audio_path
        else:
            print("WARNING: Audio extraction returned None")
            speech_input = video_path # fallback: pass video directly to whisper

        print("Starting speech analysis...")
        speech_analysis = analyze_full_speech(speech_input)
        
        # After transcription tracking
        transcription = speech_analysis.get("transcription", "")
        print(f"Transcription text length: {len(transcription)}")
        print(f"Transcription preview: {transcription[:100]}")
        
        print(f"Speech analysis complete: Score: {speech_analysis.get('overall_speech_score')}")

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

        # PART 2 — Fix how individual_scores are stored
        from datetime import datetime
        analysis_store[session_id] = {
            "session_id": session_id,
            "overall": {
                "score": report["overall"]["score"],
                "performance_label": report["overall"]["performance_label"]
            },
            "individual_scores": {
                "eye_contact": report["individual_scores"]["eye_contact"],
                "emotion": report["individual_scores"]["emotion"],
                "posture": report["individual_scores"]["posture"],
                "speech_pace": report["individual_scores"]["speech_pace"],
                "filler_words": report["individual_scores"]["filler_words"]
            },
            "summaries": {
                "gaze": gaze_summary,
                "emotion": emotion_summary,
                "posture": posture_summary,
                "speech": speech_analysis
            },
            "timeline_labels": report["timeline_data"]["labels"],
            "timeline_confidence": report["timeline_data"]["confidence_data"],
            "timeline_eye": report["timeline_data"]["eye_contact_data"],
            "timeline_emotion": report["timeline_data"]["emotion_data"],
            "timeline_posture": report["timeline_data"]["posture_data"],
            "recommendations": report["recommendations"],
            "transcription": report["transcription"],
            "filler_word_details": report["filler_word_details"],
            "chart_data": report["chart_data"],
            "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "duration": duration_str,
            "generated_at": report["generated_at"],
            "interview_duration": report["interview_duration"],
            "summary_text": report["summary_text"]
        }

        socketio.emit("analysis_complete", {
            "session_id": session_id,
            "redirect": "/report"
        })

    except Exception as e:
        socketio.emit("analysis_error", {"error": f"Video processing failed: {str(e)}"})


# ──────────────────────────────────────────────
# LIVE ANALYSIS FINALIZER (REMOVED)
# ──────────────────────────────────────────────
# finalize_live_analysis has been removed as live sessions
# now follow the same pipeline as recorded videos.


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
    if not session_id or session_id not in analysis_store:
        return redirect(url_for("index"))
    
    report_data = analysis_store[session_id]
    
    # Use the unified helper to build chart data consistent with helpers.py
    chart_data = prepare_chart_data(report_data)
    
    import json
    chart_data_json = json.dumps(chart_data)
    
    # Debug print
    print("=== CHART DATA DEBUG ===")
    print("chart_data_json:", chart_data_json[:500] + "...")
    print("========================")
    
    return render_template(
        "report.html",
        report=report_data,
        chart_data=chart_data,
        chart_data_json=chart_data_json,
        summary_text=report_data.get("summary_text", ""),
        overall_score=report_data["overall"]["score"],
        performance_label=report_data["overall"]["performance_label"],
        performance_color=report_data.get("overall", {}).get("performance_color", "#fff"),
        individual_scores=report_data["individual_scores"],
        recommendations=report_data["recommendations"],
        filler_details=report_data.get("filler_word_details", {}),
        transcription=report_data.get("transcription", "")
    )


@app.route("/upload", methods=["POST"])
def upload_video():
    # Handle both "video" (from normal form) and "file" (from live recorder FormData)
    file_key = "video" if "video" in request.files else ("file" if "file" in request.files else None)
    
    is_fetch = "application/json" in request.headers.get("Accept", "")

    if not file_key:
        if is_fetch:
            return jsonify({"error": "No file"}), 400
        return redirect(url_for("recorded"))

    file = request.files[file_key]
    if file.filename == "":
        if is_fetch:
            return jsonify({"error": "No filename"}), 400
        return redirect(url_for("recorded"))

    if file and allowed_file(file.filename):
        session_id     = str(uuid.uuid4())
        safe_name      = secure_filename(file.filename)
        video_filename = f"{session_id}_{safe_name}"
        video_path     = os.path.join(app.config["UPLOAD_FOLDER"], video_filename)
        file.save(video_path)

        session["session_id"] = session_id
        session["session_mode"] = "recorded"  # Live sessions now act as recorded ones

        thread = threading.Thread(
            target=process_video_file,
            args=(video_path, session_id),
            daemon=True
        )
        thread.start()

        if is_fetch:
            return jsonify({"redirect": "/loading", "session_id": session_id})
        return redirect(url_for("loading"))

    if is_fetch:
        return jsonify({"error": "Invalid file type"}), 400
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
    """Checks if an analysis session is currently active and its status."""
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"active": False, "report_ready": False})
    
    report_ready = session_id in analysis_store
    mode = session.get("session_mode", "recorded")
    
    return jsonify({
        "active": True,
        "session_id": session_id,
        "report_ready": report_ready,
        "mode": mode
    })


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
    try:
        session["session_mode"] = "live"
        emit("live_started", {"message": "Recording started"})
    except Exception as e:
        emit("analysis_error", {"error": str(e)})


@socketio.on("stop_live_analysis")
def on_stop_live():
    pass # Kept as empty stub for JS compatibility


@socketio.on("request_finalize")
def handle_request_finalize(data):
    pass # No longer needed, kept as empty stub


@socketio.on("live_frame")
def on_live_frame(data):
    pass # Kept as empty stub for JS compatibility


# ──────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    socketio.run(app, debug=Config.FLASK_DEBUG, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True, use_reloader=False)
