import math


class Animation:
    def get_colors(self, i: float) -> [int, int, int, int]:
        raise NotImplementedError


class BtConnectingAnimation(Animation):
    def __init__(self):
        super(BtConnectingAnimation, self).__init__()
        self.phase = [.0 * math.pi, .5 * math.pi, 1. * math.pi, 1.5 * math.pi]

    def get_colors(self, i):
        colors = []
        for i in range(4):
            colors.append(math.floor((math.sin(self.phase[i]) + 1.) * .5 * 255))
            self.phase[i] += .05

        return colors