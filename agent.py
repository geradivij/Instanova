# agent.py

import time
import threading
from signal_collector import SignalCollector
from load_score import LoadScoreEngine


class CLRAgent:
    def __init__(self, ui_callback=None):
        self.focus_mode = False
        self.auto_focus_enabled = True  # allow auto-on
        self.collector = SignalCollector()
        self.scorer = LoadScoreEngine()
        self.last_intervention = 0
        self.cooldown_secs = 60  # avoid spamming actions
        self.vision_state = {}
        self.ui_callback = ui_callback  # dashboard hook
        self.last_zone = "NORMAL"

    def set_vision_state(self, vs: dict):
        self.vision_state = vs or {}

    def set_focus_mode(self, enabled: bool):
        self.focus_mode = enabled
        print(f"Focus Mode: {'ON' if enabled else 'OFF'}")

    def maybe_auto_focus(self, score, zone, signals):
        if not self.auto_focus_enabled:
            return
        if self.focus_mode:
            return

        switches = signals.get("app_switches_30s", 0)
        bursts = signals.get("backspace_bursts", 0)
        idle = signals.get("idle_secs", 0)
        eye = signals.get("eye_state", "unknown")
        face = signals.get("face_present", True)
        stressed_face = signals.get("stressed_face", False)
        on_call = signals.get("on_call", False)
        call_minutes = signals.get("call_minutes", 0)
        active_app = (signals.get("active_app") or "").lower()

        # 1) Score already very high
        if score >= 80:
            self.set_focus_mode(True)
            return

        # 2) Thrashing between apps + frustrated typing
        if switches >= 6 and bursts >= 3:
            self.set_focus_mode(True)
            return

        # 3) Stuck + staring at screen
        if idle >= 60 and face and eye in ("strained", "open"):
            self.set_focus_mode(True)
            return

        # 4) On call for too long while face looks stressed -> soft nudge
        if on_call and call_minutes >= 1 and stressed_face:
            try:
                from action_executor import execute_action
                execute_action("nudge")
            except ImportError:
                print("[AGENT] would nudge after long stressed call")
            return

        # 5) Idle in Slack for ~1 minute and stressed -> hide Slack & reset
        if "slack" in active_app and idle >= 60 and stressed_face:
            try:
                from action_executor import execute_action
                execute_action("hide_slack_and_break")
            except ImportError:
                print("[AGENT] would hide Slack after idle stressed minute")
            return

    def _decide_action(self, zone, signals, score):
        # simple heuristic for now; later you can call Gemma here
        if zone == "RAGE":
            return "rage_break"
        elif zone == "OVERLOAD":
            return "hide_slack_and_break"
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
            time.sleep(2)  # faster updates

            signals = self.collector.get_state(self.vision_state)
            result = self.scorer.compute(signals)

            if isinstance(result, dict):
                score = result.get("score", 0)
                zone = result.get("zone", "NORMAL")
            else:
                score, zone = result

            print(f"[AGENT] Score: {score} | Zone: {zone} | Signals: {signals}")

            # send structured data to dashboard
            if self.ui_callback:
                data = {
                    "score": score,
                    "zone": zone,
                    "signals": signals,
                    "log": None,
                }
                self.ui_callback(data)

            # gentle voice when first entering ELEVATED (optional)
            if zone == "ELEVATED" and self.focus_mode and self.last_zone != "ELEVATED":
                try:
                    from voice_output import speak_text
                    speak_text(
                        "Your load is rising. If you want, I can protect your focus."
                    )
                except ImportError:
                    pass

            self.last_zone = zone

            # auto-enable Focus Mode / nudges / Slack rule
            self.maybe_auto_focus(score, zone, signals)

            if not self.focus_mode:
                continue

            cooldown_ok = (time.time() - self.last_intervention) > self.cooldown_secs

            if zone in ("OVERLOAD", "RAGE") and cooldown_ok:
                action = self._decide_action(zone, signals, score)
                if action:
                    log = f"{time.strftime('%H:%M')} – {action} at score {score}"
                    if self.ui_callback:
                        self.ui_callback(
                            {
                                "score": score,
                                "zone": zone,
                                "signals": signals,
                                "log": log,
                            }
                        )
                    self._execute(action)
                    self.last_intervention = time.time()

    def start(self):
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()
        print("CLR Agent started.")
