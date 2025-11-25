# smart_counter.py
# 모델 기반 스마트 카운터 - 정자세일 때만 카운트
import numpy as np
import joblib
from pathlib import Path
from config import MODELS

class SmartSquatCounter:
    def __init__(self, exercise="squat", model_path=None, down_knee_thresh=95, up_knee_thresh=160, min_depth_frames=3, min_good_prob=0.5):
        """
        모델 기반 스마트 카운터
        
        Args:
            exercise: 운동 이름
            model_path: 모델 파일 경로 (None이면 자동으로 찾음)
            down_knee_thresh: 하강 임계값 (무릎 각도)
            up_knee_thresh: 상승 임계값 (무릎 각도)
            min_depth_frames: 최소 깊이 유지 프레임 수
            min_good_prob: 정자세로 인정할 최소 확률 (0~1)
        """
        self.state = 'up'
        self.count = 0
        self.depth_frames = 0
        self.down_knee_thresh = down_knee_thresh
        self.up_knee_thresh = up_knee_thresh
        self.min_depth_frames = min_depth_frames
        self.min_good_prob = min_good_prob
        
        # 모델 로드
        self.model = None
        if model_path is None:
            model_path = MODELS / f"{exercise}_from_images.pkl"
        
        if Path(model_path).exists():
            try:
                self.model = joblib.load(model_path)
                print(f"Loaded model from {model_path}")
            except Exception as e:
                print(f"Warning: Could not load model: {e}")
                print("Falling back to rule-based counter")
        else:
            print(f"Warning: Model not found at {model_path}")
            print("Falling back to rule-based counter")
    
    def predict_posture(self, knee, hip, tilt):
        """현재 자세가 정자세인지 예측"""
        if self.model is None:
            # 모델이 없으면 규칙 기반으로 판단
            return 1.0  # 항상 정자세로 간주 (기본 카운터 동작)
        
        try:
            # 모델에 맞는 피처 형식으로 변환
            X = np.array([[knee, hip, tilt]], dtype=float)
            
            if hasattr(self.model, "predict_proba"):
                prob_good = self.model.predict_proba(X)[0, 1]  # 정자세 확률
            else:
                pred = self.model.predict(X)[0]
                prob_good = float(pred)
            
            return float(prob_good)
        except Exception as e:
            print(f"Error in prediction: {e}")
            return 1.0  # 에러 시 정자세로 간주
    
    def update(self, knee, hip=None, tilt=None):
        """
        카운터 업데이트
        
        Args:
            knee: 무릎 각도
            hip: 고관절 각도 (선택, 모델 사용 시 필요)
            tilt: 상체 기울기 (선택, 모델 사용 시 필요)
        
        Returns:
            (count, state, is_good_posture): (카운트, 상태, 정자세 여부)
        """
        is_good_posture = True
        
        # 모델이 있으면 자세 평가
        if self.model is not None and hip is not None and tilt is not None:
            prob_good = self.predict_posture(knee, hip, tilt)
            is_good_posture = prob_good >= self.min_good_prob
        
        if self.state == 'up':
            if knee < self.down_knee_thresh:
                self.depth_frames += 1
                if self.depth_frames >= self.min_depth_frames:
                    self.state = 'down'
            else:
                self.depth_frames = 0
        elif self.state == 'down':
            if knee > self.up_knee_thresh:
                # 정자세일 때만 카운트
                if is_good_posture:
                    self.count += 1
                self.state = 'up'
                self.depth_frames = 0
        
        return self.count, self.state, is_good_posture

