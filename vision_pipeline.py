# vision_pipeline.py — works with mediapipe 0.10+ (new API) + fallback to haar

import threading
import time
import cv2

MEDIAPIPE_OK = False
mp_face_mesh = None
mp_hands = None

try:
    import mediapipe as mp
    # mediapipe 0.10+ uses new task-based API on some builds
    # try old solutions API first
    try:
        _ = mp.solutions.face_mesh
        _ = mp.solutions.hands
        MEDIAPIPE_OK = True
        MEDIAPIPE_NEW = False
        print("[VISION] mediapipe solutions API ready")
    except AttributeError:
        # try new API
        try:
            from mediapipe.tasks import python as mp_tasks
            from mediapipe.tasks.python import vision as mp_vision
            MEDIAPIPE_OK = True
            MEDIAPIPE_NEW = True
            print("[VISION] mediapipe tasks API ready")
        except Exception as e2:
            print(f"[VISION] mediapipe both APIs failed: {e2}, using haar fallback")
            MEDIAPIPE_OK = False
except ImportError:
    print("[VISION] mediapipe not installed — run: pip install mediapipe==0.10.9")


class VisionPipeline:

    LEFT_EYE  = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]
    MOUTH_TOP    = 13
    MOUTH_BOTTOM = 14
    MOUTH_LEFT   = 78
    MOUTH_RIGHT  = 308

    def __init__(self):
        self.state = {
            "face_present":    False,
            "eye_state":       "unknown",
            "stressed_face":   False,
            "mouth_open":      False,
            "hand_on_face":    False,
            "hand_on_head":    False,
            "stress_gestures": 0,
        }

        self._hand_on_face_frames = 0
        self._hand_on_head_frames = 0
        self._eye_strained_frames = 0
        self._mouth_open_frames   = 0

        self._init_detectors()
        self._cap = cv2.VideoCapture(0)

        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _init_detectors(self):
        global MEDIAPIPE_OK
        if not MEDIAPIPE_OK:
            self._setup_haar()
            return
        try:
            import mediapipe as mp
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._hands = mp.solutions.hands.Hands(
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            print("[VISION] Face mesh + hands initialised")
        except Exception as e:
            print(f"[VISION] mediapipe init error: {e} — falling back to haar")
            MEDIAPIPE_OK = False
            self._setup_haar()

    def _setup_haar(self):
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        print("[VISION] Using haar fallback (no hand/eye strain detection)")

    # ── EAR helper ─────────────────────────────────────────────────────
    def _ear(self, lm, indices, w, h):
        pts = [(lm[i].x * w, lm[i].y * h) for i in indices]
        v1 = abs(pts[1][1] - pts[5][1])
        v2 = abs(pts[2][1] - pts[4][1])
        horiz = abs(pts[0][0] - pts[3][0])
        return (v1 + v2) / (2.0 * horiz) if horiz > 0 else 0.3

    # ── MediaPipe analysis ─────────────────────────────────────────────
    def _analyse_mp(self, frame):
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False

        face_result  = self._face_mesh.process(rgb)
        hands_result = self._hands.process(rgb)

        rgb.flags.writeable = True

        face_present = False
        eye_state    = "unknown"
        mouth_open   = False
        hof = hoh    = False

        if face_result.multi_face_landmarks:
            face_present = True
            lm = face_result.multi_face_landmarks[0].landmark

            # Eye strain
            left_ear  = self._ear(lm, self.LEFT_EYE,  w, h)
            right_ear = self._ear(lm, self.RIGHT_EYE, w, h)
            avg_ear   = (left_ear + right_ear) / 2.0

            if avg_ear < 0.18:
                self._eye_strained_frames += 1
            else:
                self._eye_strained_frames = max(0, self._eye_strained_frames - 1)

            if avg_ear < 0.14:
                eye_state = "closed"
            elif self._eye_strained_frames >= 8:
                eye_state = "strained"
            else:
                eye_state = "open"

            # Mouth open
            vert  = abs(lm[self.MOUTH_BOTTOM].y - lm[self.MOUTH_TOP].y) * h
            horiz = abs(lm[self.MOUTH_RIGHT].x  - lm[self.MOUTH_LEFT].x) * w
            mar   = vert / horiz if horiz > 0 else 0
            if mar > 0.35:
                self._mouth_open_frames += 1
            else:
                self._mouth_open_frames = max(0, self._mouth_open_frames - 1)
            mouth_open = self._mouth_open_frames >= 4

            # Face bounding box
            xs = [l.x for l in lm]
            ys = [l.y for l in lm]
            fx_min, fx_max = min(xs), max(xs)
            fy_min, fy_max = min(ys), max(ys)

            # Hand proximity
            found_hof = found_hoh = False
            if hands_result.multi_hand_landmarks:
                for hand_lm in hands_result.multi_hand_landmarks:
                    for idx in [0, 4, 8, 12, 16, 20]:
                        hx = hand_lm.landmark[idx].x
                        hy = hand_lm.landmark[idx].y
                        # inside face box → hand on face
                        if fx_min - 0.05 < hx < fx_max + 0.05 and fy_min - 0.05 < hy < fy_max + 0.1:
                            found_hof = True
                        # above face box → hand on head
                        if fx_min - 0.12 < hx < fx_max + 0.12 and hy < fy_min + 0.04:
                            found_hoh = True

            if found_hof:
                self._hand_on_face_frames += 1
            else:
                self._hand_on_face_frames = max(0, self._hand_on_face_frames - 1)

            if found_hoh:
                self._hand_on_head_frames += 1
            else:
                self._hand_on_head_frames = max(0, self._hand_on_head_frames - 1)

            hof = self._hand_on_face_frames >= 5
            hoh = self._hand_on_head_frames >= 5

        return face_present, eye_state, mouth_open, hof, hoh

    def _analyse_haar(self, frame):
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._face_cascade.detectMultiScale(gray, 1.3, 5)
        return len(faces) > 0, "open", False, False, False

    def _loop(self):
        while True:
            ok, frame = self._cap.read()
            if not ok:
                time.sleep(0.5)
                continue
            try:
                if MEDIAPIPE_OK:
                    fp, eye, mouth, hof, hoh = self._analyse_mp(frame)
                else:
                    fp, eye, mouth, hof, hoh = self._analyse_haar(frame)
            except Exception as e:
                print(f"[VISION] frame error: {e}")
                time.sleep(0.5)
                continue

            stressed = (eye == "strained") or hof or hoh
            gestures = self.state.get("stress_gestures", 0)
            if hof or hoh:
                gestures += 1

            self.state = {
                "face_present":    fp,
                "eye_state":       eye,
                "stressed_face":   stressed,
                "mouth_open":      mouth,
                "hand_on_face":    hof,
                "hand_on_head":    hoh,
                "stress_gestures": gestures,
            }
            time.sleep(0.15)

    def get_state(self):
        return dict(self.state)


if __name__ == "__main__":
    v = VisionPipeline()
    print("Testing — put your hand on your face or head...")
    for _ in range(30):
        s = v.get_state()
        print(
            f"face={s['face_present']}  eye={s['eye_state']}  "
            f"hand_on_face={s['hand_on_face']}  hand_on_head={s['hand_on_head']}  "
            f"stressed={s['stressed_face']}"
        )
        time.sleep(1)