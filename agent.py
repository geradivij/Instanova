# agent.py  — final integrated version

import time
import threading
from signal_collector import SignalCollector
from load_score import LoadScoreEngine


class CLRAgent:
    def __init__(self, ui_callback=None):
        self.focus_mode = False
        self.auto_focus_enabled = True
        self.collector = SignalCollector()
        self.scorer = LoadScoreEngine()
        self.last_intervention = 0
        self.cooldown_secs = 60
        self.vision_state = {}
        self.ui_callback = ui_callback
        self.last_zone = "NORMAL"

        # Gemma label  →  executor action string
        self.action_map = {
            "hide_chat_and_focus_work": "hide_chat_and_focus_work",
            "soft_nudge":               "nudge",
            "enforce_break":            "enforce_break",
            "rage_break":               "rage_break",
            "no_action":                None,
        }

    def set_vision_state(self, vs: dict):
        self.vision_state = vs or {}

    def set_focus_mode(self, enabled: bool):
        self.focus_mode = enabled
        print(f"[AGENT] Focus Mode: {'ON' if enabled else 'OFF'}")
        try:
            from voice_output import speak_text
            if enabled:
                speak_text("Focus mode activated. I'll protect your attention.")
            else:
                speak_text("Focus mode off. Good work.")
        except Exception:
            pass

    # ── Auto-enable focus / quick actions outside focus mode ──────────
    def maybe_auto_focus(self, score, zone, signals):
        if not self.auto_focus_enabled or self.focus_mode:
            return

        switches      = signals.get("app_switches_30s", 0)
        bursts        = signals.get("backspace_bursts", 0)
        idle          = signals.get("idle_secs", 0)
        eye           = signals.get("eye_state", "unknown")
        face          = signals.get("face_present", True)
        stressed_face = signals.get("stressed_face", False)
        on_call       = signals.get("on_call", False)
        call_minutes  = signals.get("call_minutes", 0)
        active_app    = (signals.get("active_app") or "").lower()

        if score >= 80:
            self.set_focus_mode(True)
            return
        if switches >= 6 and bursts >= 3:
            self.set_focus_mode(True)
            return
        if idle >= 60 and face and eye in ("strained", "open"):
            self.set_focus_mode(True)
            return
        if on_call and call_minutes >= 1 and stressed_face:
            self._execute("nudge")
            return
        if "slack" in active_app and idle >= 60 and stressed_face:
            self._execute("hide_chat_and_focus_work")
            return

    # ── Gemma decision with heuristic fallback ────────────────────────
    def _get_action(self, zone, signals, score):
        state = {
            "app_switches_30s": signals.get("app_switches_30s", 0),
            "backspace_bursts":  signals.get("backspace_bursts", 0),
            "idle_secs":         signals.get("idle_secs", 0),
            "eye_state":         signals.get("eye_state", "unknown"),
            "load_score":        score,
            "active_app":        signals.get("active_app", "other"),
        }
        try:
            from gemma_decider_local import get_label
            label = get_label(state)
            print(f"[AGENT] Gemma → {label}")
        except Exception as e:
            print(f"[AGENT] Gemma unavailable ({e}), using heuristic fallback")
            label = "rage_break" if zone == "RAGE" else "hide_chat_and_focus_work"

        return self.action_map.get(label)

    def _execute(self, action_str):
        if not action_str:
            return
        print(f"[AGENT] Executing: {action_str}")
        try:
            from action_executor import execute_action
            execute_action(action_str)
        except Exception as e:
            print(f"[AGENT] executor error: {e}")

    # ── Main loop ─────────────────────────────────────────────────────
    def _run_loop(self):
        while True:
            time.sleep(2)

            signals = self.collector.get_state(self.vision_state)
            result  = self.scorer.compute(signals)
            score   = result.get("score", 0)
            zone    = result.get("zone", "NORMAL")

            print(f"[AGENT] Score={score} Zone={zone} App={signals.get('active_app','?')}")

            # push live data to dashboard
            if self.ui_callback:
                self.ui_callback({"score": score, "zone": zone, "signals": signals, "log": None})

            # voice hint on first ELEVATED entry (while focus mode on)
            if zone == "ELEVATED" and self.focus_mode and self.last_zone not in ("ELEVATED", "OVERLOAD", "RAGE"):
                try:
                    from voice_output import speak_text
                    speak_text("Your load is rising. I'm keeping an eye on things.")
                except Exception:
                    pass

            self.last_zone = zone

            # auto-trigger even without focus mode
            self.maybe_auto_focus(score, zone, signals)

            if not self.focus_mode:
                continue

            cooldown_ok = (time.time() - self.last_intervention) > self.cooldown_secs
            if zone in ("OVERLOAD", "RAGE") and cooldown_ok:
                action = self._get_action(zone, signals, score)
                if action:
                    log = f"{time.strftime('%H:%M')} – {action} (score {score})"
                    if self.ui_callback:
                        self.ui_callback({"score": score, "zone": zone, "signals": signals, "log": log})
                    self._execute(action)
                    self.last_intervention = time.time()

    def start(self):
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()
        print("[AGENT] CLR Agent started.")