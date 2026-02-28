import time, threading, collections
from pynput import keyboard, mouse

# --- Windows active window title ---
try:
    import pygetwindow as gw
    def GET_WINDOW():
        w = gw.getActiveWindow()
        return w.title if w else ''
except Exception:
    GET_WINDOW = lambda: ''  # fallback


class SignalCollector:
    def __init__(self, window_secs=30):
        self.window_secs = window_secs
        self.backspace_times = collections.deque()   # timestamps of backspaces
        self.window_switches = collections.deque()   # timestamps of app switches
        self.last_activity = time.time()             # for idle detection
        self.last_window = ''
        self._start_listeners()

    def _start_listeners(self):
        # Keyboard listener
        def on_key(key):
            self.last_activity = time.time()
            if key == keyboard.Key.backspace:
                self.backspace_times.append(time.time())
        keyboard.Listener(on_press=on_key).start()

        # Mouse listener (any move = not idle)
        def on_move(x, y):
            self.last_activity = time.time()
        mouse.Listener(on_move=on_move).start()

        # App switch tracker — poll every 1 second
        def poll_window():
            while True:
                try:
                    w = GET_WINDOW()
                    if w and w != self.last_window:
                        self.window_switches.append(time.time())
                        self.last_window = w
                except Exception:
                    pass
                time.sleep(1)

        threading.Thread(target=poll_window, daemon=True).start()

    def _prune(self, dq, cutoff):
        while dq and dq[0] < cutoff:
            dq.popleft()

    def get_state(self, vision_state=None):
        now = time.time()
        cutoff = now - self.window_secs

        # Prune old events
        self._prune(self.window_switches, cutoff)
        self._prune(self.backspace_times, cutoff)

        # Count app switches in last 30s
        switches = len(self.window_switches)

        # Count backspace bursts (5+ backspaces within 3 seconds)
        # We'll count how many burst "windows" start points satisfy this.
        bs = list(self.backspace_times)
        bursts = 0
        j = 0
        for i in range(len(bs)):
            while j < len(bs) and bs[j] - bs[i] <= 3:
                j += 1
            if (j - i) >= 5:
                bursts += 1

        # Idle time (seconds since last activity)
        idle_secs = int(now - self.last_activity)

        # Merge optional vision state
        eye_state = vision_state.get('eye_state', 'unknown') if vision_state else 'unknown'
        face_present = vision_state.get('face_present', True) if vision_state else True

        return {
            'app_switches_30s': switches,
            'backspace_bursts': bursts,
            'idle_secs': idle_secs,
            'face_present': face_present,
            'eye_state': eye_state,   # 'open', 'strained', 'closed'
        }


if __name__ == '__main__':
    sc = SignalCollector()
    print('Collecting signals... (switch apps, move mouse, spam backspace)')
    for _ in range(12):   # ~1 minute
        time.sleep(5)
        print(sc.get_state())