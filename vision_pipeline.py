import threading, time
import cv2

class VisionPipeline:
    def __init__(self):
        # Use built‑in Haar cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.cap = cv2.VideoCapture(0)
        self.state = {"face_present": False, "eye_state": "unknown"}
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while True:
            ok, frame = self.cap.read()
            if not ok:
                self.state = {"face_present": False, "eye_state": "unknown"}
                time.sleep(0.5)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                self.state = {"face_present": False, "eye_state": "closed"}
            else:
                # Simple heuristic: if face present, assume eyes open
                self.state = {"face_present": True, "eye_state": "open"}

            time.sleep(0.5)

    def get_state(self):
        return dict(self.state)

if __name__ == "__main__":
    v = VisionPipeline()
    print("Testing vision…")
    for _ in range(10):
        print(v.get_state())
        time.sleep(1)
