# FitCoach - Real-Time Workout Intelligence & Form Assessment

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.54.0-blue.svg)](https://streamlit.io/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.14-00C0FF.svg)](https://developers.google.com/mediapipe)
[![Groq LLaMA 3.3](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-orange.svg)](https://groq.com/)

A computer vision fitness application that uses your webcam to assess exercise biomechanics in real time. Features live joint angle calculations, automated rep counting, form fault detection, energy expenditure tracking, set-interval rest timing, and spoken coaching feedback with multiple coaching styles.

---

## Features

### 1. Computer Vision & Joint Biometrics
- Low-latency pose detection powered by MediaPipe Pose Landmarker via WebRTC.
- Dynamic color-coded skeleton tracking joint alignment and depth.
- On-screen telemetry HUD with rep count, movement phase, and joint angles.

### 2. 7 Supported Exercises
- **Squats**: Knee flexion angle (depth <= 100 deg), hip posture, and torso forward lean monitoring.
- **Push-ups**: Elbow flexion (90 deg depth), rigid spine alignment, and hip sag/pike detection.
- **Biceps Curls (Dumbbell)**: Full extension/flexion tracking, elbow drift prevention, and torso sway reduction.
- **Shoulder Press**: Overhead vertical extension, elbow angles, and lumbar arch monitoring.
- **Lunges**: Front knee flexion (~90 deg), torso verticality, and lateral balance stabilization.
- **Jumping Jacks**: Full-body cardio tracking, overhead arm sweep (>120 deg), and lateral leg spread ratios.
- **Isometric Plank**: Core hold duration timer, rigid alignment check (160-180 deg), and hip position detection.

### 3. Audio Coaching (Online & Offline Fallback)
- **Groq LLaMA 3.3 70B Integration**: Generates natural, concise audio cues based on detected movement.
- **Three Coaching Styles**:
  - Energetic Coach: Positive reinforcement and motivating cues.
  - Strict Drill Sergeant: Direct, disciplined, military-standard execution commands.
  - Mindful Coach: Focused on deliberate control, tempo, and breathing.
- **Offline Rule-Based Fallback**: Built-in rules engine ensures spoken audio cues function even without an external API key.
- **Audio Toggle**: Easily enable or mute voice guidance.

### 4. Form Quality Assessment
- Evaluates biomechanical execution on every frame and rep.
- Categorizes sessions: Flawless Form (>= 85%), Acceptable Form (70-84%), or Needs Correction (< 70%).

### 5. Energy Expenditure Estimation
- Estimates calorie burn based on Metabolic Equivalent of Task (MET) values tailored to each movement, configurable body weight (kg), and active exercise duration.

### 6. Set-Interval Rest Timer
- Automatically triggers upon set completion with an interactive countdown bar and skip control.

### 7. Performance Analytics & History
- Streak tracking: Consecutive active workout days.
- Daily rep target meter with progress bar.
- Interactive volume and exercise distribution charts.
- Personal records table highlighting all-time best reps and sets.
- One-click CSV export of session logs.

### 8. Exercise Academy
- Movement standards, target muscle groups, common faults, and computer vision detection points for all 7 movements.

---

## Quick Start Guide

### Prerequisites
- Python 3.11 or 3.12
- Standard webcam

### 1. Clone & Set Up Environment
```powershell
cd "d:\ai-gym-coach-main\Main App"
.\venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run Application

#### Option A: Set Environment Variable in PowerShell (Recommended)
```powershell
$env:GROQ_API_KEY = "gsk_your_actual_key_here"
streamlit run main.py
```

#### Option B: Pass via Command-Line Argument
```powershell
streamlit run main.py -- --groq-api-key "gsk_your_actual_key_here"
```

#### Option C: Offline Mode (No Key Required)
```powershell
streamlit run main.py
```

The application will be accessible at: `http://localhost:8501`

---

## Directory Structure

```
ai-gym-coach/
|-- README.md                  # Main documentation (root)
|-- LandingPage/               # Standalone marketing landing page
|   |-- index.html
|   `-- style.css
`-- Main App/                  # Core application directory
    |-- README.md              # Application documentation
    |-- main.py                # Main Streamlit application entry point
    |-- data.db                # SQLite database for profiles and session history
    |-- requirements.txt       # Python dependencies
    |-- ml_models/             # MediaPipe task models
    |-- core/                  # Base exercise class and vector math
    |-- detectors/             # Exercise-specific movement engines
    |-- services/              # Auth, vision, tracking, coaching, persistence
    `-- static/                # Modern light-mode stylesheet and fonts
```

---

## License
Distributed under the MIT License.
