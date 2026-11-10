# 🏋️‍♂️ AI Gym Coach — Real-Time Workout Intelligence & Form Coach

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.54.0-FF4B4B.svg)](https://streamlit.io/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.14-00C0FF.svg)](https://developers.google.com/mediapipe)
[![Groq LLaMA 3.3](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-F55036.svg)](https://groq.com/)

A modern, high-performance computer vision fitness companion that turns your webcam into an elite personal trainer. Tracks joint biometrics, evaluates form in real time, counts reps, estimates calorie expenditure, enforces rest intervals, and delivers spoken audio cues with customizable coaching personas.

---

## ✨ Features & Capabilities

### 1. 👁️ Real-Time Computer Vision & Biometrics
- **MediaPipe Pose Landmarker** integration via low-latency WebRTC streaming.
- **Dynamic Joint Skeleton**: Color-coded feedback (Emerald when clean, Amber/Red when form faults are detected).
- **In-Video HUD Overlay**: On-screen rep counter, exercise stage, joint angles, and real-time biomechanical diagnostics.

### 2. 🏋️ 7 Supported Exercises
- **Squats**: Knee angle tracking (depth ≤ 100°), hip-shoulder posture, and forward lean detection.
- **Push-ups**: Elbow flexion (90° lockout), rigid plank body alignment, and hip sag/pike warnings.
- **Biceps Curls (Dumbbell)**: Full extension/flexion tracking, elbow drift prevention, and torso swing detection.
- **Shoulder Press**: Overhead vertical extension lockout, elbow angle, and lumbar hyperextension prevention.
- **Lunges**: Front knee flexion (~90°), torso verticality, and lateral balance stabilization.
- **Jumping Jacks *(NEW)***: Full-body cardio tracking, arm sweep reach (>120°), and lateral leg spread ratios.
- **Isometric Plank *(NEW)***: Core hold timer, 160°–180° rigid alignment check, and hip height deviation detection.

### 3. 🎙️ AI Voice Coaching (Online & Smart Offline Fallback)
- **Groq LLaMA 3.3 70B Integration**: Generates natural, punchy, contextual coaching cues based on detected movement.
- **Three Coach Personas**:
  - ⚡ **Energetic Coach**: High-energy, positive, pumped-up reinforcement.
  - 🎖️ **Strict Drill Sergeant**: Direct, disciplined, military-standard form adherence.
  - 🧘 **Mindful Master**: Focused on breath control, cadence, and muscle-mind connection.
- **Smart Offline Fallback Engine**: If no Groq API key is present or internet drops, high-energy rule-based coaching still speaks aloud via TTS!
- **Voice Mute & Volume Toggle**: Easily turn audio coaching on or off anytime.

### 4. 🛡️ Form Integrity Score (%)
- Computes real-time frame-by-frame and rep-by-rep biomechanical quality.
- Categorizes sessions: *Flawless Form (≥85%)*, *Good Form (70–84%)*, or *Needs Work (<70%)*.

### 5. 🔥 Precision Calorie Expenditure Tracker
- Estimates calories burned based on **MET (Metabolic Equivalent of Task)** values tailored for each exercise, your configurable body weight (kg), and active exercise duration.

### 6. ⏳ Set-Interval Rest Countdown Timer
- Automatically triggers upon set completion (or manual start).
- Audio and visual progress bar countdown (30s / 45s / 60s / 90s) with "Skip Rest" shortcut.

### 7. 📊 Performance & Analytics Dashboard
- **Streak Tracker**: Tracks consecutive days active with flame badge (🔥).
- **Daily Rep Goal Meter**: Set personal targets (e.g., 50 reps/day) with live progress bar.
- **Interactive Visual Charts**: Daily rep volume trends and exercise distribution.
- **Personal Records (PRs) Showcase**: Hall of Fame highlighting all-time best reps and sets.
- **CSV Data Export**: Download your full workout log with one click.

### 8. 📖 Exercise Academy & Form Library
- In-depth movement standards, target muscle groups, common faults, and AI vision detection points for all 7 movements.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11 or 3.12
- A webcam for live pose detection

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/your-username/ai-gym-coach.git
cd ai-gym-coach/"Main App"

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application with Groq API Key (PowerShell)

#### Option A: Set Environment Variable in PowerShell (Recommended)
```powershell
$env:GROQ_API_KEY = "gsk_your_actual_key_here"
streamlit run main.py
```

#### Option B: Pass Directly as a Command-Line Flag
```powershell
streamlit run main.py -- --groq-api-key "gsk_your_actual_key_here"
```

#### Option C: Run in Offline Mode (No API Key Required)
```powershell
streamlit run main.py
```
*(If no API key is set, the application seamlessly runs on its built-in rule-based coaching engine with full voice TTS audio).*

---

## 📁 Project Architecture

```
ai-gym-coach/
├── LandingPage/               # Showcase & portfolio landing page
│   ├── index.html             # High-converting athlete landing page
│   ├── style.css              # Cyberpunk athletic CSS styling
│   └── fonts/                 # Averta web fonts
└── Main App/                  # Core Streamlit Web Application
    ├── main.py                # Studio UI, Tabbed Navigation & Streamlit logic
    ├── data.db                # SQLite database for athlete profiles & workouts
    ├── requirements.txt       # Python dependencies
    ├── ml_models/
    │   └── pose_landmarker_full.task  # MediaPipe vision model
    ├── core/
    │   └── base_exercise.py   # Base abstract class & geometry math
    ├── detectors/             # Biomechanical form detection engines
    │   ├── squat.py           # Squat depth & back angle
    │   ├── pushup.py          # Push-up elbow & hip sag
    │   ├── biceps_curl.py     # Curl elbow drift & sway
    │   ├── shoulder_press.py  # Overhead press lockout & arch
    │   ├── lunges.py          # Lunge depth & lateral balance
    │   ├── jumping_jacks.py   # Cardio arm sweep & leg spread
    │   └── plank.py           # Core alignment & hold timer
    ├── services/
    │   ├── auth/              # Athlete login & profile loader
    │   ├── coaching/          # LLM, TTS, Personas & Voice Pipeline
    │   ├── config/            # Exercise METs, guides, prompts
    │   ├── persistence/       # SQLite schema, migrations & analytics queries
    │   ├── tracking/          # Calorie calculation & form accuracy
    │   ├── ui/                # CSS injection & font loader
    │   └── vision/            # WebRTC video processor & HUD renderer
    └── static/
        └── style.css          # Modern dark-mode athletic styling
```

---

## 🛡️ License
Distributed under the MIT License. Built for athletes and fitness enthusiasts.
