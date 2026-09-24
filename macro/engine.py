"""The fishing loop: check rod -> cast -> wait for bite -> track -> repeat.

Screen and input are passed in so the loop can be tested without Roblox.
  screen.grab(region) -> HxWx3 RGB array      screen.pixel(x, y) -> (r, g, b)
  inputs.mouse_down() / mouse_up() / tap(key)
"""

import threading
import time

from .tracker import Tracker
from .vision import color_matches, find_x


class FishingEngine:
    def __init__(self, cfg, screen, inputs, on_status=print,
                 clock=time.monotonic, sleep=time.sleep):
        self.cfg = cfg
        self.screen = screen
        self.inputs = inputs
        self.on_status = on_status
        self.clock = clock
        self.sleep = sleep
        self.stop_event = threading.Event()
        self.catches = 0
        self._thread = None
        self._last_afk = None

    # ---- control ---------------------------------------------------------
    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running:
            return
        self.stop_event.clear()
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        self.stop_event.set()

    def run(self):
        self._last_afk = self.clock()
        try:
            while not self.stop_event.is_set():
                if not self.cycle() or not self.cfg.features.auto_recast:
                    break
        finally:
            self.inputs.mouse_up()
            self.on_status("Stopped")

    # ---- steps -----------------------------------------------------------
    def rod_held(self) -> bool:
        rp = self.cfg.rod_pixel
        if not self.cfg.features.rod_check or not rp:
            return True
        return color_matches(self.screen.pixel(rp["x"], rp["y"]),
                             rp["color"], self.cfg.rod_tolerance)

    def read_bar(self):
        """(fish_x, bar_x) inside the minigame bar; either may be None."""
        cfg = self.cfg
        img = self.screen.grab(cfg.bar_region)
        return (find_x(img, cfg.fish_color, cfg.color_tolerance, cfg.min_pixels),
                find_x(img, cfg.bar_color, cfg.color_tolerance, cfg.min_pixels))

    def minigame_active(self) -> bool:
        return self.read_bar()[1] is not None

    def cycle(self) -> bool:
        """One cast + catch. Returns False when the loop should end."""
        cfg = self.cfg
        if cfg.features.tracking and not cfg.bar_region:
            self.on_status("Set the reel bar region in Calibrate first")
            return False

        self.anti_afk()
        if not self.wait_for_rod():
            return False

        if cfg.features.auto_cast:
            self.on_status("Casting")
            self.inputs.mouse_down()
            self.sleep(cfg.cast_hold)
            self.inputs.mouse_up()

        if cfg.features.tracking:
            self.on_status("Waiting for bite")
            if not self.wait_for_minigame():
                return not self.stop_event.is_set()   # timed out: recast
            self.track()
            self.catches += 1
            self.on_status(f"Caught! ({self.catches})")

        return self.pause(cfg.recast_delay)

    def wait_for_rod(self) -> bool:
        warned = False
        while not self.rod_held():
            if not warned:
                self.on_status("Hold your fishing rod")
                warned = True
            if not self.pause(0.25):
                return False
        return True

    def wait_for_minigame(self) -> bool:
        deadline = self.clock() + self.cfg.bite_timeout
        while self.clock() < deadline:
            if self.stop_event.is_set():
                return False
            if self.minigame_active():
                return True
            self.sleep(0.03)
        self.on_status("No bite, recasting")
        return False

    def track(self):
        self.on_status("Tracking fish")
        tracker = Tracker(self.cfg.deadzone, self.cfg.lookahead)
        missing = 0
        holding = False
        while not self.stop_event.is_set():
            fish_x, bar_x = self.read_bar()
            if bar_x is None:
                missing += 1
                if missing >= self.cfg.lost_frames:
                    break
                self.sleep(0.01)
                continue
            missing = 0
            want = tracker.update(fish_x if fish_x is not None else bar_x,
                                  bar_x, self.clock())
            if want != holding:
                (self.inputs.mouse_down if want else self.inputs.mouse_up)()
                holding = want
            self.sleep(0.005)
        self.inputs.mouse_up()

    def anti_afk(self):
        if not self.cfg.features.anti_afk:
            return
        now = self.clock()
        if now - self._last_afk >= self.cfg.anti_afk_every:
            self.inputs.tap(self.cfg.anti_afk_key)
            self._last_afk = now

    def pause(self, seconds) -> bool:
        """Sleep that wakes early on stop. False if stopped."""
        return not self.stop_event.wait(seconds)
