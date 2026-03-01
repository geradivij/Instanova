# agent.py — full agentic loop with persistent memory

import time
import threading
from signal_collector import SignalCollector
from load_score import LoadScoreEngine
from memory import AgentMemory


class CLRAgent:
    def __init__(self, ui_callback=None, vision_pipeline=None):
        self.focus_mode = False
        self.auto_focus_enabled = True
        self.collector = SignalCollector()
        self.scorer = LoadScoreEngine()
        self.vision_state = {}
        self.ui_callback = ui_callback
        self.last_zone = "NORMAL"
        self.vision_pipeline = vision_pipeline

        # Persistent memory — this is what makes it truly adaptive
        self.memory = AgentMemory()
        self.cooldown_secs = self.memory.get_adapted_cooldown()
        self.last_intervention = 0
        self.last_intervention_idx = -1   # for outcome tracking
        self.last_intervention_score = 0

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
            from voice_output import speak_focus_on, speak_focus_off
            if enabled:
                # warn if this is a historically bad hour
                warning = self.memory.get_peak_hour_warning()
                if warning:
                    from voice_output import speak_text
                    speak_text(warning)
                else:
                    speak_focus_on()
            else:
                speak_focus_off()
                print("[MEMORY]\n" + self.memory.summary())
        except Exception:
            pass

    def on_stress_detected(self, text: str):
        print(f"[AGENT] Stress phrase heard: '{text}'")
        self._execute("stress_voice")

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
            self.set_focus_mode(True); return
        if switches >= 6 and bursts >= 3:
            self.set_focus_mode(True); return
        if idle >= 60 and face and eye in ("strained", "open"):
            self.set_focus_mode(True); return
        if on_call and call_minutes >= 1 and stressed_face:
            self._execute("nudge"); return
        if "slack" in active_app and idle >= 60 and stressed_face:
            self._execute("hide_chat_and_focus_work"); return

    def _get_action(self, zone, signals, score) -> str | None:
        # 1) Check memory: has a specific action been working well?
        memory_suggestion = self.memory.get_best_action(zone)

        state = {
            "app_switches_30s": signals.get("app_switches_30s", 0),
            "backspace_bursts":  signals.get("backspace_bursts", 0),
            "idle_secs":         signals.get("idle_secs", 0),
            "eye_state":         signals.get("eye_state", "unknown"),
            "load_score":        score,
            "active_app":        signals.get("active_app", "other"),
        }

        # 2) Ask Gemma
        try:
            from gemma_decider_local import get_label
            gemma_label = get_label(state)
            print(f"[AGENT] Gemma -> {gemma_label}")
        except Exception as e:
            print(f"[AGENT] Gemma fallback ({e})")
            gemma_label = "rage_break" if zone == "RAGE" else "hide_chat_and_focus_work"

        # 3) Memory overrides Gemma if it has learned a better action
        if memory_suggestion and memory_suggestion != gemma_label:
            print(f"[AGENT] Memory overrides Gemma: {gemma_label} -> {memory_suggestion}")
            label = memory_suggestion
        else:
            label = gemma_label

        return self.action_map.get(label)

    def _execute(self, action_str):
        if not action_str:
            return
        print(f"[AGENT] Executing: {action_str}")
        try:
            from action_executor import execute_action
            execute_action(action_str, vision_pipeline=self.vision_pipeline)
        except Exception as e:
            print(f"[AGENT] executor error: {e}")

    def _observe_outcome(self, idx, score_before):
        """Run 2 min after intervention — did it actually help?"""
        def _check():
            time.sleep(120)
            signals = self.collector.get_state(self.vision_state)
            result  = self.scorer.compute(signals)
            score_after = result.get("score", 0)

            # simple heuristic: did they reopen distractions within 2 min?
            active = (signals.get("active_app") or "").lower()
            distraction_keywords = ["slack", "discord", "whatsapp", "youtube", "twitter"]
            reopened = any(k in active for k in distraction_keywords)

            self.memory.observe_outcome(idx, score_after, reopened)
            print(f"[MEMORY] Outcome: score {score_before}->{score_after}, reopened={reopened}")

            # adaptive voice if it worked
            if score_after < score_before - 10 and not reopened:
                try:
                    from voice_output import speak_text
                    speak_text("Good. Your load came down. Nice reset.")
                except Exception:
                    pass

        threading.Thread(target=_check, daemon=True).start()

    def _run_loop(self):
        while True:
            time.sleep(2)
            signals = self.collector.get_state(self.vision_state)
            result  = self.scorer.compute(signals)
            score   = result.get("score", 0)
            zone    = result.get("zone", "NORMAL")

            print(f"[AGENT] Score={score} Zone={zone} App={signals.get('active_app','?')}")

            if self.ui_callback:
                self.ui_callback({"score": score, "zone": zone, "signals": signals, "log": None})

            # voice on zone transition
            if zone != self.last_zone:
                try:
                    from voice_output import speak_elevated
                    if zone == "ELEVATED" and self.focus_mode:
                        speak_elevated()
                except Exception:
                    pass

            self.last_zone = zone

            # adapt cooldown from memory each loop
            self.cooldown_secs = self.memory.get_adapted_cooldown()

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

                    # record BEFORE acting
                    idx = self.memory.record_intervention(action, score, zone)
                    self._execute(action)
                    self.last_intervention = time.time()
                    self.last_intervention_score = score

                    # schedule outcome observation 2 min later
                    self._observe_outcome(idx, score)

    def start(self):
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()
        print("[AGENT] CLR Agent started.")