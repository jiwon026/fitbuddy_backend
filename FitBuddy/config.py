# config.py
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RAW = DATA / "raw_kpt"          # 프레임별 키포인트/각도 CSV
REPS = DATA / "reps_agg"        # rep 요약 피처
LABELED = DATA / "labeled"      # 정자세/오자세 라벨링된 이미지에서 추출한 피처
MODELS = ROOT / "models"

CATEGORIES = {
    "full_body": ["plank", "burpee", "mountain_climber"],
    "upper_body": ["pushup", "pullup", "kickback"],
    "lower_body": ["squat", "lunge", "deadlift"],
    "core": ["crunch", "leg_raise", "russian_twist"],
}
EXERCISES = {ex: cat for cat, lst in CATEGORIES.items() for ex in lst}

FPS = 15
THRESH = {
    "squat": {"down_knee": 95, "up_knee": 160},
    "pushup": {"min_elbow": 75},
}
