# agent.py

import time
import threading
from signal_collector import SignalCollector
from load_score import LoadScoreEngine

from gemma_decider_local import get_label


class CLRAgent:
    def __init__(self, ui_callback=None):
        self.focus_mode = False
        self.auto_focus_enabled = True  # allow auto-on
        self.collector = SignalCollector()
        self.scorer = LoadScoreEngine()
        self.last_intervention = 0
        self.cooldown_secs = 60
        self.vision_state = {}

        self.action_map = {
            "hide_chat_and_focus_work": 'hide_app(target="slack")',
            "soft_nudge": 'trigger_break(duration_secs=60, message="Quick reset: 60 seconds.")',
            "enforce_break": 'trigger_break(duration_secs=180, message="Take a short break.")',
            "rage_break": 'hide_app(target="slack") and trigger_break(duration_secs=180, message="Rage detected. Step away.")',
            "no_action": None,
        }

    def set_vision_state(self, vs: dict):
        self.vision_state = vs or {}

    def set_focus_mode(self, enabled: bool):
        self.focus_mode = enabled
        print(f"Focus Mode: {'ON' if enabled else 'OFF'}")

    def _execute(self, action_str):
        print(f"[AGENT] Executing: {action_str}")
        try:
            from action_executor import execute_action
            execute_action(action_str)
        except ImportError:
            print("[AGENT] (action_executor not ready yet — demo print only)")

    def _run_loop(self):
        while True:
            time.sleep(2)  # faster updates

            signals = self.collector.get_state(self.vision_state)
            result = self.scorer.compute(signals)

            score = result["score"]
            zone = result["zone"]
            print(f"[AGENT] Score: {score} | Zone: {zone}")

            if not self.focus_mode:
                continue

            # Only consider intervention in these zones
            if zone not in ("OVERLOAD", "RAGE"):
                continue

            cooldown_ok = (time.time() - self.last_intervention) > self.cooldown_secs
            if not cooldown_ok:
                continue

            state = {
                "app_switches_30s": signals.get("app_switches_30s", 0),
                "backspace_bursts": signals.get("backspace_bursts", 0),
                "idle_secs": signals.get("idle_secs", 0),
                "face_present": signals.get("face_present", True),
                "eye_state": signals.get("eye_state", "unknown"),
                "load_score": score,
                "active_app": signals.get("active_app", "other"),
            }

            try:
                label = get_label(state)
                print("[AGENT] Gemma label:", label)
                action = self.action_map.get(label, None)
            except Exception as e:
                print("[AGENT] Gemma error, fallback:", e)
                action = self.action_map["rage_break"] if zone == "RAGE" else self.action_map["hide_chat_and_focus_work"]

            if action:
                self._execute(action)
                self.last_intervention = time.time()

    def start(self):
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()
        print("CLR Agent started.")
