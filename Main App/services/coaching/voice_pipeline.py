import time
import streamlit as st


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0
        self.enabled = True

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def _find_form_issue(self, exercise, metrics):
        if not metrics:
            return None

        if "issue" in metrics and metrics["issue"]:
            return metrics["issue"]

        if "form_issue" in metrics and metrics["form_issue"]:
            return metrics["form_issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", 180)

            if depth == "TOO HIGH":
                return "The user's squat is not deep enough — knees are not bending sufficiently."
            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "The user is leaning too far forward during the squat."

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")

            if alignment == "Poor Form":
                return "The user's body is not straight during the push-up."
            if hip_status == "SAGGING":
                return "The user's hips are sagging down during the push-up."
            if hip_status == "PIKED UP":
                return "The user's hips are too high — lower them to form a straight line."

        elif exercise == "Biceps Curls (Dumbbell)":
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")

            if swing == "SWINGING":
                return "The user is swinging their torso during the curl — keep the body still."
            if shoulder == "ELBOW DRIFTING":
                return "The user's elbow is drifting away from their side during the curl."

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")
            if back_arch == "Excessive Arch":
                return "The user is arching their lower back excessively during the press."
            if back_arch == "Slight Arch":
                return "Slight back arch detected — encourage the user to brace their core."

        elif exercise == "Lunges":
            balance = metrics.get("balance_status", "")
            if balance == "OFF BALANCE":
                return "The user is losing balance during the lunge — feet should be hip-width apart."

        elif exercise == "Jumping Jacks":
            phase = metrics.get("motion_phase", "")
            arm = metrics.get("arm_angle", 0)
            if phase == "PEAK EXTENSION" and arm < 115:
                return "Raise arms higher overhead for full range!"

        elif exercise == "Plank":
            hip_status = metrics.get("hip_status", "")
            if hip_status == "SAGGING":
                return "The user's hips are sagging — lift hips and squeeze core!"
            if hip_status == "PIKED UP":
                return "The user's hips are piked too high — lower hips into a straight plank line!"

        return None

    def process_event(self, event, exercise, metrics):
        issue = self._find_form_issue(exercise, metrics)
        now = time.time()

        is_major_event = event in ["workout_started", "set_completed", "workout_completed", "rest_ended"]

        if not is_major_event:
            if not issue:
                return None
            if now - self.last_spoken_at < 6.0:
                return None

        text = self.llm.give_feedback(event, issue)
        voice = None

        if self.enabled and self.tts:
            try:
                voice = self.tts.speak(text)
            except Exception:
                voice = None

        self.last_spoken_at = now
        return voice, text


def autoplay_audio(audio_bytes):
    if not audio_bytes:
        return

    st.markdown("<style>[data-testid='stAudio'] {display: none;}</style>", unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
