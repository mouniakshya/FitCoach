import streamlit as st
import sqlite3
from services.persistence.exercise_repository import get_or_create_user, get_user_profile, _get_connection


def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True

    # Clean Header
    st.markdown(
        """
        <div style="text-align: center; margin-top: 2rem; margin-bottom: 2rem;">
            <div style="display: inline-block; padding: 4px 14px; border-radius: 4px; background: #EFF6FF; border: 1px solid #BFDBFE; color: #1D4ED8; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 12px;">
                Computer Vision · Biometric Feedback · Audio Coaching
            </div>
            <h1 style="font-size: 2.6rem; font-weight: 800; color: #0F172A; margin: 0 0 10px 0;">
                FitCoach
            </h1>
            <p style="font-size: 1.05rem; color: #475569; max-width: 580px; margin: 0 auto 2rem auto; line-height: 1.5;">
                Real-time pose estimation, automated form assessment, rep counting, and audio feedback through your camera.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        with st.container(border=True):
            st.markdown("#### Athlete Sign-In")
            st.caption("Sign in with an athlete name or select an existing profile to begin.")

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
                    "Select Existing Athlete Profile:",
                    options=["-- New Athlete Profile --"] + existing_users,
                    index=0
                )

            with st.form("login_form", clear_on_submit=False):
                default_name = selected_existing if selected_existing and selected_existing != "-- New Athlete Profile --" else ""
                username = st.text_input(
                    "Athlete Name",
                    value=default_name,
                    placeholder="e.g. Alex, Jordan, Sarah"
                )
                submit_button = st.form_submit_button("Enter Studio", type="primary", use_container_width=True)

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

                st.success(f"Signed in as {cleaned_name}. Entering studio...")
                st.rerun()

        # Architecture notes
        st.markdown(
            """
            <div style="display: flex; justify-content: space-around; text-align: center; margin-top: 1.5rem; color: #64748B; font-size: 0.8rem; font-weight: 500;">
                <div>[Local SQLite Database]</div>
                <div>[Zero Wearables Needed]</div>
                <div>[Real-Time Vision Pipeline]</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    return False
