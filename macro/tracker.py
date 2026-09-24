"""Decides whether to hold the mouse so the player bar stays on the fish.

Holding click pushes the bar right, releasing lets it fall back left.
"""


class Tracker:
    def __init__(self, deadzone: float = 4, lookahead: float = 0.08):
        self.deadzone = deadzone
        self.lookahead = lookahead
        self.reset()

    def reset(self):
        self.holding = False
        self._last_bar = None
        self._last_t = None
        self.velocity = 0.0

    def update(self, fish_x: float, bar_x: float, t: float) -> bool:
        if self._last_bar is not None and t > self._last_t:
            v = (bar_x - self._last_bar) / (t - self._last_t)
            self.velocity = 0.6 * self.velocity + 0.4 * v  # smooth out jitter
        self._last_bar, self._last_t = bar_x, t

        error = fish_x - (bar_x + self.velocity * self.lookahead)
        if error > self.deadzone:
            self.holding = True
        elif error < -self.deadzone:
            self.holding = False
        else:
            # On target: counter whichever way the bar is drifting.
            self.holding = self.velocity < 0
        return self.holding
