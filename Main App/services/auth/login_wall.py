import streamlit as st
import sqlite3
from services.persistence.exercise_repository import get_or_create_user, get_user_profile, _get_connection


def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True

    # Header with aesthetic badge
    st.markdown(
        """
        <div style="text-align: center; margin-top: 2rem; margin-bottom: 2rem;">
            <div style="display: inline-block; padding: 6px 16px; border-radius: 20px; background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.3); color: #00F0FF; font-size: 0.85rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px;">
                ⚡ Computer Vision · Voice Coaching · Biometrics
            </div>
            <h1 style="font-size: 2.8rem; font-weight: 800; background: linear-gradient(135deg, #FFFFFF 0%, #A0AEC0 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0 0 10px 0;">
                AI Gym Coach
            </h1>
            <p style="font-size: 1.15rem; color: #94A3B8; max-width: 580px; margin: 0 auto 2rem auto;">
                Real-time pose estimation, proactive form correction, rep tracking, and personalized audio coaching right through your webcam.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("#### 👤 Athlete Access")
            st.caption("Sign in with your athlete name or pick an existing profile.")

            conn = _get_connection()
            existing_users = []
            try:
                rows = conn.execute("SELECT username FROM users ORDER BY created_at DESC LIMIT 10").fetchall()
                existing_users = [r["username"] for r in rows]
            except Exception:
                existing_users = []

            selected_existing = None
            if existing_users:
                selected_existing = st.selectbox(
                    "Quick Pick Athlete:",
                    options=["-- Or select existing athlete --"] + existing_users,
                    index=0
                )

            with st.form("login_form", clear_on_submit=False):
                default_name = selected_existing if selected_existing and selected_existing != "-- Or select existing athlete --" else ""
                username = st.text_input(
                    "Athlete Username",
                    value=default_name,
                    placeholder="e.g. Alex, Jordan, Sarah"
                )
                submit_button = st.form_submit_button("Enter Gym Studio →", width="stretch")

            if submit_button:
                cleaned_name = (username or "").strip()
                if not cleaned_name:
                    st.error("Please enter an athlete name to proceed.")
                    return False

                user = get_or_create_user(cleaned_name)
                st.session_state["user_id"] = user["id"]
                st.session_state["username"] = user["username"]

                # Load saved profile settings into session
                profile = get_user_profile(user["id"])
                st.session_state["user_weight"] = profile["weight_kg"]
                st.session_state["daily_goal_reps"] = profile["daily_goal_reps"]
                st.session_state["coach_personality"] = profile["coach_personality"]
                st.session_state["voice_enabled"] = profile["voice_enabled"]

                st.success(f"Welcome back, **{cleaned_name}**! Entering studio...")
                st.rerun()

        # Feature badges at bottom of login
        st.markdown(
            """
            <div style="display: flex; justify-content: space-around; text-align: center; margin-top: 1.5rem; color: #64748B; font-size: 0.85rem;">
                <div>🔒 Local SQLite DB</div>
                <div>⚡ Zero Wearables</div>
                <div>🎙️ Real-time Audio Cues</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    return False
