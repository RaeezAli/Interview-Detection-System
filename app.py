import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import eventlet

# Initialize eventlet for async mode
eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'interview_detector_secret'

# Set up upload folder configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Flask-SocketIO with eventlet
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Global dictionary to store detection results
analysis_results = {
    "gaze": None,
    "emotion": None,
    "posture": None,
    "speech": None,
    "overall_confidence": 0
}

# --- PAGE ROUTES (GET) ---

@app.route("/")
def index():
    """Renders the main landing page."""
    return render_template("index.html")

@app.route("/live")
def live_video():
    """Renders the Live Video Analysis page."""
    return render_template("LiveVideo.html")

@app.route("/recorded")
def recorded_video():
    """Renders the Recorded Video Analysis page."""
    return render_template("RecordedVideo.html")

@app.route("/loading")
def loading():
    """Renders the loading/processing screen."""
    return render_template("loading.html")

@app.route("/report")
def report():
    """Renders the feedback and report page with analysis results."""
    return render_template("report.html", results=analysis_results)

# --- ACTION ROUTES (POST) ---

@app.route("/upload", methods=["POST"])
def upload_video():
    """Accepts a video file upload, saves it, and redirects to loading."""
    if 'video' not in request.files:
        return "No video file provided", 400
    
    video = request.files['video']
    if video.filename == '':
        return "No selected file", 400
    
    if video:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
        video.save(file_path)
        print(f"Video saved to: {file_path}")
        return redirect(url_for("loading"))

@app.route("/analyze", methods=["POST"])
def analyze_video():
    """Full detection pipeline placeholder for recorded videos."""
    # Logic for full video analysis will go here
    return jsonify({"status": "analyzing", "message": "Detection pipeline started"})

# --- SOCKET.IO EVENTS ---

@socketio.on("start_live_analysis")
def handle_start_live(data):
    """Triggers the live video detection pipeline."""
    print("Live analysis requested")
    # Live detection logic trigger will go here
    emit("status", {"message": "Live analysis started"})

@socketio.on("stop_live_analysis")
def handle_stop_live():
    """Stops the live feed and triggers redirection sequence."""
    print("Live analysis stop requested")
    # Logic to terminate live stream and finalize results will go here
    emit("status", {"message": "Live analysis stopped"})

if __name__ == "__main__":
    # Run the Flask app with Socket.IO
    socketio.run(app, debug=True)
