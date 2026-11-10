import random
from services.config.workout_config import PROMPT, COACH_PERSONAS


class RuleBasedCoach:
    """High-energy fallback coach providing instant cues when Groq API key is not present or offline."""
    def __init__(self, persona="Motivational"):
        self.persona = persona

    def give_feedback(self, event, issue=None):
        if event == "workout_started":
            greetings = {
                "Motivational": [
                    "Let's crush this workout! Focus on every single rep!",
                    "Game on! Time to give 100% effort today!",
                    "Lock in! Form first, power second. Let's do this!"
                ],
                "Drill Sergeant": [
                    "Attention! Time to work! Zero excuses, perfect form only!",
                    "Move it! Get into position and show me what you've got!",
                    "Drop the hesitation and start the set now!"
                ],
                "Zen": [
                    "Center your mind and breathe. Move with intention and control.",
                    "Focus inward. Quality and breath matter most in this practice.",
                    "Align your body and let's begin with calm focus."
                ]
            }
            return random.choice(greetings.get(self.persona, greetings["Motivational"]))

        if event == "workout_completed":
            closings = {
                "Motivational": [
                    "Outstanding work! You gave it your all today, champion!",
                    "Workout complete! Fantastic effort, be proud of that session!",
                    "Incredible job! Recovery time now, you earned it!"
                ],
                "Drill Sergeant": [
                    "Workout terminated! Good hustle today, dismissed!",
                    "Session finished! You survived and got stronger. Great discipline!",
                    "Done! Rest up, recover, and be ready for tomorrow!"
                ],
                "Zen": [
                    "Session complete. Thank your body for its strength and perseverance.",
                    "Honor your effort today. Take deep breaths and recover peacefully.",
                    "Beautiful work. Your focus and presence made all the difference."
                ]
            }
            return random.choice(closings.get(self.persona, closings["Motivational"]))

        if event == "set_completed":
            set_cues = {
                "Motivational": [
                    "Great set! Catch your breath and shake it off!",
                    "Boom! Another set in the books! Keep that momentum going!",
                    "Solid reps! Stay hydrated and get ready for the next one!"
                ],
                "Drill Sergeant": [
                    "Set complete! Take your rest, but keep your head in the game!",
                    "Good set! Don't get comfortable, next set is coming fast!",
                    "Reps counted! Breathe and get ready to attack again!"
                ],
                "Zen": [
                    "Set finished. Inhale deeply, release any tension, and reset.",
                    "Well executed. Enjoy this rest period with steady breaths.",
                    "Graceful effort. Allow your muscles to replenish and calm."
                ]
            }
            return random.choice(set_cues.get(self.persona, set_cues["Motivational"]))

        if event == "no_pose_detected":
            return "Please step into the camera frame so I can track your form!"

        if issue:
            # Direct corrective cues
            corrections = {
                "knees are not bending sufficiently": "Squat lower! Sink those hips down to parallel!",
                "leaning too far forward": "Chest up! Keep your spine tall and proud!",
                "hips are sagging": "Squeeze your core! Don't let your hips sag towards the floor!",
                "hips are too high": "Lower your hips to form a straight rigid plank line!",
                "swinging their torso": "Stop swinging! Lock your torso and isolate the biceps!",
                "elbow is drifting": "Pin your elbows tight against your ribcage!",
                "arching their lower back": "Brace your core tight! Prevent that lower back arch!",
                "losing balance": "Widen your stance for a stable, rock-solid base!",
                "Raise arms higher": "Reach those arms all the way overhead!",
                "Widen your stance": "Jump wider! Get a full athletic jump!"
            }
            for keyword, cue in corrections.items():
                if keyword.lower() in issue.lower():
                    return cue
            return f"Check your form: {issue}"

        encouragements = [
            "Great rhythm, keep that pristine form!",
            "Looking strong, maintain steady breathing!",
            "Excellent tempo! Stay focused on every contraction!",
            "Smooth motion, you are dialed in!"
        ]
        return random.choice(encouragements)


class LLMCoach:
    def __init__(self, groq_client=None, persona="Motivational"):
        self.client = groq_client
        self.persona = persona
        self.history = []
        self.fallback_coach = RuleBasedCoach(persona=persona)

    def set_persona(self, persona):
        self.persona = persona
        self.fallback_coach.persona = persona

    def give_feedback(self, event, issue):
        if not self.client:
            return self.fallback_coach.give_feedback(event, issue)

        prompt_tone = COACH_PERSONAS.get(self.persona, {}).get("prompt_tone", "High-energy, encouraging fitness coach.")
        system_instruction = f"{PROMPT}\n\n### Persona Tone\n{prompt_tone}"

        user_content = f"Event: {event}"
        if issue:
            user_content += f" Form Issue: {issue}"

        messages = [
            {"role": "system", "content": system_instruction},
            *self.history[-6:],
            {"role": "user", "content": user_content}
        ]

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.5,
                max_tokens=60,
                timeout=4.0
            )
            text = response.choices[0].message.content.strip()
            # Clean quotes if any
            if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                text = text[1:-1].strip()
            self.history.append({"role": "assistant", "content": text})
            return text
        except Exception:
            # Graceful fallback to rule-based coach if API call fails or times out
            return self.fallback_coach.give_feedback(event, issue)
