import streamlit as st
import time
from services.config.workout_config import METRICS_FIELDS, EXERCISE_MET
from services.persistence.exercise_repository import add_exercise


def sync_metrics_update(context):
    if not context or not hasattr(context, "state") or not context.state.playing:
        return

    processor = getattr(context, "video_processor", None)
    if not processor:
        return

    exercise = st.session_state.get("exercise_type")
    if not exercise:
        return

    processor.set_exercise(exercise)
    latest_metrics = processor.get_latest_metrics()
    if not latest_metrics:
        return

    reps = latest_metrics.get("reps", 0)
    if reps is None:
        reps = 0

    st.session_state.reps = reps

    fields = METRICS_FIELDS.get(exercise)
    if fields:
        for key, default in fields.items():
            st.session_state[key] = latest_metrics.get(key, default)

    # Form Accuracy calculation
    has_issue = (
        latest_metrics.get("form_issue") is not None or
        latest_metrics.get("depth_status") == "TOO HIGH" or
        latest_metrics.get("body_alignment") == "Poor Form" or
        latest_metrics.get("hip_status") in ["SAGGING", "PIKED UP"] or
        latest_metrics.get("swing_status") == "SWINGING" or
        latest_metrics.get("balance_status") == "OFF BALANCE" or
        latest_metrics.get("back_arch_status") == "Excessive Arch"
    )

    total_samples = st.session_state.get("form_total_samples", 0) + 1
    clean_samples = st.session_state.get("form_clean_samples", 0) + (0 if has_issue else 1)
    st.session_state.form_total_samples = total_samples
    st.session_state.form_clean_samples = clean_samples
    session_form_score = round((clean_samples / max(1, total_samples)) * 100, 1)
    st.session_state.session_form_score = session_form_score

    reps_per_set = st.session_state.get("reps_per_set", 0)
    target_sets = st.session_state.get("target_sets", 0)

    if reps is not None and reps_per_set > 0 and target_sets > 0:
        sets_completed = reps // reps_per_set
        current_set_reps = reps % reps_per_set
        workout_completed = sets_completed >= target_sets
    else:
        sets_completed = 0
        current_set_reps = 0
        workout_completed = False

    st.session_state.sets_completed = sets_completed
    st.session_state.current_set_reps = current_set_reps
    st.session_state.workout_completed = workout_completed

    # Live calories calculation for the active session
    workout_start_ts = st.session_state.get("workout_started_at", time.time())
    elapsed_total_sec = max(1.0, time.time() - workout_start_ts)
    met = EXERCISE_MET.get(exercise, 5.0)
    user_weight = st.session_state.get("user_weight", 70.0)
    st.session_state.session_calories = round(met * user_weight * (elapsed_total_sec / 3600.0), 1)

    last_saved_sets = st.session_state.get("last_saved_sets_completed", 0)

    if target_sets > 0 and reps_per_set > 0 and sets_completed > last_saved_sets:
        newly_completed = sets_completed - last_saved_sets
        now_ts = time.time()
        started_at = st.session_state.get("set_cycle_started_at", now_ts)
        time_taken = max(1.0, now_ts - started_at)
        user_id = st.session_state.get("user_id", 0)

        # Calorie share for this set
        set_calories = round(met * user_weight * (time_taken / 3600.0), 2)

        add_exercise(
            user_id=user_id,
            exercise_name=exercise,
            reps=newly_completed * reps_per_set,
            sets=newly_completed,
            time_taken=int(time_taken),
            calories=set_calories,
            form_score=session_form_score
        )

        # Trigger Rest Interval Timer
        st.session_state.rest_timer_active = True
        st.session_state.rest_start_time = now_ts
        st.session_state.rest_duration = st.session_state.get("rest_interval_seconds", 45)

        if st.session_state.get("voice_pipeline"):
            result = st.session_state.voice_pipeline.process_event(
                event="set_completed",
                exercise=exercise,
                metrics=latest_metrics,
            )
            if result:
                st.session_state.audio_to_play, st.session_state.coach_feedback = result

        st.session_state.set_cycle_started_at = now_ts
        st.session_state.last_saved_sets_completed = sets_completed

    if workout_completed and not st.session_state.get("last_notified_workout_complete", False):
        st.session_state.last_notified_workout_complete = True

        if st.session_state.get("voice_pipeline"):
            result = st.session_state.voice_pipeline.process_event(
                event="workout_completed",
                exercise=exercise,
                metrics=latest_metrics,
            )
            if result:
                st.session_state.audio_to_play, st.session_state.coach_feedback = result

    pose_detected = latest_metrics.get("pose_detected", True)

    if not pose_detected and st.session_state.get("voice_pipeline"):
        result = st.session_state.voice_pipeline.process_event(
            event="no_pose_detected",
            exercise=exercise,
            metrics={"issue": "No pose detected! Please step into the camera frame."},
        )
        if result:
            st.session_state.audio_to_play, st.session_state.coach_feedback = result

    if st.session_state.get("voice_pipeline"):
        result = st.session_state.voice_pipeline.process_event(
            event="ongoing_form_check",
            exercise=exercise,
            metrics=latest_metrics,
        )
        if result:
            st.session_state.audio_to_play, st.session_state.coach_feedback = result
