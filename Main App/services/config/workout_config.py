EXERCISE_OPTIONS = [
    "Squats",
    "Push-ups",
    "Biceps Curls (Dumbbell)",
    "Shoulder Press",
    "Lunges",
    "Jumping Jacks",
    "Plank"
]

EXERCISE_MET = {
    "Squats": 5.5,
    "Push-ups": 8.0,
    "Biceps Curls (Dumbbell)": 4.0,
    "Shoulder Press": 5.0,
    "Lunges": 6.0,
    "Jumping Jacks": 8.5,
    "Plank": 4.0
}

POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),       # Shoulders & Arms
    (11, 23), (12, 24), (23, 24),                           # Torso / Hips
    (23, 25), (24, 26), (25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)  # Legs
]

METRICS_FIELDS = {
    "Squats": {
        "knee_angle": 0,
        "back_angle": 0,
        "depth_status": "N/A",
    },
    "Push-ups": {
        "elbow_angle": 0,
        "body_alignment": "N/A",
        "hip_status": "N/A",
    },
    "Biceps Curls (Dumbbell)": {
        "elbow_angle": 0,
        "shoulder_status": "N/A",
        "swing_status": "N/A",
    },
    "Shoulder Press": {
        "elbow_angle": 0,
        "extension_status": "N/A",
        "back_arch_status": "N/A",
    },
    "Lunges": {
        "front_knee_angle": 0,
        "torso_angle": 0,
        "balance_status": "N/A",
    },
    "Jumping Jacks": {
        "arm_angle": 0,
        "leg_spread_ratio": 0.0,
        "motion_phase": "N/A",
    },
    "Plank": {
        "hold_seconds": 0,
        "body_alignment": "N/A",
        "hip_status": "N/A",
    },
}

EXERCISE_GUIDES = {
    "Squats": {
        "title": "Barbell / Bodyweight Squats",
        "target_muscles": "Quadriceps, Glutes, Hamstrings, Core",
        "ideal_form": "Keep feet shoulder-width apart. Hinge at hips and knees until thighs are parallel to ground (knee angle ≤ 100°). Keep chest lifted and spine neutral.",
        "common_mistakes": ["Not squatting deep enough (knee angle > 100°)", "Leaning excessively forward", "Knees caving inwards"],
        "difficulty": "Beginner to Intermediate",
        "rep_label": "Reps"
    },
    "Push-ups": {
        "title": "Standard Push-up",
        "target_muscles": "Chest (Pectorals), Triceps, Front Deltoids, Core",
        "ideal_form": "Hands slightly wider than shoulders. Maintain a straight rigid line from shoulders through hips down to ankles. Lower chest until elbows bend to 90° or below, then press up to full lockout.",
        "common_mistakes": ["Hips sagging down (strains lumbar spine)", "Hips piked up in the air", "Half reps without full elbow bend"],
        "difficulty": "Beginner to Intermediate",
        "rep_label": "Reps"
    },
    "Biceps Curls (Dumbbell)": {
        "title": "Standing Dumbbell Curl",
        "target_muscles": "Biceps Brachii, Brachialis, Forearms",
        "ideal_form": "Stand tall with dumbbells at sides. Pin elbows tight against ribcage. Curl weights smoothly upward to around 50° elbow angle without rocking torso. Lower with control.",
        "common_mistakes": ["Swinging torso for momentum", "Elbows drifting forward or away from sides", "Incomplete extension at bottom"],
        "difficulty": "Beginner",
        "rep_label": "Reps"
    },
    "Shoulder Press": {
        "title": "Dumbbell Overhead Shoulder Press",
        "target_muscles": "Deltoids (Anterior & Medial), Upper Traps, Triceps",
        "ideal_form": "Start with weights at shoulder height (elbows ~90°). Brace your core and press dumbbells vertically overhead to full lockout without hyperextending lower back.",
        "common_mistakes": ["Excessive lower back hyperextension/arch", "Not locking out arms at top", "Flaring elbows too far back"],
        "difficulty": "Intermediate",
        "rep_label": "Reps"
    },
    "Lunges": {
        "title": "Alternating Forward Lunges",
        "target_muscles": "Quadriceps, Glutes, Hamstrings, Calves",
        "ideal_form": "Step forward firmly and lower body until lead thigh is parallel to ground (front knee ~90°). Keep torso upright and balance centered over hips.",
        "common_mistakes": ["Front knee driving too far past toes", "Torso tilting forward", "Loss of lateral balance"],
        "difficulty": "Intermediate",
        "rep_label": "Reps"
    },
    "Jumping Jacks": {
        "title": "Dynamic Cardio Jumping Jacks",
        "target_muscles": "Full Body Cardio, Calves, Deltoids, Hip Abductors",
        "ideal_form": "Start standing with arms at sides. Jump feet out wider than shoulder-width while sweeping arms overhead until hands meet. Jump back to starting position rhythmically.",
        "common_mistakes": ["Half arm reaches (hands don't clear shoulders)", "Feet barely jumping outward", "Lack of rhythmic tempo"],
        "difficulty": "Beginner (High Cardio)",
        "rep_label": "Reps"
    },
    "Plank": {
        "title": "Isometric Core Plank",
        "target_muscles": "Rectus Abdominis, Transverse Abdominis, Glutes, Shoulders",
        "ideal_form": "Hold body on forearms and toes in a rigid, unwavering straight line. Squeeze glutes and engage core so hips neither sag nor pike.",
        "common_mistakes": ["Hips sagging towards the floor", "Piking hips up into downward dog", "Holding breath"],
        "difficulty": "All Levels",
        "rep_label": "Hold Seconds"
    }
}

COACH_PERSONAS = {
    "Motivational": {
        "name": "⚡ Energetic Coach",
        "desc": "High-energy, positive, and enthusiastic motivation to push your limits.",
        "prompt_tone": "High-energy, encouraging, positive, and inspiring. Speak like an enthusiastic top fitness trainer."
    },
    "Drill Sergeant": {
        "name": "🎖️ Strict Drill Sergeant",
        "desc": "No-nonsense, direct, demanding discipline and razor-sharp form.",
        "prompt_tone": "Direct, authoritative, strict, and military-style. No fluff, demand focus and proper form."
    },
    "Zen": {
        "name": "🧘 Mindful Master",
        "desc": "Calm, focused on breathing, mindful movement, and smooth control.",
        "prompt_tone": "Calm, centered, focused on breathing, deliberate control, and posture awareness."
    }
}

PROMPT = (
    "You are AI Gym Coach, an elite professional AI gym trainer monitoring a user's workout via live camera.\n\n"
    "### Your Role\n"
    "Provide concise (around 10-15 words), punchy, natural coaching cues spoken aloud.\n\n"
    "### Input Format\n"
    "Updates arrive as: 'Event: [state] Form Issue: [description]'.\n"
    "- 'Event': workout_started, set_completed, workout_completed, no_pose_detected, ongoing_form_check.\n"
    "- 'Form Issue': A technical description of a pose error (if any).\n\n"
    "### Guidelines\n"
    "1. Speak directly to the athlete in the second person ('Drive through your heels!', 'Keep that chest upright!').\n"
    "2. Keep it punchy and memorable — exactly what a trainer shouts in the gym.\n"
    "3. Prioritize safety and form integrity."
)
