---

# 🎯 InterviewAI — AI Powered Interview Detection System

> An intelligent interview analysis system that uses computer vision, speech recognition, and AI to help you improve your interview performance.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-orange)
![Claude AI](https://img.shields.io/badge/Claude-AI-purple)

---

## 🌟 Features

| Feature                           | Description                                                         |
| --------------------------------- | ------------------------------------------------------------------- |
| 👁 **Eye Contact Detection**      | Real iris tracking using MediaPipe to measure camera engagement     |
| 😊 **Facial Expression Analysis** | DeepFace emotion recognition mapped to interview context            |
| 🧍 **Posture Detection**          | MediaPipe Pose to detect slouching, leaning, and head position      |
| 🎙 **Speech Analysis**            | OpenAI Whisper transcription with WPM calculation                   |
| 🔤 **Filler Word Detection**      | Detects uh, um, like, so and 15+ other filler words with timestamps |
| 💪 **Confidence Scoring**         | Weighted scoring across all 5 categories                            |
| 🤖 **AI Feedback**                | Claude AI generates personalized recommendations per session        |
| 🎯 **Practice Mode**              | AI asks interview questions and evaluates your answers              |
| 📊 **Detailed Report**            | Charts, graphs, transcription, and actionable recommendations       |

---

## 🖥 Demo

### Upload Video Mode
Upload any recorded interview video and get a full analysis report.

### Live Interview Mode
Use your webcam to record a live interview session and get analyzed after.

### Practice Mode
Answer AI-generated interview questions and receive instant feedback.

---

## 🛠 Tech Stack

**Backend:**
- Python 3.11
- Flask + Flask-SocketIO
- OpenCV
- MediaPipe (Face Mesh + Pose)
- DeepFace
- OpenAI Whisper
- Anthropic Claude API

**Frontend:**
- HTML5 + CSS3 + JavaScript
- Chart.js
- Socket.IO
- Font Awesome

---

## ⚡ Installation

### Prerequisites

- Python 3.11
- FFmpeg installed and added to PATH or configured in .env
- Anthropic API key from https://console.anthropic.com

### Step 1 — Clone the repository

```bash
git clone https://github.com/yourusername/interview-detector.git
cd interview-detector
```

### Step 2 — Create virtual environment

```bash
python -m venv venv
```

**Windows:**

```bash
venv\Scripts\activate
```

**Mac/Linux:**

```bash
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment variables

```bash
cp .env.example .env
```

### Step 5 — Run the application

```bash
python app.py
```
