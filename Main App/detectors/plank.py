import time
from core.base_exercise import BaseExercise


class PlankDetector(BaseExercise):
    MIN_VISIBILITY = 0.6
    HIP_SAG_TOLERANCE = 0.07

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()
        self.hold_seconds = 0.0
        self.last_timestamp = None
        self.is_holding = False

    def reset(self) -> None:
        self.reps = 0
        self.hold_seconds = 0.0
        self.last_timestamp = None
        self.is_holding = False

    def process(self, landmarks) -> dict:
        now = time.time()
        dt = 0.0
        if self.last_timestamp is not None:
            dt = min(1.0, max(0.0, now - self.last_timestamp))
        self.last_timestamp = now

        left_vis = landmarks[self.LEFT_HIP].visibility
        right_vis = landmarks[self.RIGHT_HIP].visibility

        if left_vis >= right_vis:
            sh_idx, hip_idx, ank_idx = self.LEFT_SHOULDER, self.LEFT_HIP, self.LEFT_ANKLE
        else:
            sh_idx, hip_idx, ank_idx = self.RIGHT_SHOULDER, self.RIGHT_HIP, self.RIGHT_ANKLE

        sh_pt = self.get_point(landmarks, sh_idx)
        hip_pt = self.get_point(landmarks, hip_idx)
        ank_pt = self.get_point(landmarks, ank_idx)

        body_angle = self.calculate_angle(sh_pt, hip_pt, ank_pt)

        # Vertical alignment comparison (y coordinates in normalized image)
        expected_hip_y = (landmarks[sh_idx].y + landmarks[ank_idx].y) / 2.0
        hip_deviation = landmarks[hip_idx].y - expected_hip_y

        key_visible = (
            landmarks[sh_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[hip_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[ank_idx].visibility >= self.MIN_VISIBILITY
        )

        issue = None
        if key_visible:
            if hip_deviation > self.HIP_SAG_TOLERANCE:
                hip_status = "SAGGING"
                issue = "Lift your hips up to keep your core engaged!"
            elif hip_deviation < -self.HIP_SAG_TOLERANCE:
                hip_status = "PIKED UP"
                issue = "Lower your hips to create a flat line!"
            else:
                hip_status = "LEVEL (PERFECT)"

            if body_angle >= 160:
                body_alignment = "Solid Plank"
            elif body_angle >= 145:
                body_alignment = "Slight Bend"
            else:
                body_alignment = "Poor Alignment"

            # Only accumulate hold time if form is acceptable
            if hip_status == "LEVEL (PERFECT)" and body_angle >= 150:
                self.hold_seconds += dt
                self.is_holding = True
            else:
                self.is_holding = False
        else:
            hip_status = "NO POSE"
            body_alignment = "N/A"
            self.is_holding = False

        self.reps = int(self.hold_seconds)

        return {
            "reps": self.reps,
            "hold_seconds": int(self.hold_seconds),
            "body_alignment": body_alignment,
            "hip_status": hip_status,
            "form_issue": issue,
            "is_clean": issue is None and self.is_holding
        }
