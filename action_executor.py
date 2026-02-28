import pygetwindow as gw
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

TARGET_TITLE_KEYWORD = "Slack"  # or "Chrome" / "VS Code"

def _find_windows():
    return [w for w in gw.getAllWindows()
            if TARGET_TITLE_KEYWORD.lower() in w.title.lower()]

def hide_slack():
    for w in _find_windows():
        try:
            w.minimize()
        except Exception:
            pass

def show_break_overlay(duration=120):
    w = QWidget()
    w.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    w.setStyleSheet("background-color: rgba(0,0,0,200); color: white;")
    layout = QVBoxLayout(w)
    label = QLabel("Take a short break")
    label.setFont(QFont("Arial", 24))
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    w.showFullScreen()
    QTimer.singleShot(duration * 1000, w.close)

def show_rage_banner():
    msg = QMessageBox()
    msg.setWindowTitle("RAGE DETECTED")
    msg.setText("🔥 RAGE DETECTED 🔥\nTake a breath. Step away for 2 minutes.")
    msg.exec_()

def execute_action(action: str):
    if action == "hide_slack_and_break":
        hide_slack()
        show_break_overlay(120)
    elif action == "rage_break":
        hide_slack()
        show_rage_banner()
        show_break_overlay(300)
    elif action == "nudge":
        show_rage_banner()

# if __name__ == "__main__":
#     # quick test
#     show_rage_banner()

if __name__ == "__main__":
    print("action_executor imported successfully")
