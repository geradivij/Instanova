from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QProgressBar, QLabel, QFrame, QSizeGrip
)
from PyQt5.QtCore import pyqtSignal, QObject, Qt, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QPen, QBrush


class AgentBridge(QObject):
    updated = pyqtSignal(dict)


# ── Drag support for frameless window ──────────────────────────────────────
class DraggableWidget(QWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._drag_pos = None

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos:
            self.window().move(e.globalPos() - self._drag_pos)


# ── Animated score arc (custom widget) ────────────────────────────────────
class ScoreArc(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self._score = 0
        self._color = QColor("#A6E3A1")

    def set_score(self, score, color):
        self._score = score
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)

        # background arc
        pen = QPen(QColor("#313244"), 7, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 225 * 16, -270 * 16)

        # score arc
        span = int(-270 * 16 * self._score / 100)
        pen2 = QPen(self._color, 7, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen2)
        painter.drawArc(rect, 225 * 16, span)

        # center text
        painter.setPen(QColor("#CDD6F4"))
        font = QFont("Courier New", 13, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, str(self._score))


# ── Main HUD window ────────────────────────────────────────────────────────
class CLRDashboard(QMainWindow):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.focus_on = False

        self.setWindowTitle("CLR – Focus Companion")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(420, 240)
        self.move(20, 30)

        self.bridge = AgentBridge()
        self.bridge.updated.connect(self.handle_update)

        self._build_ui()

    def _build_ui(self):
        outer = DraggableWidget()
        outer.setObjectName("outer")
        outer.setStyleSheet("""
            QWidget#outer {
                background: rgba(17, 17, 27, 235);
                border: 1px solid rgba(137, 180, 250, 0.25);
                border-radius: 16px;
            }
        """)
        self.setCentralWidget(outer)

        root = QVBoxLayout(outer)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # ── Header row ──────────────────────────────────────────────
        header = QHBoxLayout()

        title = QLabel("CLR")
        title.setFont(QFont("Courier New", 14, QFont.Bold))
        title.setStyleSheet("color: #89B4FA; letter-spacing: 3px;")

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #313244; font-size: 10px;")

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #585B70; border: none; font-size: 12px; }
            QPushButton:hover { color: #F38BA8; }
        """)

        header.addWidget(title)
        header.addWidget(self.status_dot)
        header.addStretch()
        header.addWidget(self.close_btn)
        root.addLayout(header)

        # ── Score + State row ────────────────────────────────────────
        score_row = QHBoxLayout()
        score_row.setSpacing(14)

        self.arc = ScoreArc()
        score_row.addWidget(self.arc)

        info_col = QVBoxLayout()
        info_col.setSpacing(4)

        self.zone_label = QLabel("CALM")
        self.zone_label.setFont(QFont("Courier New", 16, QFont.Bold))
        self.zone_label.setStyleSheet("color: #A6E3A1; letter-spacing: 2px;")
        info_col.addWidget(self.zone_label)

        self.coach_label = QLabel("")
        self.coach_label.setWordWrap(True)
        self.coach_label.setFont(QFont("Helvetica", 10))
        self.coach_label.setStyleSheet("color: #CDD6F4;")
        info_col.addWidget(self.coach_label)

        self.signal_label = QLabel("Signals: –")
        self.signal_label.setFont(QFont("Courier New", 8))
        self.signal_label.setStyleSheet("color: #585B70;")
        info_col.addWidget(self.signal_label)

        score_row.addLayout(info_col)
        root.addLayout(score_row)

        # ── Divider ──────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: rgba(137,180,250,0.12);")
        root.addWidget(line)

        # ── Focus button ─────────────────────────────────────────────
        self.focus_btn = QPushButton("▶  START FOCUS SESSION")
        self.focus_btn.clicked.connect(self.toggle_focus)
        self.focus_btn.setFont(QFont("Courier New", 10, QFont.Bold))
        self.focus_btn.setFixedHeight(38)
        self.focus_btn.setCursor(Qt.PointingHandCursor)
        self._set_btn_idle()
        root.addWidget(self.focus_btn)

        # ── Log strip ────────────────────────────────────────────────
        self.log_label = QLabel("")
        self.log_label.setFont(QFont("Courier New", 8))
        self.log_label.setStyleSheet("color: #45475A;")
        root.addWidget(self.log_label)

    def _set_btn_idle(self):
        self.focus_btn.setStyleSheet("""
            QPushButton {
                background: rgba(137,180,250,0.12);
                color: #89B4FA;
                border: 1px solid rgba(137,180,250,0.35);
                border-radius: 10px;
                padding: 6px 14px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(137,180,250,0.22);
            }
        """)

    def _set_btn_active(self):
        self.focus_btn.setStyleSheet("""
            QPushButton {
                background: rgba(166,227,161,0.15);
                color: #A6E3A1;
                border: 1px solid rgba(166,227,161,0.45);
                border-radius: 10px;
                padding: 6px 14px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(166,227,161,0.25);
            }
        """)

    # ── called from agent thread ──────────────────────────────────────
    def update_from_agent(self, data: dict):
        self.bridge.updated.emit(data)

    # ── runs on UI thread ─────────────────────────────────────────────
    def handle_update(self, data: dict):
        score   = data.get("score", 0)
        zone    = data.get("zone", "NORMAL")
        signals = data.get("signals", {})
        log     = data.get("log")

        # zone colours
        ZONE_CFG = {
            "RAGE":     ("#F38BA8", "OVERLOADED",     "Distractions paused. Breathe."),
            "OVERLOAD": ("#FAB387", "HIGH LOAD",      "Noise muted. Stay in flow."),
            "ELEVATED": ("#F9E2AF", "FOCUSED+",       "Load rising — I'm watching."),
            "NORMAL":   ("#A6E3A1", "CALM",           ""),
        }
        color, state_text, coach = ZONE_CFG.get(zone, ZONE_CFG["NORMAL"])

        # call nudge override
        if zone == "NORMAL" and signals.get("on_call") and signals.get("call_minutes", 0) >= 1:
            coach = "Long call — ready to get back?"

        self.arc.set_score(int(score), color)
        self.zone_label.setText(state_text)
        self.zone_label.setStyleSheet(f"color: {color}; letter-spacing: 2px;")
        self.coach_label.setText(coach)

        # status dot
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 10px;")

        # compact signal line
        sw  = signals.get("app_switches_30s", 0)
        bs  = signals.get("backspace_bursts", 0)
        id_ = signals.get("idle_secs", 0)
        ey  = signals.get("eye_state", "?")
        app = signals.get("active_app", "")
        self.signal_label.setText(
            f"sw:{sw}  bs:{bs}  idle:{id_}s  eye:{ey}  app:{app or '–'}"
        )

        if log:
            self.log_label.setText(f"⚡ {log}")

    def toggle_focus(self):
        self.focus_on = not self.focus_on
        if self.focus_on:
            self.focus_btn.setText("■  FOCUS SESSION ACTIVE")
            self._set_btn_active()
        else:
            self.focus_btn.setText("▶  START FOCUS SESSION")
            self._set_btn_idle()
            self.coach_label.setText("")

        if self.agent:
            self.agent.set_focus_mode(self.focus_on)