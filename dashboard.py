from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QProgressBar,
    QLabel,
    QTextEdit,
)
from PyQt5.QtCore import pyqtSignal, QObject, Qt


class AgentBridge(QObject):
    updated = pyqtSignal(dict)


class CLRDashboard(QMainWindow):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent

        # Overlay HUD styling
        self.setWindowTitle("CLR – Focus Companion")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(480, 150)
        self.move(20, 40)  # small top-left HUD

        self.bridge = AgentBridge()
        self.bridge.updated.connect(self.handle_update)

        self.focus_on = False
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(
            "background-color: rgba(15, 15, 30, 230);"
            "color: #CDD6F4;"
        )
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(6)
        layout.setContentsMargins(14, 10, 14, 10)

        # Focus Session button
        self.focus_btn = QPushButton("Start Focus Session (F)")
        self.focus_btn.clicked.connect(self.toggle_focus)
        self.focus_btn.setStyleSheet(
            "QPushButton {background:#89B4FA; color:#1E1E2E; "
            "border-radius:10px; padding:8px 16px; font-weight:bold;}"
            "QPushButton:pressed {background:#1E66F5; color:#EFF1F5;}"
        )
        layout.addWidget(self.focus_btn)

        # Score / load bar
        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setTextVisible(True)
        self.score_bar.setStyleSheet(
            "QProgressBar {background:#313244; border-radius:4px;}"
            "QProgressBar::chunk {background:#A6E3A1; border-radius:4px;}"
        )
        layout.addWidget(self.score_bar)

        # State label
        self.zone_label = QLabel("State: Calm")
        self.zone_label.setStyleSheet("color:#A6E3A1;")
        layout.addWidget(self.zone_label)

        # Signals display
        self.signal_label = QLabel("Signals: –")
        self.signal_label.setWordWrap(True)
        self.signal_label.setStyleSheet("color:#BAC2DE;")
        layout.addWidget(self.signal_label)

        # Coach text (small message line)
        self.rage_label = QLabel("")
        self.rage_label.setStyleSheet("color:#F38BA8; font-weight:bold;")
        layout.addWidget(self.rage_label)

        # Tiny log (optional)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet(
            "background:#181825; color:#CDD6F4; "
            "border-radius:6px; border:none;"
        )
        self.log_box.setFixedHeight(40)
        layout.addWidget(self.log_box)

    def toggle_focus(self):
        self.focus_on = not self.focus_on
        self.focus_btn.setText(
            "Focus Session ON (press F to stop)" if self.focus_on
            else "Start Focus Session (F)"
        )
        if self.agent:
            self.agent.set_focus_mode(self.focus_on)

        if not self.focus_on:
            self.rage_label.setText("")

    # called from agent thread
    def update_from_agent(self, data: dict):
        self.bridge.updated.emit(data)

    # runs on UI thread
    def handle_update(self, data: dict):
        score = data.get("score", 0)
        zone = data.get("zone", "NORMAL")
        signals = data.get("signals", {})
        log = data.get("log")

        # Score
        try:
            self.score_bar.setValue(int(score))
        except Exception:
            self.score_bar.setValue(0)

        # State text + colors
        if zone == "RAGE":
            self.zone_label.setText("State: Overwhelmed")
            style = (
                "QProgressBar {background:#313244; border-radius:4px;}"
                "QProgressBar::chunk {background:#F38BA8; border-radius:4px;}"
            )
            self.zone_label.setStyleSheet("color:#F38BA8;")
        elif zone == "OVERLOAD":
            self.zone_label.setText("State: High load")
            style = (
                "QProgressBar {background:#313244; border-radius:4px;}"
                "QProgressBar::chunk {background:#FAB387; border-radius:4px;}"
            )
            self.zone_label.setStyleSheet("color:#FAB387;")
        elif zone == "ELEVATED":
            self.zone_label.setText("State: Focused but loaded")
            style = (
                "QProgressBar {background:#313244; border-radius:4px;}"
                "QProgressBar::chunk {background:#F9E2AF; border-radius:4px;}"
            )
            self.zone_label.setStyleSheet("color:#F9E2AF;")
        else:
            self.zone_label.setText("State: Calm")
            style = (
                "QProgressBar {background:#313244; border-radius:4px;}"
                "QProgressBar::chunk {background:#A6E3A1; border-radius:4px;}"
            )
            self.zone_label.setStyleSheet("color:#A6E3A1;")

        self.score_bar.setStyleSheet(style)

        # Signals – includes stress + call info
        self.signal_label.setText(
            "Signals: "
            f"switches={signals.get('app_switches_30s', 0)}, "
            f"backspace={signals.get('backspace_bursts', 0)}, "
            f"idle={signals.get('idle_secs', 0)}s, "
            f"face={signals.get('face_present')}, "
            f"eyes={signals.get('eye_state')}, "
            f"stress_face={signals.get('stressed_face', False)}, "
            f"call={signals.get('call_minutes', 0)}min "
            f"({signals.get('active_app', 'no app')})"
        )

        # Coach text based on zone / calls
        if zone == "RAGE":
            self.rage_label.setText("You’re overloaded. We’ve paused distractions.")
        elif zone == "OVERLOAD":
            self.rage_label.setText("We’ve muted the noise so you can stay in flow.")
        else:
            if signals.get("on_call", False) and signals.get("call_minutes", 0) >= 1:
                self.rage_label.setText("Long call – ready to get back to the project?")
            else:
                self.rage_label.setText("")

        # Intervention log (small history at bottom)
        if log:
            self.log_box.append(log)
