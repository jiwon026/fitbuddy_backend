# recorder.py
import csv, time
from pathlib import Path
import cv2
from pose_detector import PoseDetector
from angles import extract_angles
from utils import EMA
from config import RAW, FPS

def record_session(exercise, subject="U000", view="side"):
    out_dir = RAW / exercise / subject
    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    pose = PoseDetector()
    ema = EMA(0.25)
    t0 = time.time()
    idx = 0
    csv_path = out_dir / f"S{int(t0)}_{view}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        cols = ["t","frame","knee","hip","torso_tilt"]  # 필요시 확장
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        while True:
            ok, frame = cap.read()
            if not ok: break
            h, wid = frame.shape[:2]
            lm = pose.process(frame)
            if lm is not None:
                kpts = pose.to_numpy()
                if kpts is not None:
                    ang = extract_angles(kpts, w=wid, h=h)
                    ang["knee"] = float(ema(ang["knee"]))
                    w.writerow({"t":time.time(), "frame":idx, **ang})
            cv2.imshow("REC - q to stop", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            idx += 1
    cap.release(); cv2.destroyAllWindows()
    print("saved:", csv_path)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--exercise", required=True)
    ap.add_argument("--subject", default="U000")
    ap.add_argument("--view", default="side")
    args = ap.parse_args()
    record_session(args.exercise, args.subject, args.view)
