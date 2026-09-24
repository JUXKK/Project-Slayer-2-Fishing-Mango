"""Real screen capture (mss) and mouse/keyboard input (pynput)."""

import threading
import time

import mss
import numpy as np
from pynput import keyboard, mouse


class Screen:
    """mss handles are per-thread, so each thread gets its own."""

    def __init__(self):
        self._local = threading.local()

    @property
    def _sct(self):
        if not hasattr(self._local, "sct"):
            self._local.sct = mss.mss()
        return self._local.sct

    def grab(self, region):
        left, top, width, height = region
        shot = self._sct.grab({"left": left, "top": top,
                               "width": width, "height": height})
        return np.asarray(shot)[..., 2::-1]  # BGRA -> RGB

    def pixel(self, x, y):
        return tuple(int(c) for c in self.grab((x, y, 1, 1))[0, 0])


class Inputs:
    def __init__(self):
        self._mouse = mouse.Controller()
        self._kb = keyboard.Controller()
        self._down = False

    def mouse_down(self):
        if not self._down:
            self._mouse.press(mouse.Button.left)
            self._down = True

    def mouse_up(self):
        if self._down:
            self._mouse.release(mouse.Button.left)
            self._down = False

    def tap(self, key):
        k = getattr(keyboard.Key, key, None) or key
        self._kb.press(k)
        time.sleep(0.05)
        self._kb.release(k)

    def cursor(self):
        x, y = self._mouse.position
        return int(x), int(y)


def listen_hotkeys(start_key, stop_key, on_start, on_stop):
    """Global F1/F2 style hotkeys that work while Roblox is focused."""
    start_k = getattr(keyboard.Key, start_key, None)
    stop_k = getattr(keyboard.Key, stop_key, None)

    def on_press(key):
        if key == start_k:
            on_start()
        elif key == stop_k:
            on_stop()

    listener = keyboard.Listener(on_press=on_press, daemon=True)
    listener.start()
    return listener
