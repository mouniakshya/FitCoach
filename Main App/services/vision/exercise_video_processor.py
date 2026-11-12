import os
import cv2
import av
import numpy as np
import mediapipe as mp
import threading
from streamlit_webrtc import VideoProcessorBase
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from detectors.squat import SquatDetector
from detectors.pushup import PushUpDetector
from detectors.biceps_curl import BicepsCurlDetector
from detectors.shoulder_press import ShoulderPressDetector
from detectors.lunges import LungesDetector
from detectors.jumping_jacks import JumpingJacksDetector
from detectors.plank import PlankDetector
from services.config.workout_config import POSE_CONNECTIONS


class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"

        model_path = os.path.join(os.getcwd(), "ml_models", "pose_landmarker_full.task")
        base_option = python.BaseOptions(model_asset_path=model_path)

        options = vision.PoseLandmarkerOptions(
            base_options=base_option,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.65,
            min_pose_presence_confidence=0.65,
            min_tracking_confidence=0.65,
            output_segmentation_masks=False
        )

        self._landmarker = vision.PoseLandmarker.create_from_options(options)

        self._detectors = {
            "Squats": SquatDetector(),
            "Push-ups": PushUpDetector(),
            "Biceps Curls (Dumbbell)": BicepsCurlDetector(),
            "Shoulder Press": ShoulderPressDetector(),
            "Lunges": LungesDetector(),
            "Jumping Jacks": JumpingJacksDetector(),
            "Plank": PlankDetector(),
        }

        self._frame_timestamps_ms = 0

    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()

    def set_exercise(self, exercise_type):
        with self._lock:
            if exercise_type != self._exercise_type:
                self._exercise_type = exercise_type
                detector = self._detectors.get(exercise_type)
                if detector:
                    detector.reset()

    def get_exercise(self):
        with self._lock:
            return self._exercise_type

    def _draw_hud_card(self, img, x, y, w, h, bg_color=(20, 24, 33), border_color=(0, 240, 255), alpha=0.75):
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), bg_color, -1)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        cv2.rectangle(img, (x, y), (x + w, y + h), border_color, 2)

    def _draw_skeleton(self, img, landmarks, has_error=False):
        h, w = img.shape[:2]
        line_color = (0, 160, 255) if has_error else (0, 230, 118)  # Amber if error, Emerald if clean
        joint_color = (255, 220, 0)

        for start_idx, end_idx in POSE_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]

            if p1.visibility > 0.6 and p2.visibility > 0.6:
                cv2.line(
                    img,
                    (int(p1.x * w), int(p1.y * h)),
                    (int(p2.x * w), int(p2.y * h)),
                    line_color,
                    5,
                    cv2.LINE_AA
                )

        for lm in landmarks:
            if lm.visibility > 0.6:
                cv2.circle(
                    img,
                    (int(lm.x * w), int(lm.y * h)),
                    6,
                    joint_color,
                    -1,
                    cv2.LINE_AA
                )
                cv2.circle(
                    img,
                    (int(lm.x * w), int(lm.y * h)),
                    7,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )

    def _draw_no_pose_warnings(self, img):
        h, w = img.shape[:2]
        card_w, card_h = min(420, w - 40), 90
        card_x = (w - card_w) // 2
        card_y = 40
        self._draw_hud_card(img, card_x, card_y, card_w, card_h, bg_color=(15, 18, 25), border_color=(0, 165, 255), alpha=0.85)

        cv2.putText(
            img,
            "NO POSE DETECTED",
            (card_x + 25, card_y + 38),
            cv2.FONT_HERSHEY_DUPLEX,
            0.85,
            (0, 180, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            img,
            "Step into frame & face camera",
            (card_x + 25, card_y + 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )

    def _draw_overlays(self, img, metrics, ex_type):
        h, w = img.shape[:2]

        # Top HUD Bar
        self._draw_hud_card(img, 15, 15, w - 30, 60, bg_color=(12, 16, 24), border_color=(0, 200, 255), alpha=0.7)
        cv2.putText(
            img,
            f"FITCOACH: {ex_type.upper()}",
            (30, 52),
            cv2.FONT_HERSHEY_DUPLEX,
            0.75,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        reps_val = metrics.get("reps", 0)
        rep_label = "SEC" if ex_type == "Plank" else "REPS"
        reps_text = f"{reps_val} {rep_label}"
        text_size = cv2.getTextSize(reps_text, cv2.FONT_HERSHEY_DUPLEX, 0.9, 2)[0]
        cv2.putText(
            img,
            reps_text,
            (w - 30 - text_size[0] - 15, 53),
            cv2.FONT_HERSHEY_DUPLEX,
            0.9,
            (0, 240, 255),
            2,
            cv2.LINE_AA
        )

        # Bottom HUD for specific exercise telemetry
        if ex_type == "Squats":
            self._draw_squats_overlays(img, metrics)
        elif ex_type == "Push-ups":
            self._draw_pushup_overlays(img, metrics)
        elif ex_type == "Biceps Curls (Dumbbell)":
            self._draw_curl_overlays(img, metrics)
        elif ex_type == "Shoulder Press":
            self._draw_press_overlays(img, metrics)
        elif ex_type == "Lunges":
            self._draw_lunge_overlays(img, metrics)
        elif ex_type == "Jumping Jacks":
            self._draw_jumping_jacks_overlays(img, metrics)
        elif ex_type == "Plank":
            self._draw_plank_overlays(img, metrics)

    def _draw_squats_overlays(self, img, metrics):
        h, w = img.shape[:2]
        depth = metrics.get("depth_status", "N/A")
        knee = metrics.get("knee_angle", 0)
        is_good = "GOOD" in depth or depth == "STANDING"
        border = (0, 230, 118) if is_good else (0, 165, 255)

        self._draw_hud_card(img, 15, h - 65, w - 30, 50, border_color=border)
        status_text = f"KNEE: {knee} deg  |  DEPTH: {depth}"
        cv2.putText(img, status_text, (30, h - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (255, 255, 255), 2, cv2.LINE_AA)

    def _draw_pushup_overlays(self, img, metrics):
        h, w = img.shape[:2]
        align = metrics.get("body_alignment", "N/A")
        hip = metrics.get("hip_status", "N/A")
        elbow = metrics.get("elbow_angle", 0)
        is_good = align == "Straight" and hip == "LEVEL"
        border = (0, 230, 118) if is_good else (0, 80, 255)

        self._draw_hud_card(img, 15, h - 65, w - 30, 50, border_color=border)
        status_text = f"ELBOW: {elbow} deg  |  BODY: {align}  |  HIP: {hip}"
        cv2.putText(img, status_text, (30, h - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

    def _draw_curl_overlays(self, img, metrics):
        h, w = img.shape[:2]
        swing = metrics.get("swing_status", "N/A")
        shoulder = metrics.get("shoulder_status", "N/A")
        elbow = metrics.get("elbow_angle", 0)
        is_good = swing == "NO SWING" and shoulder == "STABLE"
        border = (0, 230, 118) if is_good else (0, 165, 255)

        self._draw_hud_card(img, 15, h - 65, w - 30, 50, border_color=border)
        status_text = f"ELBOW: {elbow} deg  |  STABILITY: {shoulder}  |  SWING: {swing}"
        cv2.putText(img, status_text, (30, h - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

    def _draw_press_overlays(self, img, metrics):
        h, w = img.shape[:2]
        ext = metrics.get("extension_status", "N/A")
        arch = metrics.get("back_arch_status", "N/A")
        elbow = metrics.get("elbow_angle", 0)
        is_good = arch in ["Neutral", "Slight Arch"]
        border = (0, 230, 118) if is_good else (0, 80, 255)

        self._draw_hud_card(img, 15, h - 65, w - 30, 50, border_color=border)
        status_text = f"ELBOW: {elbow} deg  |  EXT: {ext}  |  BACK: {arch}"
        cv2.putText(img, status_text, (30, h - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

    def _draw_lunge_overlays(self, img, metrics):
        h, w = img.shape[:2]
        bal = metrics.get("balance_status", "N/A")
        knee = metrics.get("front_knee_angle", 0)
        is_good = bal == "BALANCED"
        border = (0, 230, 118) if is_good else (0, 165, 255)

        self._draw_hud_card(img, 15, h - 65, w - 30, 50, border_color=border)
        status_text = f"KNEE: {knee} deg  |  BALANCE: {bal}"
        cv2.putText(img, status_text, (30, h - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (255, 255, 255), 2, cv2.LINE_AA)

    def _draw_jumping_jacks_overlays(self, img, metrics):
        h, w = img.shape[:2]
        phase = metrics.get("motion_phase", "READY")
        ratio = metrics.get("leg_spread_ratio", 1.0)
        arm = metrics.get("arm_angle", 0)

        self._draw_hud_card(img, 15, h - 65, w - 30, 50, border_color=(0, 240, 255))
        status_text = f"ARM: {arm} deg  |  SPREAD: {ratio}x  |  PHASE: {phase}"
        cv2.putText(img, status_text, (30, h - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

    def _draw_plank_overlays(self, img, metrics):
        h, w = img.shape[:2]
        align = metrics.get("body_alignment", "N/A")
        hip = metrics.get("hip_status", "N/A")
        is_good = "PERFECT" in hip or "Solid" in align
        border = (0, 230, 118) if is_good else (0, 80, 255)

        self._draw_hud_card(img, 15, h - 65, w - 30, 50, border_color=border)
        status_text = f"CORE: {align}  |  HIP: {hip}"
        cv2.putText(img, status_text, (30, h - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (255, 255, 255), 2, cv2.LINE_AA)

    def recv(self, frame):
        image = np.asarray(
            cv2.flip(frame.to_ndarray(format="bgr24"), 1),
            dtype=np.uint8
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        )

        self._frame_timestamps_ms += 30
        result = self._landmarker.detect_for_video(mp_image, self._frame_timestamps_ms)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            ex_type = self.get_exercise()
            detector = self._detectors.get(ex_type)

            has_error = False
            if detector:
                metrics = detector.process(landmarks)
                metrics["pose_detected"] = True
                has_error = metrics.get("form_issue") is not None
                self._draw_skeleton(image, landmarks, has_error=has_error)
                self._draw_overlays(image, metrics, ex_type)
                self.set_latest_metrics(metrics)
            else:
                self._draw_skeleton(image, landmarks, has_error=False)
        else:
            self._draw_no_pose_warnings(image)

            with self._lock:
                if self._latest_metrics is not None:
                    self._latest_metrics["pose_detected"] = False
                else:
                    self._latest_metrics = {"pose_detected": False}

        return av.VideoFrame.from_ndarray(image, format="bgr24")
