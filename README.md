# InterviewAI - AI Powered Interview Detection System

> An AI-powered tool that analyzes interview performance in real time using computer vision and speech recognition. Get deep insights into your eye contact, facial expressions, posture, speech pace, and confidence score.

---

## 🎯 Features

| Category                  | What We Detect                                            |
| ------------------------- | --------------------------------------------------------- |
| 👁 **Eye Contact**        | Gaze direction, iris tracking, eye contact percentage     |
| 😊 **Facial Expressions** | Emotion classification mapped to interview labels         |
| 🧍 **Posture**            | Slouching, leaning, shoulder alignment, head position     |
| 🎙 **Speech Pace**        | Words per minute, long pauses, pace classification        |
| 🔤 **Filler Words**       | Detection of 20+ common interview fillers with timestamps |
| 📊 **Confidence Score**   | Weighted aggregate score with performance labels          |

---

## 🛠 Tech Stack

- **Backend**: Python, Flask, Flask-SocketIO, Eventlet
- **Computer Vision**: OpenCV, MediaPipe (Face Mesh + Pose)
- **Emotion Detection**: DeepFace / FER
- **Speech AI**: OpenAI Whisper
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js, Socket.IO client
- **Audio Extraction**: FFmpeg

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/RaeezAli/Interview-Detection-System.git
cd Interview-Detection-System
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Install FFmpeg

FFmpeg is required for audio extraction from video files.

- **Download**: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
- After installation, ensure `ffmpeg` is on your system PATH.

### 6. Run the Application

```bash
python app.py
```

## 📖 Usage

### 🎥 Live Interview Mode

1. Click **Live Interview** on the home page.
2. Allow browser access to your webcam.
3. Click **Start Interview** — the AI begins analyzing you in real time.
4. When done, click **End Interview**.
5. The system generates your full report automatically.

### 📁 Upload Video Mode

1. Click **Upload Video** on the home page.
2. Drag and drop (or browse) your recorded interview video.
3. Click **Analyze Video**.
4. Wait on the loading page — progress is shown in real time via Socket.IO.
5. Your full report opens automatically when analysis is complete.

---

## 📁 Project Structure

```
Interview-Detection-System/
├── app.py                    # Main Flask application
├── config.py                 # Configuration class (reads .env)
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignored files
├── README.md                 # Project documentation
├── face_landmarker.task      # MediaPipe model file
│
├── detectors/                # AI Detection Modules
│   ├── gaze.py               # Eye contact & iris tracking (MediaPipe)
│   ├── emotion.py            # Facial expression analysis
│   ├── posture.py            # Body language analysis (MediaPipe Pose)
│   ├── speech.py             # Transcription & pace (Whisper)
│   └── confidence_score.py   # Weighted score + report generator
│
├── utils/                    # Utility functions
│   └── helpers.py            # Shared utilities (video, file, chart, color)
│
├── templates/                # HTML Templates (Refactored)
│   ├── index.html            # Landing page
│   ├── LiveVideo.html        # Live webcam interview
│   ├── RecordedVideo.html    # Video upload page
│   ├── loading.html          # Analysis progress page
│   └── report.html           # Final analytics dashboard
│
├── static/                   # Static Assets
│   ├── css/                  # Extracted Stylesheets
│   │   ├── style.css         # Main shared styles
│   │   ├── live.css          # Live interview styles
│   │   ├── upload.css        # Recorded video styles
│   │   ├── loading.css       # Loading page styles
│   │   └── report.css        # Report dashboard styles
│   ├── js/                   # Extracted Scripts
│   │   ├── live.js           # Live interview logic
│   │   ├── upload.js         # Recorded video logic
│   │   ├── loading.js        # Loading page logic
│   │   └── report.js         # Report dashboard logic
│   └── assets/               # Images and icons
│
└── uploads/                  # Temporary video/audio files
```

---

## ⚡ Performance Notes

- **GPU Acceleration**: MediaPipe and FER benefit from a CUDA-enabled GPU.
- **Whisper Model**: The `base` model is used by default. Adjust in code if needed for higher accuracy.
- **Refactored Assets**: All inline CSS and JS have been moved to the `static/` directory to improve maintainability and page load speeds.
