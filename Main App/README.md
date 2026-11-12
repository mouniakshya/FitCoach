# FitCoach - Main Application

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.54.0-blue.svg)](https://streamlit.io/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.14-00C0FF.svg)](https://developers.google.com/mediapipe)

Main application directory for the FitCoach computer vision fitness platform.

## Quick Start (PowerShell)

```powershell
cd "d:\ai-gym-coach-main\Main App"
.\venv\Scripts\activate

# Optional: Set Groq API key for LLaMA 3.3 voice coaching
$env:GROQ_API_KEY = "gsk_your_actual_key_here"

# Launch Streamlit studio
streamlit run main.py
```

The application will be accessible at: `http://localhost:8501`

## Features

- Real-time pose estimation and joint angle tracking via MediaPipe.
- 7 supported exercises: Squats, Push-ups, Biceps Curls, Overhead Shoulder Press, Lunges, Jumping Jacks, and Isometric Plank.
- Professional light-mode user interface with high-contrast data visualization.
- Form quality assessment, live calorie burn meter, and set-interval rest timer.
- Audio coaching engine with 3 customizable coaching personas.
- Performance analytics, personal records, and CSV export.
