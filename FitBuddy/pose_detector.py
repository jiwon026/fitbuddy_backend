# pose_detector.py (추가/수정)
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_styles  = mp.solutions.drawing_styles

class PoseDetector:
    def __init__(self, model_complexity=1):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.results = None   # <- 마지막 결과 저장

    def process(self, frame_bgr):
        # MediaPipe는 RGB 입력
        rgb = frame_bgr[:, :, ::-1]
        self.results = self.pose.process(rgb)
        if self.results.pose_landmarks:
            return self.results.pose_landmarks
        return None

    def to_numpy(self):
        """최근 결과를 numpy 형태 (33 x 3: x,y,visibility)로 반환"""
        if not self.results or not self.results.pose_landmarks:
            return None
        lms = self.results.pose_landmarks.landmark
        import numpy as np
        return np.array([[lm.x, lm.y, lm.visibility] for lm in lms], dtype=float)

    def draw_landmarks(self, frame_bgr, thickness=2, circle_radius=2):
        """스켈레톤(관절+연결선) 오버레이"""
        if self.results and self.results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame_bgr,
                self.results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style(),
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=thickness)
            )
