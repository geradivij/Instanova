# voice_output.py
import pyttsx3
import random

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 155)
        _engine.setProperty("volume", 0.92)
        voices = _engine.getProperty("voices")
        for v in voices:
            if any(x in v.name.lower() for x in ["zira", "hazel", "female"]):
                _engine.setProperty("voice", v.id)
                break
    return _engine

def speak_text(text: str):
    try:
        e = _get_engine()
        e.say(text)
        e.runAndWait()
    except Exception as ex:
        print(f"[VOICE] error: {ex}")

RAGE_LINES = [
    "Okay, things got spicy. I'm closing the noise. Five minutes, just breathe.",
    "You're in the red. I've got you. Distractions are gone. Step away for a bit.",
    "Whoa. Way too much going on. I'm shutting it all down. You've earned a break.",
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
    "Heads up, you're getting a bit scattered. Want to refocus?",
]
ENFORCE_BREAK_LINES = [
    "Your eyes look tired. Seriously, step away for three minutes.",
    "You've been staring a long time. Three minute break. Look at something far away.",
    "Eyes need a rest. Short break. You'll come back sharper.",
]
NUDGE_LINES = [
    "That call's been running long. When you're ready, I'll help you get back on track.",
    "Long call detected. Your project is waiting.",
    "Hey, call's getting long. Deep work is calling when you're done.",
]
STRESS_RESPONSE_LINES = [
    "Hey, I hear you. Let's just breathe for a second. I'm closing everything distracting.",
    "You're stressed. That's okay. I'm handling the noise. You just breathe.",
    "Take it easy. I've got this. Closing the clutter, just focus on your breath.",
    "I hear you. Let's slow down together. Everything can wait.",
    "It's okay to feel overwhelmed. I'm here. Let's close everything and reset.",
]
BREATHING_CHECK_STILL_TENSE = [
    "You still look a little tense. No pressure. Just keep breathing.",
    "Take your time. There is no rush. I am right here.",
    "Still a bit wound up. That's fine. Another slow breath when you're ready.",
]
BREATHING_CHECK_RELAXED = [
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

def speak_rage():            speak_text(random.choice(RAGE_LINES))
def speak_overload():        speak_text(random.choice(OVERLOAD_LINES))
def speak_elevated():        speak_text(random.choice(ELEVATED_LINES))
def speak_enforce_break():   speak_text(random.choice(ENFORCE_BREAK_LINES))
def speak_nudge():           speak_text(random.choice(NUDGE_LINES))
def speak_stress_response(): speak_text(random.choice(STRESS_RESPONSE_LINES))
def speak_breathing_still_tense(): speak_text(random.choice(BREATHING_CHECK_STILL_TENSE))
def speak_breathing_relaxed():     speak_text(random.choice(BREATHING_CHECK_RELAXED))
def speak_focus_on():        speak_text(random.choice(FOCUS_ON_LINES))
def speak_focus_off():       speak_text(random.choice(FOCUS_OFF_LINES))