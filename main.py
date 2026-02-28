# main.py
import sys, time, threading
from PyQt5.QtWidgets import QApplication

from vision_pipeline import VisionPipeline
from agent import CLRAgent
from dashboard import CLRDashboard

def main():
    app = QApplication(sys.argv)

    # Start vision
    vision = VisionPipeline()
    print("Vision pipeline started")

    # Start agent
    agent = CLRAgent()
    # Create dashboard and connect agent → UI
    dashboard = CLRDashboard(agent=agent)
    agent.ui_callback = dashboard.update_from_agent

    # Feed vision into agent
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
