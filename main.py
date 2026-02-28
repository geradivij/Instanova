# main.py
import sys, time, threading
from PyQt5.QtWidgets import QApplication

from vision_pipeline import VisionPipeline
from agent import CLRAgent
from dashboard import CLRDashboard


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # Vision (webcam → face/eye state)
    vision = VisionPipeline()
    print("[MAIN] Vision pipeline started")

    # Agent (signal collection + Gemma decisions)
    agent = CLRAgent()

    # Dashboard (HUD)
    dashboard = CLRDashboard(agent=agent)
    agent.ui_callback = dashboard.update_from_agent

    # Feed vision state into agent every 2s
    def vision_feed():
        while True:
            vs = vision.get_state()
            agent.set_vision_state(vs)
            time.sleep(2)

    threading.Thread(target=vision_feed, daemon=True).start()

    agent.start()
    dashboard.show()

    # Startup voice greeting
    def greet():
        time.sleep(1.5)
        try:
            from voice_output import speak_text
            speak_text(
                "CLR is running. Press the focus button to activate your session "
                "and I'll keep your attention protected."
            )
        except Exception:
            pass

    threading.Thread(target=greet, daemon=True).start()

    print("[MAIN] CLR running. Toggle Focus Mode in the HUD.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()