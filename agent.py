import time
import threading
from signal_collector import SignalCollector
from load_score import LoadScoreEngine

class CLRAgent:
    def __init__(self):
        self.focus_mode = False
        self.collector = SignalCollector()
        self.scorer = LoadScoreEngine()
        self.last_intervention = 0
        self.cooldown_secs = 60  # avoid spamming actions

    def set_focus_mode(self, enabled: bool):
        self.focus_mode = enabled
        print(f"Focus Mode: {'ON' if enabled else 'OFF'}")

    def _decide_action(self, zone):
        # RULE-BASED LOGIC (Gemma later)
        if zone == "RAGE":
            return 'hide_app(target="slack") and trigger_break(duration_secs=180, message="Rage detected. Step away.")'
        elif zone == "OVERLOAD":
            return 'hide_app(target="slack")'
        else:
            return None

    def _execute(self, action_str):
        print(f"[AGENT] Executing: {action_str}")
        try:
            from action_executor import execute_action
            execute_action(action_str)
        except ImportError:
            print("[AGENT] (action_executor not ready yet — demo print only)")

    def _run_loop(self):
        while True:
            time.sleep(5)

            signals = self.collector.get_state()
            result = self.scorer.compute(signals)

            score = result["score"]
            zone = result["zone"]

            print(f"[AGENT] Score: {score} | Zone: {zone}")

            if not self.focus_mode:
                continue

            cooldown_ok = (time.time() - self.last_intervention) > self.cooldown_secs

            if zone in ("OVERLOAD", "RAGE") and cooldown_ok:
                action = self._decide_action(zone)
                if action:
                    self._execute(action)
                    self.last_intervention = time.time()

    def start(self):
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()
        print("CLR Agent started.")