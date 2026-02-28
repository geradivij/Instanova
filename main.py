# main.py
import sys, time, threading
from PyQt5.QtWidgets import QApplication

from vision_pipeline import VisionPipeline
from agent import CLRAgent
from dashboard import CLRDashboard

def main():
    app = QApplication(sys.argv)

    vision = VisionPipeline()
    print("Vision pipeline started")

    agent = CLRAgent()
    dashboard = CLRDashboard(agent=agent)

    # Agent → UI
    agent.ui_callback = dashboard.update_from_agent

    # Vision → agent
    def vision_feed():
        while True:
            vs = vision.get_state()
            agent.set_vision_state(vs)
            time.sleep(2)

    threading.Thread(target=vision_feed, daemon=True).start()

    agent.start()
    dashboard.show()

    print("CLR running. Toggle Focus Mode in the UI.")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
