# vision_pipeline.py
import threading, time
import cv2

class VisionPipeline:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.cap = cv2.VideoCapture(0)
        self.state = {
            "face_present": False,
            "eye_state": "unknown",
            "stressed_face": False,
        }
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while True:
            ok, frame = self.cap.read()
            if not ok:
                self.state = {
                    "face_present": False,
                    "eye_state": "unknown",
                    "stressed_face": False,
                }
                time.sleep(0.5)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                face_present = False
                eye_state = "closed"
            else:
                face_present = True
                # simple heuristic: if face present, assume eyes open
                eye_state = "open"

            # fast proxy: strained == not fully open or no face
            stressed_face = (eye_state == "strained") or (face_present and eye_state != "open")

            self.state = {
                "face_present": face_present,
                "eye_state": eye_state,
                "stressed_face": stressed_face,
            }

            time.sleep(0.5)

    def get_state(self):
        return dict(self.state)

if __name__ == "__main__":
    v = VisionPipeline()
    print("Testing vision…")
    for _ in range(10):
        print(v.get_state())
        time.sleep(1)
