def squat_feedback(angles):
    msgs = []
    if angles['knee'] > 110:
        msgs.append('조금 더 깊게 앉아봐요')
    if angles['hip'] < 60:
        msgs.append('엉덩이를 더 뒤로 빼요')
    if angles['torso_tilt'] > 55:
        msgs.append('상체가 너무 숙여져 있어요')
    if not msgs:
        msgs.append('좋아요! 자세가 안정적이에요')
    return ' / '.join(msgs)
