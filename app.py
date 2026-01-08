import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify
import threading
import time
from datetime import datetime
from collections import Counter
import os

# Import your simplified trackers
from src.emotion_detection import EmotionDetector
from src.blink_tracker import BlinkTracker

app = Flask(__name__)

# Initialize detection engines
emotion_engine = EmotionDetector(
    r'F:\MAJU\6th Semester\AI\Project\Interview-Detection-System\models\interview_emotion_final_94.keras'
)
blink_engine = BlinkTracker()

# Global variables
current_metrics = {
    'emotion': 'Initializing...',
    'confidence': 0.0,
    'blink_count': 0
}

session_data = {
    'start_time': None,
    'end_time': None,
    'emotion_history': [],
    'blink_history': [],
    'is_active': False
}

camera = None
camera_enabled = False
interview_active = True

# ---------------- CAMERA HANDLING ----------------
def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
    return camera

def release_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None

# ---------------- FRAME GENERATOR ----------------
def generate_frames():
    global current_metrics, session_data, camera_enabled, interview_active

    # Start session
    if session_data['start_time'] is None:
        session_data['start_time'] = datetime.now()
        session_data['is_active'] = True

    while interview_active:
        if not camera_enabled:
            # Black frame placeholder when camera is OFF
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "Camera OFF", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            cap = get_camera()
            success, frame = cap.read()
            if not success:
                break

            # ---------------- DETECTIONS ----------------
            emotion, conf = emotion_engine.predict_emotion(frame)
            blink_count = blink_engine.update_blink(frame)

            # ---------------- UPDATE METRICS ----------------
            current_metrics.update({
                'emotion': emotion,
                'confidence': float(conf),
                'blink_count': blink_count
            })

            # Track session
            if emotion != "No Face":
                session_data['emotion_history'].append(emotion)
            session_data['blink_history'].append(blink_count)

            # Overlay metrics on frame
            cv2.putText(frame, f"Emotion: {emotion} ({conf*100:.1f}%)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Blinks: {blink_count}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ---------------- FLASK ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/metrics')
def metrics():
    return jsonify(current_metrics)

@app.route('/toggle_camera', methods=['POST'])
def toggle_camera():
    global camera_enabled
    camera_enabled = not camera_enabled
    if not camera_enabled:
        release_camera()
    return jsonify({'camera_enabled': camera_enabled})

@app.route('/end_interview', methods=['POST'])
def end_interview():
    global interview_active, session_data
    interview_active = False
    session_data['end_time'] = datetime.now()
    session_data['is_active'] = False
    release_camera()
    return jsonify({'status': 'success', 'message': 'Interview ended'})

@app.route('/summary')
def summary():
    if session_data['start_time'] is None:
        return jsonify({'error': 'No session found'})

    duration = (session_data['end_time'] - session_data['start_time']).total_seconds() if session_data['end_time'] else 0
    minutes = int(duration // 60)
    seconds = int(duration % 60)

    # Emotion analysis
    emotion_counts = Counter(session_data['emotion_history'])
    dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else 'N/A'

    avg_blinks = session_data['blink_history'][-1] if session_data['blink_history'] else 0

    summary_data = {
        'duration': f"{minutes}m {seconds}s",
        'dominant_emotion': dominant_emotion,
        'total_blinks': avg_blinks
    }

    return jsonify(summary_data)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    release_camera()
    def die():
        time.sleep(1)
        os._exit(0)
    threading.Thread(target=die).start()
    return jsonify({'status': 'success', 'message': 'Server shutting down...'})

# ---------------- MAIN ----------------
if __name__ == '__main__':
    print("Starting Interview Detection System...")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
