import math

import numpy as np

from macro.config import Config
from macro.engine import FishingEngine
from macro.tracker import Tracker
from macro.vision import color_matches, find_x

FISH = [255, 255, 255]
BAR = [85, 170, 255]
BG = [20, 30, 40]
W, H = 300, 10


def frame(fish_x=None, bar_x=None, bar_w=40):
    img = np.full((H, W, 3), BG, dtype=np.uint8)
    if bar_x is not None:
        lo, hi = int(bar_x - bar_w / 2), int(bar_x + bar_w / 2)
        img[:, max(lo, 0):max(hi, 0)] = BAR
    if fish_x is not None:
        img[2:8, int(fish_x) - 2:int(fish_x) + 2] = FISH
    return img


def test_find_x_locates_colours():
    img = frame(fish_x=200, bar_x=100)
    assert abs(find_x(img, FISH, 10) - 199.5) < 1
    # fish pixels overwrite nothing inside the bar here, so the bar centre is exact
    assert abs(find_x(img, BAR, 10) - 99.5) < 1
    assert find_x(frame(), BAR, 10) is None


def test_color_matches_tolerance():
    assert color_matches((100, 100, 100), [110, 95, 100], 10)
    assert not color_matches((100, 100, 100), [120, 100, 100], 10)


def test_tracker_holds_when_fish_is_right():
    t = Tracker(deadzone=4, lookahead=0)
    assert t.update(200, 100, 0.0) is True
    assert t.update(50, 100, 0.1) is False


class Sim:
    """Fake Roblox: fish wanders, holding click pushes the bar right."""

    def __init__(self, bite_after=0.2, duration=4.0):
        self.t = 0.0
        self.down = False
        self.bar_x, self.bar_v = 150.0, 0.0
        self.bite_after, self.duration = bite_after, duration
        self.cast_holds = 0
        self.inside = self.frames = 0
        self.rod = (0, 200, 0)

    # clock / sleep
    def clock(self):
        return self.t

    def sleep(self, dt):
        dt = max(dt, 0.005)
        steps = max(1, int(dt / 0.005))
        for _ in range(steps):
            self._step(dt / steps)

    def _step(self, dt):
        self.t += dt
        if self.active():
            acc = 900 if self.down else -900
            self.bar_v = max(-400, min(400, self.bar_v + acc * dt))
            self.bar_x += self.bar_v * dt
            if not 20 <= self.bar_x <= W - 20:
                self.bar_x = min(max(self.bar_x, 20), W - 20)
                self.bar_v = 0

    def fish_x(self):
        return 150 + 90 * math.sin(self.t * 1.3)

    def active(self):
        return self.bite_after <= self.t < self.bite_after + self.duration

    # screen
    def grab(self, region):
        if not self.active():
            return frame()
        if self.t > self.bite_after + 1.0:   # after the bar catches up
            self.frames += 1
            self.inside += abs(self.fish_x() - self.bar_x) < 20
        return frame(self.fish_x(), self.bar_x)

    def pixel(self, x, y):
        return self.rod

    # inputs
    def mouse_down(self):
        if not self.active() and not self.down:
            self.cast_holds += 1
        self.down = True

    def mouse_up(self):
        self.down = False

    def tap(self, key):
        pass


def make(sim, **kw):
    cfg = Config(bar_region=[0, 0, W, H], fish_color=FISH, bar_color=BAR,
                 rod_pixel={"x": 1, "y": 1, "color": [0, 200, 0]},
                 recast_delay=0, **kw)
    cfg.features.auto_recast = False
    return FishingEngine(cfg, sim, sim, on_status=lambda s: None,
                         clock=sim.clock, sleep=sim.sleep)


def test_cycle_casts_then_tracks_fish():
    sim = Sim()
    eng = make(sim)
    eng.run()
    assert sim.cast_holds == 1
    assert eng.catches == 1
    assert sim.frames > 200
    assert sim.inside / sim.frames > 0.95, sim.inside / sim.frames
    assert sim.down is False


def test_no_cast_without_rod():
    sim = Sim()
    sim.rod = (50, 50, 50)
    eng = make(sim)
    eng.pause = lambda s: (eng.stop_event.set(), False)[1]
    eng.run()
    assert sim.cast_holds == 0


def test_recasts_after_bite_timeout():
    sim = Sim(bite_after=999)
    eng = make(sim, bite_timeout=1.0)
    eng.cycle()
    assert sim.cast_holds == 1 and eng.catches == 0
