# action_executor.py

import pygetwindow as gw
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QApplication, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer

DISTRACTION_KEYWORDS = [
    "slack", "discord", "whatsapp", "chrome", "edge", "firefox",
    "youtube", "teams", "zoom", "telegram", "instagram", "twitter",
]


def hide_distraction_apps():
    for w in gw.getAllWindows():
        title = (w.title or "").lower()
        if any(k in title for k in DISTRACTION_KEYWORDS):
            print(f"[EXECUTOR] Minimizing: {title}")
            try:
                w.minimize()
            except Exception as e:
                print(f"[EXECUTOR] error: {e}")


def _qt(func):
    if QApplication.instance():
        QTimer.singleShot(0, func)


# ── Overlay widgets ────────────────────────────────────────────────────────

def show_break_overlay(duration_secs=120, message="Short reset", submessage=""):
    def _show():
        w = QWidget()
        w.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        w.setStyleSheet("background-color: rgba(10,10,20,245);")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        title = QLabel(message)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #CDD6F4; font-size: 26px; font-weight: bold; font-family: 'Courier New';"
        )
        layout.addWidget(title)

        if submessage:
            sub = QLabel(submessage)
            sub.setAlignment(Qt.AlignCenter)
            sub.setStyleSheet("color: #585B70; font-size: 14px; font-family: 'Courier New';")
            layout.addWidget(sub)

        countdown = QLabel(f"{duration_secs}s")
        countdown.setAlignment(Qt.AlignCenter)
        countdown.setStyleSheet(
            "color: #89B4FA; font-size: 48px; font-weight: bold; font-family: 'Courier New';"
        )
        layout.addWidget(countdown)

        btn = QPushButton("DISMISS")
        btn.clicked.connect(w.close)
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(137,180,250,0.15); color: #89B4FA;
                border: 1px solid rgba(137,180,250,0.4); border-radius: 8px;
                padding: 8px 24px; font-family: 'Courier New'; font-size: 12px;
                letter-spacing: 2px;
            }
            QPushButton:hover { background: rgba(137,180,250,0.28); }
        """)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

        w.showFullScreen()

        remaining = [duration_secs]
        def tick():
            remaining[0] -= 1
            if remaining[0] <= 0:
                w.close()
            else:
                countdown.setText(f"{remaining[0]}s")
        timer = QTimer(w)
        timer.timeout.connect(tick)
        timer.start(1000)

    _qt(_show)


def show_nudge_overlay(message="Back to your project?"):
    def _show():
        w = QWidget()
        w.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        w.setStyleSheet("""
            background: rgba(17,17,27,230);
            border: 1px solid rgba(249,226,175,0.35);
            border-radius: 12px;
        """)
        w.resize(380, 64)
        screen = QApplication.primaryScreen().availableGeometry()
        w.move(screen.width() - 410, 50)

        layout = QHBoxLayout(w)
        layout.setContentsMargins(16, 0, 16, 0)
        icon = QLabel("💡")
        icon.setStyleSheet("font-size: 18px;")
        label = QLabel(message)
        label.setStyleSheet(
            "color: #F9E2AF; font-size: 13px; font-family: 'Courier New';"
        )
        layout.addWidget(icon)
        layout.addWidget(label)

        w.show()
        QTimer.singleShot(7000, w.close)
    _qt(_show)


def show_rage_overlay(message="You're in the red. Five-minute reset."):
    """Full screen red tinted rage banner."""
    def _show():
        w = QWidget()
        w.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        w.setStyleSheet("background-color: rgba(15,5,10,250);")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("🛑")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 56px;")
        layout.addWidget(icon)

        title = QLabel("OVERLOADED")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #F38BA8; font-size: 32px; font-weight: bold; font-family: 'Courier New'; letter-spacing: 4px;"
        )
        layout.addWidget(title)

        sub = QLabel(message)
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #CDD6F4; font-size: 15px; font-family: 'Courier New';")
        layout.addWidget(sub)

        countdown = QLabel("300s")
        countdown.setAlignment(Qt.AlignCenter)
        countdown.setStyleSheet(
            "color: #F38BA8; font-size: 52px; font-weight: bold; font-family: 'Courier New';"
        )
        layout.addWidget(countdown)

        btn = QPushButton("I'M BACK")
        btn.clicked.connect(w.close)
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(243,139,168,0.15); color: #F38BA8;
                border: 1px solid rgba(243,139,168,0.4); border-radius: 8px;
                padding: 8px 24px; font-family: 'Courier New'; font-size: 12px; letter-spacing: 2px;
            }
            QPushButton:hover { background: rgba(243,139,168,0.28); }
        """)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

        w.showFullScreen()

        remaining = [300]
        def tick():
            remaining[0] -= 1
            if remaining[0] <= 0:
                w.close()
            else:
                countdown.setText(f"{remaining[0]}s")
        timer = QTimer(w)
        timer.timeout.connect(tick)
        timer.start(1000)

    _qt(_show)


# ── Main dispatcher ────────────────────────────────────────────────────────

def execute_action(action: str):
    print(f"[EXECUTOR] Action: {action}")
    a = (action or "").strip().lower()

    try:
        from voice_output import speak_text
    except Exception:
        speak_text = lambda t: None

    if a == "hide_chat_and_focus_work":
        hide_distraction_apps()
        speak_text(
            "You look overloaded. I've closed your distractions so you can get back in flow."
        )
        show_break_overlay(
            60,
            "Chats closed. 60-second reset.",
            "Close your eyes. Take a breath. You've got this."
        )

    elif a == "hide_slack_and_break":
        hide_distraction_apps()
        speak_text(
            "You've been in Slack too long and you look stressed. Closing distractions now."
        )
        show_break_overlay(
            60,
            "Slack closed. Quick reset.",
            "Step back for a moment."
        )

    elif a == "rage_break":
        hide_distraction_apps()
        speak_text(
            "Your load is in the red. I'm shutting down everything. Take five minutes. You've earned it."
        )
        show_rage_overlay("Distractions off. Five-minute reset — you've earned it.")

    elif a == "enforce_break":
        speak_text(
            "Your eyes are looking tired and you've been sitting too long. Time for a short break."
        )
        show_break_overlay(
            180,
            "Three-minute break.",
            "Step away from the screen. Look at something far away."
        )

    elif a in ("soft_nudge", "nudge"):
        speak_text(
            "Hey, this call is running long. When you're ready, I'll help you get back into your project."
        )
        show_nudge_overlay("Long call — ready to get back to deep work?")

    else:
        print(f"[EXECUTOR] No-op: {action}")