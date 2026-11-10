import math
from core.base_exercise import BaseExercise


class JumpingJacksDetector(BaseExercise):
    MIN_VISIBILITY = 0.6
    ARM_OPEN_ANGLE = 120
    ARM_CLOSED_ANGLE = 50
    LEG_SPREAD_OPEN_RATIO = 1.35
    LEG_SPREAD_CLOSED_RATIO = 1.15

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()
        self.stage = "closed"

    def reset(self) -> None:
        self.reps = 0
        self.stage = "closed"

    def _euclidean_dist(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def process(self, landmarks) -> dict:
        l_sh = self.get_point(landmarks, self.LEFT_SHOULDER)
        r_sh = self.get_point(landmarks, self.RIGHT_SHOULDER)
        l_wr = self.get_point(landmarks, self.LEFT_WRIST)
        r_wr = self.get_point(landmarks, self.RIGHT_WRIST)
        l_hip = self.get_point(landmarks, self.LEFT_HIP)
        r_hip = self.get_point(landmarks, self.RIGHT_HIP)
        l_ank = self.get_point(landmarks, self.LEFT_ANKLE)
        r_ank = self.get_point(landmarks, self.RIGHT_ANKLE)

        # Calculate arm angles (hip-shoulder-wrist)
        left_arm_angle = self.calculate_angle(l_hip, l_sh, l_wr)
        right_arm_angle = self.calculate_angle(r_hip, r_sh, r_wr)
        avg_arm_angle = (left_arm_angle + right_arm_angle) / 2.0

        # Calculate leg spread ratio
        shoulder_dist = max(0.01, self._euclidean_dist(l_sh, r_sh))
        ankle_dist = self._euclidean_dist(l_ank, r_ank)
        spread_ratio = ankle_dist / shoulder_dist

        key_visible = (
            landmarks[self.LEFT_SHOULDER].visibility >= self.MIN_VISIBILITY and
            landmarks[self.RIGHT_SHOULDER].visibility >= self.MIN_VISIBILITY and
            landmarks[self.LEFT_ANKLE].visibility >= self.MIN_VISIBILITY and
            landmarks[self.RIGHT_ANKLE].visibility >= self.MIN_VISIBILITY
        )

        motion_phase = "READY"
        issue = None

        if key_visible:
            is_open = avg_arm_angle >= self.ARM_OPEN_ANGLE and spread_ratio >= self.LEG_SPREAD_OPEN_RATIO
            is_closed = avg_arm_angle <= self.ARM_CLOSED_ANGLE and spread_ratio <= self.LEG_SPREAD_CLOSED_RATIO

            if is_open:
                self.stage = "open"
                motion_phase = "PEAK EXTENSION"
            elif is_closed and self.stage == "open":
                self.stage = "closed"
                self.reps += 1
                motion_phase = "REP COMPLETE"
            elif self.stage == "open":
                motion_phase = "RETURNING"
            else:
                motion_phase = "JUMPING"

            # Form evaluation
            if self.stage == "open" and avg_arm_angle < 115:
                issue = "Raise arms higher overhead for full range!"
            elif self.stage == "open" and spread_ratio < 1.25:
                issue = "Widen your stance during the jump!"

        return {
            "reps": self.reps,
            "arm_angle": int(avg_arm_angle),
            "leg_spread_ratio": round(spread_ratio, 2),
            "motion_phase": motion_phase,
            "form_issue": issue,
            "is_clean": issue is None
        }
