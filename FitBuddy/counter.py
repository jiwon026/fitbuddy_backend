class SquatCounter:
    def __init__(self, down_knee_thresh=95, up_knee_thresh=160, min_depth_frames=3):
        self.state = 'up'
        self.count = 0
        self.depth_frames = 0
        self.down_knee_thresh = down_knee_thresh
        self.up_knee_thresh = up_knee_thresh
        self.min_depth_frames = min_depth_frames

    def update(self, knee_angle):
        if self.state == 'up':
            if knee_angle < self.down_knee_thresh:
                self.depth_frames += 1
                if self.depth_frames >= self.min_depth_frames:
                    self.state = 'down'
            else:
                self.depth_frames = 0
        elif self.state == 'down':
            if knee_angle > self.up_knee_thresh:
                self.count += 1
                self.state = 'up'
                self.depth_frames = 0
        return self.count, self.state
