# vision_pipeline.py — MediaPipe face mesh + hand tracking

import threading
import time
import cv2

try:
    import mediapipe as mp
    MEDIAPIPE_OK = True
except ImportError:
    MEDIAPIPE_OK = False
    print("[VISION] mediapipe not installed — run: pip install mediapipe")


class VisionPipeline:
    def __init__(self):
        self.state = {
            "face_present":     False,
            "eye_state":        "unknown",   # open / strained / closed
            "stressed_face":    False,
            "mouth_open":       False,
            "hand_on_face":     False,        # ← NEW: hand touching head/face
            "hand_on_head":     False,        # ← NEW: hand resting on top of head
            "stress_gestures":  0,            # cumulative count this session
        }

        self._hand_on_face_frames  = 0
        self._hand_on_head_frames  = 0
        self._eye_strained_frames  = 0
        self._mouth_open_frames    = 0

        if MEDIAPIPE_OK:
            self._mp_face = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._mp_hands = mp.solutions.hands.Hands(
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        else:
            # fallback to basic haar
            self._face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

        self._cap = cv2.VideoCapture(0)
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    # ── Eye openness from face mesh ────────────────────────────────────
    def _eye_aspect_ratio(self, landmarks, indices, w, h):
        """
        EAR = vertical distance / horizontal distance of eye landmarks.
        Low EAR = closed/strained. MediaPipe left eye: 159,145 vertical; 33,133 horizontal.
        """
        pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in indices]
        # vertical
        v1 = abs(pts[1][1] - pts[5][1])
        v2 = abs(pts[2][1] - pts[4][1])
        # horizontal
        h1 = abs(pts[0][0] - pts[3][0])
        if h1 == 0:
            return 0.3
        return (v1 + v2) / (2.0 * h1)

    # Left eye landmark indices in MediaPipe face mesh
    LEFT_EYE  = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]
    # Mouth open: top lip 13, bottom lip 14
    MOUTH_TOP    = 13
    MOUTH_BOTTOM = 14
    MOUTH_LEFT   = 78
    MOUTH_RIGHT  = 308

    def _analyse_mediapipe(self, frame):
        h, w = frame.shape[:2]
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        face_result  = self._mp_face.process(rgb)
        hands_result = self._mp_hands.process(rgb)

        face_present   = False
        eye_state      = "unknown"
        mouth_open     = False
        hand_on_face   = False
        hand_on_head   = False

        # ── Face mesh ─────────────────────────────────────────────────
        if face_result.multi_face_landmarks:
            face_present = True
            lm = face_result.multi_face_landmarks[0].landmark

            # EAR for both eyes
            left_ear  = self._eye_aspect_ratio(lm, self.LEFT_EYE,  w, h)
            right_ear = self._eye_aspect_ratio(lm, self.RIGHT_EYE, w, h)
            avg_ear   = (left_ear + right_ear) / 2.0

            if avg_ear < 0.18:
                self._eye_strained_frames += 1
            else:
                self._eye_strained_frames = max(0, self._eye_strained_frames - 1)

            if avg_ear < 0.15:
                eye_state = "closed"
            elif self._eye_strained_frames >= 8:
                eye_state = "strained"
            else:
                eye_state = "open"

            # Mouth open detection
            top_y    = lm[self.MOUTH_TOP].y * h
            bot_y    = lm[self.MOUTH_BOTTOM].y * h
            left_x   = lm[self.MOUTH_LEFT].x * w
            right_x  = lm[self.MOUTH_RIGHT].x * w
            vert     = abs(bot_y - top_y)
            horiz    = abs(right_x - left_x)
            mar      = vert / horiz if horiz > 0 else 0
            if mar > 0.35:
                self._mouth_open_frames += 1
            else:
                self._mouth_open_frames = max(0, self._mouth_open_frames - 1)
            mouth_open = self._mouth_open_frames >= 4

            # Face bounding box (normalised)
            xs = [l.x for l in lm]
            ys = [l.y for l in lm]
            face_box = {
                "x_min": min(xs), "x_max": max(xs),
                "y_min": min(ys), "y_max": max(ys),
            }

            # ── Hand proximity check ───────────────────────────────────
            if hands_result.multi_hand_landmarks:
                for hand_lm in hands_result.multi_hand_landmarks:
                    # Use wrist (0) and fingertips (4,8,12,16,20)
                    key_pts = [0, 4, 8, 12, 16, 20]
                    for idx in key_pts:
                        hx = hand_lm.landmark[idx].x
                        hy = hand_lm.landmark[idx].y

                        # Hand ON face: fingertip inside face bounding box
                        if (face_box["x_min"] - 0.05 < hx < face_box["x_max"] + 0.05 and
                                face_box["y_min"] - 0.05 < hy < face_box["y_max"] + 0.1):
                            self._hand_on_face_frames += 1
                            break

                        # Hand ON HEAD: hand above the top of the face box
                        if (face_box["x_min"] - 0.1 < hx < face_box["x_max"] + 0.1 and
                                hy < face_box["y_min"] + 0.05):
                            self._hand_on_head_frames += 1
                            break
                    else:
                        self._hand_on_face_frames = max(0, self._hand_on_face_frames - 1)
                        self._hand_on_head_frames = max(0, self._hand_on_head_frames - 1)
            else:
                self._hand_on_face_frames = max(0, self._hand_on_face_frames - 1)
                self._hand_on_head_frames = max(0, self._hand_on_head_frames - 1)

            # Require 5 consecutive frames to confirm gesture
            hand_on_face = self._hand_on_face_frames >= 5
            hand_on_head = self._hand_on_head_frames >= 5

        return face_present, eye_state, mouth_open, hand_on_face, hand_on_head

    def _analyse_fallback(self, frame):
        """Basic haar fallback when mediapipe unavailable."""
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._face_cascade.detectMultiScale(gray, 1.3, 5)
        face_present = len(faces) > 0
        return face_present, "open", False, False, False

    def _loop(self):
        while True:
            ok, frame = self._cap.read()
            if not ok:
                time.sleep(0.5)
                continue

            try:
                if MEDIAPIPE_OK:
                    fp, eye, mouth, hof, hoh = self._analyse_mediapipe(frame)
                else:
                    fp, eye, mouth, hof, hoh = self._analyse_fallback(frame)
            except Exception as e:
                print(f"[VISION] frame error: {e}")
                time.sleep(0.5)
                continue

            # stressed_face = strained eyes OR hand on face/head
            stressed = (eye == "strained") or hof or hoh

            if stressed and (hof or hoh):
                self.state["stress_gestures"] = self.state.get("stress_gestures", 0) + 1

            self.state = {
                "face_present":    fp,
                "eye_state":       eye,
                "stressed_face":   stressed,
                "mouth_open":      mouth,
                "hand_on_face":    hof,
                "hand_on_head":    hoh,
                "stress_gestures": self.state.get("stress_gestures", 0),
            }

            time.sleep(0.15)   # ~6 fps is enough

    def get_state(self):
        return dict(self.state)


if __name__ == "__main__":
    print("Install: pip install mediapipe")
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