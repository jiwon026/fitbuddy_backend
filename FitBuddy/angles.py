import numpy as np

def angle_abc(a, b, c, eps=1e-6):
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cos_val = np.clip(np.dot(ba, bc) / ((np.linalg.norm(ba)*np.linalg.norm(bc))+eps), -1, 1)
    return np.degrees(np.arccos(cos_val))

RIGHT = {'hip': 24, 'knee': 26, 'ankle': 28, 'shoulder': 12, 'ear': 8}
LEFT = {'hip': 23, 'knee': 25, 'ankle': 27, 'shoulder': 11, 'ear': 7}

def extract_angles(kpts, side='right', w=1, h=1):
    idx = RIGHT if side == 'right' else LEFT
    def xy(i): return np.array([kpts[i,0]*w, kpts[i,1]*h])
    hip, knee, ankle = xy(idx['hip']), xy(idx['knee']), xy(idx['ankle'])
    shoulder, ear = xy(idx['shoulder']), xy(idx['ear'])

    knee_angle = angle_abc(hip, knee, ankle)
    hip_angle = angle_abc(shoulder, hip, knee)
    torso_tilt = np.degrees(np.arctan2(abs(hip[1]-shoulder[1]), abs(hip[0]-shoulder[0])+1e-6))
    return {'knee': float(knee_angle), 'hip': float(hip_angle), 'torso_tilt': float(torso_tilt)}
