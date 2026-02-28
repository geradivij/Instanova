# action_executor.py

import pygetwindow as gw
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QMessageBox, QApplication
from PyQt5.QtCore import Qt, QTimer

from voice_output import speak_text


def hide_distraction_apps():
    """
    Minimize distraction apps: Slack, Discord, browsers, etc.
    Keep IDEs like VS Code visible.
    """
    KEYWORDS = ["slack", "discord", "whatsapp", "chrome", "edge", "firefox", "youtube"]
    wins = gw.getAllWindows()
    print("[EXECUTOR] Windows:")
    for w in wins:
        title = (w.title or "").lower()
        print(" -", title)
        if any(k in title for k in KEYWORDS):
            print("[EXECUTOR] Minimizing:", title)
            try:
                w.minimize()
            except Exception as e:
                print("[EXECUTOR] error minimizing", title, e)


def _run_qt_overlay(func):
    app = QApplication.instance()
    if app is None:
        return
    QTimer.singleShot(0, func)


def show_break_overlay(duration_secs=120, message="Short reset"):
    def _show():
        w = QWidget()
        w.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        w.setStyleSheet(
            "background-color: rgba(10,10,20,230);"
            "color: #CDD6F4;"
        )
        layout = QVBoxLayout(w)
        label = QLabel(message)
        label.setStyleSheet("font-size: 22px; font-family: Arial;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        w.showFullScreen()
        QTimer.singleShot(duration_secs * 1000, w.close)
    _run_qt_overlay(_show)


def show_rage_banner(message="You’re in the red. Five minute reset."):
    def _show():
        msg = QMessageBox()
        msg.setWindowTitle("CLR – High Load")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    _run_qt_overlay(_show)


def show_nudge_overlay(message="This call’s long. Back to deep work?"):
    def _show():
        w = QWidget()
        w.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        w.setStyleSheet(
            "background-color: rgba(20,20,35,240);"
            "color: #CDD6F4; border-radius: 12px;"
        )
        w.resize(420, 80)
        screen = QApplication.primaryScreen().availableGeometry()
        w.move(screen.width() - 450, 40)

        layout = QVBoxLayout(w)
        label = QLabel(message)
        label.setStyleSheet("font-size: 16px; font-family: Arial;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        w.show()
        QTimer.singleShot(6000, w.close)
    _run_qt_overlay(_show)


def execute_action(action: str):
    """
    Interpret agent/model action strings and run real OS actions.
    """
    print(f"[EXECUTOR] Action: {action}")
    a = (action or "").strip().lower()

    if a == "hide_slack_and_break":
        # Use same minimization for both Slack-idle and overload
        hide_distraction_apps()
        speak_text(
            "You’ve been stuck in Slack and look stressed. "
            "I’m closing distractions so you can reset."
        )
        show_break_overlay(60, "Slack and chats closed for a quick reset.")

    elif a == "rage_break":
        # FULL RESET: minimize all distractions and force a longer break
        hide_distraction_apps()
        speak_text(
            "Your load is in the red. I’m shutting down distractions "
            "and giving you a five minute reset."
        )
        show_rage_banner("You’re in the red. Five minute reset.")
        show_break_overlay(300, "Distractions off. Five minute reset – breathe.")

    elif a == "nudge":
        speak_text(
            "This call is running long. Ready to get back to your project?"
        )
        show_nudge_overlay("Long call – back to your project?")

    else:
        print("[EXECUTOR] No-op for action:", action)
