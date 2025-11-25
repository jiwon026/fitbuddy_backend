import numpy as np
from collections import deque

class EMA:
    def __init__(self, alpha=0.2):
        self.alpha = alpha
        self.prev = None
    def __call__(self, x):
        if self.prev is None:
            self.prev = x
        self.prev = self.alpha * x + (1 - self.alpha) * self.prev
        return self.prev

class RingBuffer:
    def __init__(self, size=5):
        self.buf = deque(maxlen=size)
    def push(self, x):
        self.buf.append(x)
    def mean(self):
        return float(np.mean(self.buf)) if self.buf else np.nan
