import streamlit as st


def initial_session_defaults():
    defaults = {
        "reps": 0,
        "target_sets": 3,
        "reps_per_set": 10,
        "sets_completed": 0,
        "current_set_reps": 0,
        "workout_completed": False,
        "last_notified_sets_completed": 0,
        "last_notified_workout_complete": False,
        "last_saved_sets_completed": 0,
        "set_cycle_started_at": 0.0,
        "workout_started_at": 0.0,
        "last_exercise_type": "Squats",

        # Workout plan
        "workout_started": False,
        "plan_exercise": "Squats",
        "plan_sets": 3,
        "plan_reps": 10,

        # Metrics and Telemetry
        "knee_angle": 0,
        "back_angle": 0,
        "elbow_angle": 0,
        "front_knee_angle": 0,
        "torso_angle": 0,
        "arm_angle": 0,
        "leg_spread_ratio": 0.0,
        "motion_phase": "N/A",
        "hold_seconds": 0,

        # Status fields
        "depth_status": "N/A",
        "body_alignment": "N/A",
        "hip_status": "N/A",
        "shoulder_status": "N/A",
        "swing_status": "N/A",
        "extension_status": "N/A",
        "back_arch_status": "N/A",
        "balance_status": "N/A",

        # Health & Analytics Tracking
        "user_weight": 70.0,
        "daily_goal_reps": 50,
        "session_calories": 0.0,
        "session_form_score": 100.0,
        "form_total_samples": 0,
        "form_clean_samples": 0,

        # Rest Timer
        "rest_timer_active": False,
        "rest_start_time": 0.0,
        "rest_duration": 45,
        "rest_interval_seconds": 45,

        # Voice Coach & Preferences
        "coach_personality": "Motivational",
        "voice_enabled": True,
        "coach_feedback": None,
        "audio_to_play": None,
        "groq_api_key": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
