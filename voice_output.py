# voice_output.py — runs speech in its own thread so it never blocks
import pyttsx3
import random
import threading

def speak_text(text: str):
    """Always runs in a daemon thread — never blocks main/UI thread."""
    def _speak():
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 150)
            engine.setProperty("volume", 0.95)
            voices = engine.getProperty("voices")
            for v in voices:
                if any(x in v.name.lower() for x in ["zira", "hazel", "female"]):
                    engine.setProperty("voice", v.id)
                    break
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as ex:
            print(f"[VOICE] error: {ex}")
    threading.Thread(target=_speak, daemon=True).start()

# ── Randomised line banks ──────────────────────────────────────────────────

RAGE_LINES = [
    "Okay, things got spicy. I'm closing the noise. Five minutes, just breathe.",
    "You're in the red. Distractions are gone. Step away for a bit.",
    "Way too much going on. Shutting it all down. You've earned a break.",
    "Red zone. Closing everything. You're not a machine. Take five.",
    "Pulling the plug on distractions. Go drink some water. Seriously.",
]
OVERLOAD_LINES = [
    "Getting pretty loaded up. Muting the noise so you can find your flow.",
    "Too many tabs, too many apps. Closing the chaos. You've got this.",
    "High load. Trimming the distractions. Back to what matters.",
    "Things are piling up. Let me clear the clutter.",
]
ELEVATED_LINES = [
    "Things are heating up a little. I'm keeping an eye on you.",
    "Your load is rising. Take a breath. I'm here if it gets worse.",
    "Heads up, you're getting a bit scattered.",
]
ENFORCE_BREAK_LINES = [
    "Your eyes look tired. Step away for three minutes.",
    "You've been staring a long time. Three minute break.",
    "Eyes need a rest. Short break. You'll come back sharper.",
]
NUDGE_LINES = [
    "That call's been running long. Your project is waiting.",
    "Long call detected. Deep work is calling when you're done.",
    "Hey, the call's getting long. Ready to refocus?",
]
STRESS_COMFORT_LINES = [
    "Hey, I hear you. You don't have to give up. Take a breath — I'm right here.",
    "I caught that. It's okay to feel overwhelmed. Let's just slow down together.",
    "You said it, I heard it. Don't give up yet. One thing at a time.",
    "Hey. That sounds tough. I've got you. Let's take a second.",
    "It's okay. Everyone hits a wall. Just breathe — you're closer than you think.",
]
BREATHING_STILL_TENSE = [
    "You still look a little tense. No pressure. Just keep breathing.",
    "Take your time. There is no rush. I am right here.",
    "Still a bit wound up. That's fine. Another slow breath when you're ready.",
]
BREATHING_RELAXED = [
    "That's it. You're looking more relaxed. Nice work.",
    "Good. You're coming back. Whenever you're ready, we'll get back to it.",
    "Much better. Take as long as you need.",
]
FOCUS_ON_LINES = [
    "Focus mode on. I'll protect your attention.",
    "Let's get in the zone. I'm watching your back.",
    "Focus session started. Distractions don't stand a chance.",
]
FOCUS_OFF_LINES = [
    "Focus mode off. Good session.",
    "Session ended. Nice work today.",
    "Taking a breather. Good job.",
]

def speak_rage():                  speak_text(random.choice(RAGE_LINES))
def speak_overload():              speak_text(random.choice(OVERLOAD_LINES))
def speak_elevated():              speak_text(random.choice(ELEVATED_LINES))
def speak_enforce_break():         speak_text(random.choice(ENFORCE_BREAK_LINES))
def speak_nudge():                 speak_text(random.choice(NUDGE_LINES))
def speak_stress_comfort():        speak_text(random.choice(STRESS_COMFORT_LINES))
def speak_breathing_still_tense(): speak_text(random.choice(BREATHING_STILL_TENSE))
def speak_breathing_relaxed():     speak_text(random.choice(BREATHING_RELAXED))
def speak_focus_on():              speak_text(random.choice(FOCUS_ON_LINES))
def speak_focus_off():             speak_text(random.choice(FOCUS_OFF_LINES))