# vision_pipeline.py
import threading, time
import cv2

class VisionPipeline:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.mouth_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_smile.xml"
        )
        self.cap = cv2.VideoCapture(0)
        self.state = {
            "face_present": False,
            "eye_state": "unknown",
            "stressed_face": False,
            "mouth_open": False,
        }
        self._mouth_open_frames = 0
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while True:
            ok, frame = self.cap.read()
            if not ok:
                self.state = {"face_present": False, "eye_state": "unknown", "stressed_face": False, "mouth_open": False}
                time.sleep(0.5)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                self._mouth_open_frames = 0
                self.state = {"face_present": False, "eye_state": "closed", "stressed_face": False, "mouth_open": False}
                time.sleep(0.5)
                continue

            mouth_open = False
            for (x, y, w, h) in faces:
                lower_face = gray[y + int(h * 0.6): y + h, x: x + w]
                mouths = self.mouth_cascade.detectMultiScale(
                    lower_face, scaleFactor=1.7, minNeighbors=11, minSize=(25, 15)
                )
                if len(mouths) > 0:
                    self._mouth_open_frames += 1
                else:
                    self._mouth_open_frames = max(0, self._mouth_open_frames - 1)

            mouth_open = self._mouth_open_frames >= 3

            self.state = {
                "face_present": True,
                "eye_state": "open",
                "stressed_face": False,
                "mouth_open": mouth_open,
            }
            time.sleep(0.4)

    def get_state(self):
        return dict(self.state)