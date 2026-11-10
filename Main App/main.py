import streamlit as st
import os
import sys
import time
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file if present
load_dotenv()

from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS, EXERCISE_GUIDES, COACH_PERSONAS, EXERCISE_MET
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import (
    init_db,
    get_users_exercises,
    get_user_stats,
    get_user_personal_records,
    get_user_profile,
    save_user_profile,
    delete_user_history
)
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio


def resolve_groq_api_key():
    """Resolves Groq API key prioritizing PowerShell environment, CLI args, session, or .env."""
    # 1. Check CLI argument passed via terminal: streamlit run main.py -- --groq-api-key "gsk_..."
    for i, arg in enumerate(sys.argv):
        if arg in ["--groq-api-key", "--api-key", "--groq-key"] and i + 1 < len(sys.argv):
            return sys.argv[i + 1].strip(), "CLI Flag"
        if arg.startswith("--groq-api-key="):
            return arg.split("=", 1)[1].strip(), "CLI Flag"
        if arg.startswith("--api-key="):
            return arg.split("=", 1)[1].strip(), "CLI Flag"

    # 2. Check PowerShell environment variable ($env:GROQ_API_KEY)
    env_key = os.environ.get("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key, "Terminal Environment ($env:GROQ_API_KEY)"

    # 3. Check UI session state (entered in Settings tab)
    session_key = st.session_state.get("groq_api_key", "").strip()
    if session_key:
        return session_key, "Settings Tab Input"

    # 4. Check Streamlit secrets if present
    if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
        return str(st.secrets["GROQ_API_KEY"]).strip(), "Streamlit Secrets"

    return "", "None"


def setup_voice_pipeline():
    api_key, key_source = resolve_groq_api_key()
    persona = st.session_state.get("coach_personality", "Motivational")

    groq_client = None
    if api_key:
        try:
            groq_client = Groq(api_key=api_key)
        except Exception:
            groq_client = None

    llm_coach = LLMCoach(groq_client=groq_client, persona=persona)
    tts = TextToSpeech()
    pipeline = VoicePipeline(llm_coach, tts)
    pipeline.set_enabled(st.session_state.get("voice_enabled", True))
    st.session_state.voice_pipeline = pipeline


def main():
    st.set_page_config(
        page_icon="🏋️‍♂️",
        page_title="AI Gym Coach - Studio",
        initial_sidebar_state="collapsed",
        layout="wide"
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    if not render_login_wall():
        return

    initial_session_defaults()

    if "voice_pipeline" not in st.session_state or st.session_state.voice_pipeline is None:
        setup_voice_pipeline()

    user_id = st.session_state.get("user_id", 0)
    username = st.session_state.get("username", "Athlete")

    # Top Navigation Bar & Athlete Header
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem;">
                <span style="font-size: 2rem;">🏋️‍♂️</span>
                <div>
                    <h2 style="margin: 0; font-size: 1.85rem; font-weight: 800; background: linear-gradient(135deg, #00F0FF, #10B981); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        AI Gym Coach
                    </h2>
                    <span style="color: #94A3B8; font-size: 0.88rem;">Computer Vision Form Coach & Workout Intelligence</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with head_col2:
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 8px;">
                <span style="background: rgba(255, 255, 255, 0.06); padding: 6px 14px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); font-size: 0.9rem;">
                    👤 <strong>{username}</strong>
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Audio Playback
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)
        st.session_state.audio_to_play = None  # Clear so it only plays once

    # Primary App Tabs
    tab_studio, tab_analytics, tab_academy, tab_settings = st.tabs([
        "🏋️ Workout Studio",
        "📊 Analytics & Performance",
        "📖 Exercise Academy",
        "⚙️ Profile & Coach Settings"
    ])

    # =========================================================================
    # TAB 1: WORKOUT STUDIO
    # =========================================================================
    with tab_studio:
        render_workout_studio()

    # =========================================================================
    # TAB 2: ANALYTICS & PERFORMANCE
    # =========================================================================
    with tab_analytics:
        render_analytics(user_id)

    # =========================================================================
    # TAB 3: EXERCISE ACADEMY
    # =========================================================================
    with tab_academy:
        render_exercise_academy()

    # =========================================================================
    # TAB 4: PROFILE & SETTINGS
    # =========================================================================
    with tab_settings:
        render_settings(user_id)


def render_workout_studio():
    workout_started = st.session_state.get("workout_started", False)

    # Coach spoken feedback banner
    if st.session_state.get("coach_feedback"):
        st.markdown(
            f"""
            <div style="background: rgba(0, 240, 255, 0.08); border-left: 4px solid #00F0FF; padding: 12px 18px; border-radius: 8px; margin-bottom: 1.25rem;">
                <span style="color: #00F0FF; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">🎙️ Live Coach Cue:</span>
                <p style="margin: 4px 0 0 0; font-size: 1.05rem; color: #FFFFFF; font-weight: 500;">
                    "{st.session_state.coach_feedback}"
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    if not workout_started:
        # Pre-workout Plan Configuration
        st.markdown("### 🎯 Setup Your Workout Session")
        col_plan, col_preview = st.columns([1.2, 1])

        with col_plan:
            with st.container(border=True):
                plan_exercise = st.selectbox(
                    "Choose Exercise",
                    options=EXERCISE_OPTIONS,
                    index=EXERCISE_OPTIONS.index(st.session_state.get("plan_exercise", "Squats")) if st.session_state.get("plan_exercise", "Squats") in EXERCISE_OPTIONS else 0,
                    key="plan_exercise_input"
                )

                is_plank = plan_exercise == "Plank"
                rep_label = "Target Hold Time (Seconds)" if is_plank else "Reps per Set"
                default_reps = 30 if is_plank else 10

                col_s, col_r = st.columns(2)
                with col_s:
                    plan_sets = st.number_input("Target Sets", min_value=1, max_value=20, value=int(st.session_state.get("plan_sets", 3)), step=1)
                with col_r:
                    plan_reps = st.number_input(rep_label, min_value=1, max_value=300, value=int(st.session_state.get("plan_reps", default_reps)), step=5 if is_plank else 1)

                met_val = EXERCISE_MET.get(plan_exercise, 5.0)
                user_weight = st.session_state.get("user_weight", 70.0)
                est_time_sec = (plan_sets * plan_reps * 3) if not is_plank else (plan_sets * plan_reps)
                est_cals = round(met_val * user_weight * (est_time_sec / 3600.0), 1)

                st.caption(f"🔥 Est. Energy Output: ~**{est_cals} kcal** ({round(est_time_sec / 60, 1)} mins active work)")

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                start_btn = st.button("🚀 Start Workout Session", type="primary", use_container_width=True)

                if start_btn:
                    st.session_state.exercise_type = plan_exercise
                    st.session_state.target_sets = int(plan_sets)
                    st.session_state.reps_per_set = int(plan_reps)
                    st.session_state.reps = 0
                    st.session_state.sets_completed = 0
                    st.session_state.current_set_reps = 0
                    st.session_state.workout_started = True
                    st.session_state.workout_completed = False
                    st.session_state.workout_started_at = time.time()
                    st.session_state.set_cycle_started_at = time.time()
                    st.session_state.last_saved_sets_completed = 0
                    st.session_state.session_calories = 0.0
                    st.session_state.session_form_score = 100.0
                    st.session_state.form_total_samples = 0
                    st.session_state.form_clean_samples = 0
                    st.session_state.rest_timer_active = False

                    if st.session_state.voice_pipeline:
                        result = st.session_state.voice_pipeline.process_event(
                            event="workout_started",
                            exercise=plan_exercise,
                            metrics={}
                        )
                        if result:
                            st.session_state.audio_to_play, st.session_state.coach_feedback = result

                    st.session_state.last_notified_sets_completed = 0
                    st.session_state.last_notified_workout_complete = False
                    st.rerun()

        with col_preview:
            guide = EXERCISE_GUIDES.get(plan_exercise, {})
            with st.container(border=True):
                st.markdown(f"#### 💡 {guide.get('title', plan_exercise)}")
                st.markdown(f"**Target Muscles:** `{guide.get('target_muscles', 'Core')}`")
                st.markdown(f"**Form Standard:** {guide.get('ideal_form', '')}")
                st.markdown("**Key Faults to Avoid:**")
                for err in guide.get("common_mistakes", []):
                    st.markdown(f"- ⚠️ {err}")
    else:
        # Live Workout Active Screen
        render_active_workout_screen()


def render_active_workout_screen():
    exercise = st.session_state.get("exercise_type", "Squats")
    target_sets = st.session_state.get("target_sets", 3)
    reps_per_set = st.session_state.get("reps_per_set", 10)
    sets_completed = st.session_state.get("sets_completed", 0)
    current_reps = st.session_state.get("current_set_reps", 0)
    total_reps = st.session_state.get("reps", 0)
    calories = st.session_state.get("session_calories", 0.0)
    form_score = st.session_state.get("session_form_score", 100.0)
    is_plank = exercise == "Plank"
    rep_unit = "sec" if is_plank else "reps"

    # Rest Interval Countdown Banner
    if st.session_state.get("rest_timer_active", False):
        rest_start = st.session_state.get("rest_start_time", time.time())
        rest_duration = st.session_state.get("rest_duration", 45)
        elapsed_rest = time.time() - rest_start
        remaining_rest = max(0, int(rest_duration - elapsed_rest))

        if remaining_rest <= 0:
            st.session_state.rest_timer_active = False
            if st.session_state.voice_pipeline:
                result = st.session_state.voice_pipeline.process_event(
                    event="rest_ended",
                    exercise=exercise,
                    metrics={"issue": "Rest period finished! Time for the next set!"}
                )
                if result:
                    st.session_state.audio_to_play, st.session_state.coach_feedback = result
            st.rerun()
        else:
            with st.container(border=True):
                c_t1, c_t2, c_t3 = st.columns([2, 1, 1])
                with c_t1:
                    st.markdown(f"### ⏳ Rest Interval: **{remaining_rest}s remaining**")
                    st.progress((rest_duration - remaining_rest) / float(rest_duration))
                with c_t2:
                    st.caption("Catch your breath and hydrate before your next set.")
                with c_t3:
                    if st.button("Skip Rest →", use_container_width=True):
                        st.session_state.rest_timer_active = False
                        st.rerun()

    col_cam, col_metrics = st.columns([1.5, 1])

    with col_cam:
        with st.container(border=True):
            sub_col1, sub_col2 = st.columns([3, 1])
            with sub_col1:
                st.markdown(f"<span class='live-indicator'></span> **LIVE SESSION: {exercise.upper()}**", unsafe_allow_html=True)
            with sub_col2:
                if st.button("⏹️ End Workout", key="end_workout_btn", use_container_width=True):
                    st.session_state.workout_started = False
                    st.session_state.workout_completed = True
                    if st.session_state.voice_pipeline:
                        result = st.session_state.voice_pipeline.process_event(
                            event="workout_completed",
                            exercise=exercise,
                            metrics={}
                        )
                        if result:
                            st.session_state.audio_to_play, st.session_state.coach_feedback = result
                    st.rerun()

            context = webrtc_streamer(
                key="exercise-analysis",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=VideoProcessorClass,
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True
            )

            sync_metrics_update(context)

            if context.state.playing:
                time.sleep(0.25)
                st.rerun()

            inject_webrtc_styles()

    with col_metrics:
        # Progress Cards
        with st.container(border=True):
            st.markdown("#### ⚡ Real-Time Counters")
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Current Set", f"{current_reps} / {reps_per_set} {rep_unit}")
            with m2:
                st.metric("Sets Logged", f"{sets_completed} / {target_sets}")

            # Set Progress bar
            progress_ratio = min(1.0, current_reps / max(1, reps_per_set))
            st.progress(progress_ratio)

            m3, m4 = st.columns(2)
            with m3:
                st.metric("Total Output", f"{total_reps} {rep_unit}")
            with m4:
                st.metric("Calories Burned", f"{calories} kcal")

        # Form Accuracy Meter
        with st.container(border=True):
            st.markdown("#### 🛡️ Form Integrity")
            form_color = "#10B981" if form_score >= 85 else ("#F59E0B" if form_score >= 70 else "#EF4444")
            form_status = "EXCELLENT" if form_score >= 85 else ("GOOD" if form_score >= 70 else "NEEDS WORK")

            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 1.6rem; font-weight: 800; color: {form_color};">{form_score}%</span>
                    <span style="background: rgba(255, 255, 255, 0.08); padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 700; color: {form_color};">
                        {form_status}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.progress(max(0.0, min(1.0, form_score / 100.0)))

        # Specific Exercise Angles & Biometrics
        with st.container(border=True):
            st.markdown("#### 📐 Biometric Telemetry")
            if exercise == "Squats":
                s1, s2 = st.columns(2)
                with s1:
                    st.metric("Knee Angle", f"{st.session_state.get('knee_angle', 0)}°")
                with s2:
                    st.metric("Back Angle", f"{st.session_state.get('back_angle', 0)}°")
                st.markdown(f"**Depth Status:** `{st.session_state.get('depth_status', 'N/A')}`")

            elif exercise == "Push-ups":
                p1, p2 = st.columns(2)
                with p1:
                    st.metric("Elbow Angle", f"{st.session_state.get('elbow_angle', 0)}°")
                with p2:
                    st.metric("Hip Alignment", st.session_state.get('hip_status', 'N/A'))
                st.markdown(f"**Body Alignment:** `{st.session_state.get('body_alignment', 'N/A')}`")

            elif exercise == "Biceps Curls (Dumbbell)":
                b1, b2 = st.columns(2)
                with b1:
                    st.metric("Elbow Flex", f"{st.session_state.get('elbow_angle', 0)}°")
                with b2:
                    st.metric("Shoulder", st.session_state.get('shoulder_status', 'N/A'))
                st.markdown(f"**Torso Swing:** `{st.session_state.get('swing_status', 'N/A')}`")

            elif exercise == "Shoulder Press":
                sh1, sh2 = st.columns(2)
                with sh1:
                    st.metric("Elbow Angle", f"{st.session_state.get('elbow_angle', 0)}°")
                with sh2:
                    st.metric("Extension", st.session_state.get('extension_status', 'N/A'))
                st.markdown(f"**Spine Arch:** `{st.session_state.get('back_arch_status', 'N/A')}`")

            elif exercise == "Lunges":
                l1, l2 = st.columns(2)
                with l1:
                    st.metric("Lead Knee", f"{st.session_state.get('front_knee_angle', 0)}°")
                with l2:
                    st.metric("Torso Tilt", f"{st.session_state.get('torso_angle', 0)}°")
                st.markdown(f"**Balance:** `{st.session_state.get('balance_status', 'N/A')}`")

            elif exercise == "Jumping Jacks":
                j1, j2 = st.columns(2)
                with j1:
                    st.metric("Arm Sweep", f"{st.session_state.get('arm_angle', 0)}°")
                with j2:
                    st.metric("Leg Spread", f"{st.session_state.get('leg_spread_ratio', 1.0)}x")
                st.markdown(f"**Motion Phase:** `{st.session_state.get('motion_phase', 'READY')}`")

            elif exercise == "Plank":
                pl1, pl2 = st.columns(2)
                with pl1:
                    st.metric("Hold Time", f"{st.session_state.get('hold_seconds', 0)}s")
                with pl2:
                    st.metric("Hip Position", st.session_state.get('hip_status', 'N/A'))
                st.markdown(f"**Core Rigidness:** `{st.session_state.get('body_alignment', 'N/A')}`")

        # Quick Rest Trigger
        if not st.session_state.get("rest_timer_active", False):
            if st.button("⏱️ Take Rest Interval", use_container_width=True):
                st.session_state.rest_timer_active = True
                st.session_state.rest_start_time = time.time()
                st.session_state.rest_duration = st.session_state.get("rest_interval_seconds", 45)
                st.rerun()


def render_analytics(user_id: int):
    st.markdown("### 📊 Workout Analytics & Progress")

    stats = get_user_stats(user_id)
    profile = get_user_profile(user_id)
    daily_goal = profile.get("daily_goal_reps", 50)
    today_reps = stats.get("today_reps", 0)

    # Top KPI Strip
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("🔥 Workout Streak", f"{stats.get('streak_days', 0)} Days")
    with kpi2:
        st.metric("Total Reps Logged", f"{stats.get('total_reps', 0):,}")
    with kpi3:
        st.metric("Total Calories", f"{stats.get('total_calories', 0):,.1f} kcal")
    with kpi4:
        st.metric("Average Form Score", f"{stats.get('avg_form_score', 100.0):.1f}%")
    with kpi5:
        total_mins = round(stats.get('total_time', 0) / 60, 1)
        st.metric("Total Time", f"{total_mins} mins")

    # Daily Goal Progress
    with st.container(border=True):
        goal_pct = min(1.0, today_reps / max(1, daily_goal))
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>🎯 Today's Rep Goal: {today_reps} / {daily_goal} Reps</strong>
                <span style="color:#00F0FF; font-weight:700;">{int(goal_pct * 100)}%</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.progress(goal_pct)

    # History Data
    raw_history = get_users_exercises(user_id)
    if not raw_history:
        st.info("No workout sessions recorded yet. Complete your first workout in the Studio to view trends and charts!")
        return

    df = pd.DataFrame([dict(r) for r in raw_history])
    df["Date"] = pd.to_datetime(df["created_at"]).dt.date

    # Interactive Visual Charts
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        with st.container(border=True):
            st.markdown("#### 📈 Daily Rep Volume")
            daily_reps = df.groupby("Date")["reps"].sum().reset_index()
            daily_reps = daily_reps.sort_values("Date")
            daily_reps.set_index("Date", inplace=True)
            st.bar_chart(daily_reps["reps"], color="#00F0FF")

    with col_chart2:
        with st.container(border=True):
            st.markdown("#### ⚡ Exercise Distribution")
            ex_dist = df.groupby("exercise_name")["reps"].sum().reset_index()
            ex_dist.set_index("exercise_name", inplace=True)
            st.bar_chart(ex_dist["reps"], color="#10B981")

    # Personal Records (PRs)
    prs = get_user_personal_records(user_id)
    if prs:
        st.markdown("#### 🏆 Personal Records (PRs)")
        pr_cols = st.columns(min(len(prs), 4))
        for idx, pr in enumerate(prs[:4]):
            with pr_cols[idx]:
                with st.container(border=True):
                    st.caption(f"🎖️ {pr['exercise_name']}")
                    st.markdown(f"### {pr['max_reps']} Reps")
                    st.caption(f"Best Sets: {pr['max_sets']} | Max Cals: {pr['max_calories']} kcal")

    # Detailed Log Table with Filters & CSV Export
    st.markdown("#### 📋 Session Log")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        filter_ex = st.multiselect("Filter by Exercise", options=df["exercise_name"].unique())
    with col_f2:
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export History (CSV)",
            data=csv_data,
            file_name=f"workout_history_{user_id}.csv",
            mime="text/csv",
            use_container_width=True
        )

    filtered_df = df if not filter_ex else df[df["exercise_name"].isin(filter_ex)]
    display_df = filtered_df[["exercise_name", "reps", "sets", "calories", "form_score", "time", "Date"]].copy()
    display_df.rename(columns={
        "exercise_name": "Exercise",
        "reps": "Reps",
        "sets": "Sets",
        "calories": "Calories (kcal)",
        "form_score": "Form Score (%)",
        "time": "Time (s)",
        "Date": "Date"
    }, inplace=True)
    display_df.index = range(1, len(display_df) + 1)
    st.dataframe(display_df, use_container_width=True)


def render_exercise_academy():
    st.markdown("### 📖 Exercise Academy & Form Library")
    st.caption("Master pristine biomechanics, joint angles, and safety tips for every movement.")

    selected_ex = st.selectbox("Select Exercise Guide", options=EXERCISE_OPTIONS)
    guide = EXERCISE_GUIDES.get(selected_ex, {})

    col_g1, col_g2 = st.columns([1.5, 1])

    with col_g1:
        with st.container(border=True):
            st.markdown(f"## {guide.get('title', selected_ex)}")
            st.markdown(f"**Target Muscle Groups:** `{guide.get('target_muscles', 'Core')}`")
            st.markdown(f"**Experience Level:** `{guide.get('difficulty', 'Intermediate')}`")
            st.divider()

            st.markdown("#### 🎯 Execution Standard")
            st.write(guide.get("ideal_form", ""))

            st.markdown("#### ⚠️ Common Biomechanical Mistakes")
            for mistake in guide.get("common_mistakes", []):
                st.markdown(f"- ❌ **{mistake}**")

    with col_g2:
        with st.container(border=True):
            st.markdown("#### 🤖 AI Vision Detection Points")
            if selected_ex == "Squats":
                st.markdown("- **Hip-Knee-Ankle Angle:** Monitored for parallel depth (≤ 100°).")
                st.markdown("- **Torso-Spine Angle:** Checked to prevent excessive forward tilt.")
            elif selected_ex == "Push-ups":
                st.markdown("- **Elbow Angle:** Target 90° flexion at bottom.")
                st.markdown("- **Plank Hip Line:** Detects sagging lumbar and piked hips.")
            elif selected_ex == "Biceps Curls (Dumbbell)":
                st.markdown("- **Elbow Drift:** Monitors elbow stability against ribs.")
                st.markdown("- **Torso Sway:** Flags cheating with back momentum.")
            elif selected_ex == "Shoulder Press":
                st.markdown("- **Overhead Lockout:** Target 160°+ extension.")
                st.markdown("- **Lower Back Arch:** Prevents excessive lumbar extension.")
            elif selected_ex == "Lunges":
                st.markdown("- **Front Knee Angle:** 90° depth target.")
                st.markdown("- **Lateral Balance:** Tracks shoulder-hip center alignment.")
            elif selected_ex == "Jumping Jacks":
                st.markdown("- **Arm Abduction:** Tracks full sweep above 120°.")
                st.markdown("- **Leg Spread:** Ensures dynamic athletic lateral jump.")
            elif selected_ex == "Plank":
                st.markdown("- **Core Alignment:** Straight 160°-180° rigid line.")
                st.markdown("- **Hold Accumulator:** Only ticks when posture is correct.")

            st.info("💡 Make sure your whole body is visible in the webcam for optimal accuracy.")


def render_settings(user_id: int):
    st.markdown("### ⚙️ Athlete Profile & Coach Customization")

    profile = get_user_profile(user_id)

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### 👤 Athlete Biometrics")
            with st.form("athlete_profile_form"):
                weight = st.number_input("Body Weight (kg)", min_value=30.0, max_value=250.0, value=profile.get("weight_kg", 70.0), step=0.5)
                daily_goal = st.number_input("Daily Rep Goal", min_value=10, max_value=1000, value=profile.get("daily_goal_reps", 50), step=10)
                rest_time = st.number_input("Default Rest Interval (Seconds)", min_value=15, max_value=300, value=int(st.session_state.get("rest_interval_seconds", 45)), step=5)

                save_profile_btn = st.form_submit_button("Save Biometrics", use_container_width=True)

                if save_profile_btn:
                    st.session_state.user_weight = weight
                    st.session_state.daily_goal_reps = daily_goal
                    st.session_state.rest_interval_seconds = rest_time
                    save_user_profile(
                        user_id=user_id,
                        weight_kg=weight,
                        daily_goal_reps=daily_goal,
                        coach_personality=st.session_state.get("coach_personality", "Motivational"),
                        voice_enabled=st.session_state.get("voice_enabled", True)
                    )
                    st.success("Profile biometrics updated successfully!")

    with col2:
        with st.container(border=True):
            st.markdown("#### 🤖 AI Coach Persona & Engine")
            personas_list = list(COACH_PERSONAS.keys())
            current_persona = profile.get("coach_personality", "Motivational")
            current_idx = personas_list.index(current_persona) if current_persona in personas_list else 0

            chosen_persona = st.selectbox("Coach Personality", options=personas_list, index=current_idx)
            st.caption(COACH_PERSONAS.get(chosen_persona, {}).get("desc", ""))

            voice_toggle = st.toggle("Enable Voice Audio Cues (TTS)", value=st.session_state.get("voice_enabled", True))

            st.divider()
            st.markdown("##### 🔑 Groq LLaMA 3.3 Engine")
            active_key, key_src = resolve_groq_api_key()

            if active_key:
                masked = active_key[:7] + "..." + active_key[-4:] if len(active_key) > 12 else "********"
                st.success(f"🟢 **Active Engine:** Groq LLaMA 3.3 connected via `{key_src}` (`{masked}`)")
            else:
                st.info("ℹ️ Running on **Smart Offline Engine**. To use LLaMA 3.3, provide an API key via PowerShell terminal or below.")

            with st.expander("💻 How to set from PowerShell Terminal"):
                st.code(
                    '# Option A: Set environment variable before running\n'
                    '$env:GROQ_API_KEY = "gsk_your_actual_key_here"\n'
                    'streamlit run main.py\n\n'
                    '# Option B: Pass directly as a CLI argument\n'
                    'streamlit run main.py -- --groq-api-key "gsk_your_actual_key_here"',
                    language="powershell"
                )

            user_groq_key = st.text_input("Or enter Groq API Key manually", type="password", value=st.session_state.get("groq_api_key", ""), placeholder="gsk_...")

            if st.button("Apply Coach Settings", type="primary", use_container_width=True):
                st.session_state.coach_personality = chosen_persona
                st.session_state.voice_enabled = voice_toggle
                st.session_state.groq_api_key = user_groq_key.strip()
                save_user_profile(
                    user_id=user_id,
                    weight_kg=st.session_state.get("user_weight", 70.0),
                    daily_goal_reps=st.session_state.get("daily_goal_reps", 50),
                    coach_personality=chosen_persona,
                    voice_enabled=voice_toggle
                )
                setup_voice_pipeline()
                st.success("Coach preferences and engine updated!")

    # Danger Zone / Account Management
    st.divider()
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("🚪 Switch Athlete / Log Out", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

    with col_d2:
        with st.expander("⚠️ Reset Workout Logs"):
            st.warning("This will permanently delete all workout history for this user.")
            if st.button("Confirm Delete History", type="secondary"):
                delete_user_history(user_id)
                st.success("Workout history cleared.")
                st.rerun()


if __name__ == "__main__":
    main()
