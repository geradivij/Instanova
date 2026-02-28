import time

class LoadScoreEngine:
    # Weights — tune quickly during testing
    WEIGHTS = {
        'app_switches_30s': 8,   # distraction
        'backspace_bursts': 6,   # frustration
        'idle_with_face': 5,     # stuck/confused
        'eye_strained': 4,       # fatigue (later, from vision)
    }

    OVERLOAD_THRESHOLD = 40
    ELEVATED_THRESHOLD = 20
    RAGE_THRESHOLD = 60

    def __init__(self):
        self.history = []  # (timestamp, score)

    def compute(self, signal_state: dict):
        s = signal_state
        score = 0

        # cap extreme values so score doesn't explode
        score += min(s.get('app_switches_30s', 0), 8) * self.WEIGHTS['app_switches_30s']
        score += min(s.get('backspace_bursts', 0), 6) * self.WEIGHTS['backspace_bursts']

        # only count idle if face is present (later vision will set this)
        if s.get('face_present', True) and s.get('idle_secs', 0) > 20:
            score += min(s['idle_secs'] // 10, 6) * self.WEIGHTS['idle_with_face']

        if s.get('eye_state') == 'strained':
            score += self.WEIGHTS['eye_strained']
        
        if s.get('stressed_face'):
            score += self.WEIGHTS.get('eye_strained', 4)

        score = min(int(score), 100)
        self.history.append((time.time(), score))

        zone = (
            'RAGE' if score >= self.RAGE_THRESHOLD else
            'OVERLOAD' if score >= self.OVERLOAD_THRESHOLD else
            'ELEVATED' if score >= self.ELEVATED_THRESHOLD else
            'NORMAL'
        )
        return {'score': score, 'zone': zone}