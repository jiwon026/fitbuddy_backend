# score_live.py
# 실시간으로 프레임 → rep(1회 동작) 감지 → 피처 요약 → 모델 점수/피드백 출력
# 사용법:
#   python score_live.py --exercise squat --model models/squat_rf.pkl
#   (모델 파일 없이 실행하면 피처만 콘솔로 출력)

import argparse, time, csv, os
from pathlib import Path
import numpy as np
import joblib

import cv2
from pose_detector import PoseDetector
from angles import extract_angles
from utils import EMA, RingBuffer
from counter import SquatCounter  # rep 경계 감지에 사용(스쿼트 기준)

# ---- 피처 요약 (rep 종료 시 계산) ----
def summarize_rep(rep_buf):
    # rep_buf: [{'t':..,'knee':..,'hip':..,'torso_tilt':..}, ...]
    if not rep_buf:
        return {}
    ks  = np.array([r['knee'] for r in rep_buf], dtype=float)
    hs  = np.array([r['hip'] for r in rep_buf], dtype=float)
    ts  = np.array([r['torso_tilt'] for r in rep_buf], dtype=float)
    ts_sec = np.array([r['t'] for r in rep_buf], dtype=float)
    duration = float(ts_sec[-1] - ts_sec[0]) if len(ts_sec) > 1 else 0.0

    out = {
        "frames"   : int(len(rep_buf)),
        "knee_min" : float(np.nanmin(ks)),
        "knee_max" : float(np.nanmax(ks)),
        "knee_rom" : float(np.nanmax(ks) - np.nanmin(ks)),
        "hip_min"  : float(np.nanmin(hs)),
        "tilt_max" : float(np.nanmax(ts)),
        "pct_deep" : float(np.mean(ks < 95.0)),  # 무릎 각도 95° 미만 비율
        "duration" : duration,
    }
    return out

# ---- 피드백 문구 합성 ----
def feedback_from_features(feat, prob_good=None):
    msgs = []
    # 규칙 기반 기본 피드백
    if feat.get("pct_deep", 0) < 0.4:
        msgs.append("깊이가 부족해요(무릎 각도 <95° 구간이 적음)")
    if feat.get("tilt_max", 0) > 55:
        msgs.append("상체가 많이 숙여졌어요")
    if feat.get("knee_rom", 0) < 30:
        msgs.append("가동 범위(ROM)가 작아요")
    if feat.get("duration", 0) < 0.6:
        msgs.append("템포가 너무 빨라요")

    if prob_good is not None:
        score_txt = f"모델 점수(정석 확률): {prob_good*100:.1f}%"
        if not msgs:
            msgs.append("좋아요! 안정적인 자세예요")
        msgs.append(score_txt)
    elif not msgs:
        msgs.append("좋아요! 안정적인 자세예요")

    return " / ".join(msgs)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exercise", required=True, help="squat/lunge/deadlift/pushup/... (현재 스쿼트 로직 기반)")
    ap.add_argument("--model", default=None, help="학습 모델(pkl) 경로 (옵션)")
    ap.add_argument("--save_csv", action="store_true", help="rep 요약 피처를 CSV로 저장")
    args = ap.parse_args()

    model = None
    if args.model and Path(args.model).exists():
        model = joblib.load(args.model)

    # 카메라/모듈 초기화
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    pose = PoseDetector(model_complexity=1)
    ema = EMA(alpha=0.25)
    rb = RingBuffer(size=5)
    counter = SquatCounter()  # 스쿼트 기준의 up/down 상태머신으로 rep 경계 검출

    # rep 버퍼
    rep_buf = []      # 현재 rep에 속하는 프레임 피처들
    last_state = "up" # 상태 전이 감지용
    rep_idx = 0

    # CSV 저장 설정
    csv_writer = None
    if args.save_csv:
        os.makedirs("data/reps_live", exist_ok=True)
        csv_path = f"data/reps_live/{args.exercise}_live_{int(time.time())}.csv"
        f = open(csv_path, "w", newline="", encoding="utf-8")
        csv_writer = csv.DictWriter(f, fieldnames=[
            "rep_id","frames","knee_min","knee_max","knee_rom","hip_min","tilt_max","pct_deep","duration","prob_good"
        ])
        csv_writer.writeheader()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        h, w = frame.shape[:2]

        lms = pose.process(frame)
        if lms is not None:
            kpts = pose.to_numpy()
            if kpts is not None:
                ang = extract_angles(kpts, side='right', w=w, h=h)

                knee_s = ema(ang['knee'])
                rb.push(knee_s)
                knee = float(rb.mean())
                # NaN 체크 (버퍼가 비어있을 때)
                if np.isnan(knee):
                    knee = float(knee_s)  # EMA 값 사용
                hip = float(ang['hip'])
                tilt = float(ang['torso_tilt'])

                # 현재 프레임 피처(실시간 표시용)
                cv2.putText(frame, f"knee:{knee:.1f} hip:{hip:.1f} tilt:{tilt:.1f}", (20, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

                # rep 경계 감지
                count, state = counter.update(knee)

                # 상태가 down으로 들어간 동안 프레임 누적
                rep_buf.append({"t": time.time(), "knee": knee, "hip": hip, "torso_tilt": tilt})

                # up으로 전환될 때(한 rep 종료) → 요약/점수/피드백
                if last_state == "down" and state == "up":
                    rep_idx += 1
                    feat = summarize_rep(rep_buf)
                    prob_good = None

                    if model is not None and feat:
                        # 학습 스크립트(train_baseline.py)와 동일한 피처 집합 사용
                        cols = ["knee_min","knee_rom","hip_min","tilt_max","duration"]
                        x = np.array([[feat.get(c, 0.0) for c in cols]], dtype=float)
                        try:
                            if hasattr(model, "predict_proba"):
                                prob_good = float(model.predict_proba(x)[0, 1])
                            else:
                                # 일부 모델은 decision_function만 제공
                                pred = model.predict(x)[0]
                                prob_good = float(pred)
                        except Exception:
                            prob_good = None

                    msg = feedback_from_features(feat, prob_good)
                    cv2.putText(frame, f"REP {rep_idx}: {msg}", (20, 130),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,200,255), 2)

                    if csv_writer is not None:
                        row = {**{"rep_id": rep_idx}, **feat, "prob_good": (None if prob_good is None else float(prob_good))}
                        csv_writer.writerow(row)

                    # 다음 rep을 위해 버퍼 비우기
                    rep_buf = []

                last_state = state

                # 카운트/상태 표시
                cv2.putText(frame, f"COUNT: {count}  STATE:{state}", (20, 55),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)

        cv2.imshow("FitBuddy - Live Scoring (q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if csv_writer is not None:
        f.close()
        print("rep summaries saved.")

if __name__ == "__main__":
    main()
