# voice_output.py
import pyttsx3

_engine = None

def speak_text(text: str):
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 165)
        _engine.setProperty("volume", 0.9)
    _engine.say(text)
    _engine.runAndWait()
