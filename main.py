# main.py
import sys, time, threading
from PyQt5.QtWidgets import QApplication

from vision_pipeline import VisionPipeline
from agent import CLRAgent
from dashboard import CLRDashboard


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    vision = VisionPipeline()
    print("[MAIN] Vision pipeline started")

    agent = CLRAgent(vision_pipeline=vision)

    dashboard = CLRDashboard(agent=agent)
    agent.ui_callback = dashboard.update_from_agent

    # Vision feed thread
    def vision_feed():
        while True:
            vs = vision.get_state()
            agent.set_vision_state(vs)
            time.sleep(2)
    threading.Thread(target=vision_feed, daemon=True).start()

    # Voice listener thread
    def start_voice_listener():
        try:
            from voice_input import VoiceListener
            listener = VoiceListener(on_stress_detected=agent.on_stress_detected)
            listener.start()
            print("[MAIN] Voice listener started — say 'I'm so stressed' to trigger")
        except Exception as e:
            print(f"[MAIN] Voice listener unavailable: {e}")
    threading.Thread(target=start_voice_listener, daemon=True).start()

    agent.start()
    dashboard.show()

    # Startup greeting
    def greet():
        time.sleep(1.5)
        try:
            from voice_output import speak_text
            speak_text(
                "CLR is running. Press the focus button when you're ready "
                "and I'll keep your attention protected."
            )
        except Exception:
            pass
    threading.Thread(target=greet, daemon=True).start()

    print("[MAIN] CLR running.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()