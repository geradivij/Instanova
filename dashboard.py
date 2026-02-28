# dashboard.py
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QProgressBar, QLabel, QTextEdit
)
from PyQt5.QtCore import pyqtSignal, QObject

class AgentBridge(QObject):
    updated = pyqtSignal(dict)

class CLRDashboard(QMainWindow):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.setWindowTitle("CLR – Cognitive Load Reducer")
        self.resize(500, 400)

        self.bridge = AgentBridge()
        self.bridge.updated.connect(self.handle_update)

        self.focus_on = False
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        # Focus button
        self.focus_btn = QPushButton("FOCUS MODE – OFF")
        self.focus_btn.clicked.connect(self.toggle_focus)
        layout.addWidget(self.focus_btn)

        # Score bar + labels
        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        layout.addWidget(self.score_bar)

        self.zone_label = QLabel("Zone: NORMAL")
        layout.addWidget(self.zone_label)

        # Signals
        self.signal_label = QLabel("Signals: –")
        layout.addWidget(self.signal_label)

        # Rage badge
        self.rage_label = QLabel("")
        layout.addWidget(self.rage_label)

        # Log
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

    def toggle_focus(self):
        self.focus_on = not self.focus_on
        self.focus_btn.setText(
            "FOCUS MODE – ON" if self.focus_on else "FOCUS MODE – OFF"
        )
        if self.agent:
            self.agent.set_focus_mode(self.focus_on)

    # Called from agent thread
    def update_from_agent(self, data: dict):
        self.bridge.updated.emit(data)

    # Runs on UI thread
    def handle_update(self, data: dict):
        score = data.get("score", 0)
        zone = data.get("zone", "NORMAL")
        signals = data.get("signals", {})
        log = data.get("log")

        self.score_bar.setValue(int(score))
        self.zone_label.setText(f"Zone: {zone}")
        self.signal_label.setText(f"Signals: {signals}")

        if zone == "RAGE":
            self.rage_label.setText("🔥 RAGE DETECTED 🔥")
        else:
            self.rage_label.setText("")

        if log:
            self.log_box.append(log)
