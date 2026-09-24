"""JUXK PS2 window: six toggles, Calibrate and Start Fish."""

import queue
import tkinter as tk

from .config import Config
from .engine import FishingEngine
from .platform_io import Inputs, Screen, listen_hotkeys

BG = "#15171c"
CARD = "#1f232b"
GOLD = "#f5c542"
TEXT = "#e8e8e8"
MUTED = "#8a93a3"
GREEN = "#3ecf6e"
RED = "#e05555"

TOGGLES = [
    ("auto_cast", "Auto Cast"),
    ("rod_check", "Rod Check"),
    ("tracking", "Tracking System"),
    ("auto_recast", "Auto Re-Cast"),
    ("anti_afk", "Anti-AFK"),
    ("always_on_top", "Always On Top"),
]


def hex_color(rgb):
    return "#%02x%02x%02x" % tuple(rgb[:3])


class App:
    def __init__(self):
        self.cfg = Config.load()
        self.screen = Screen()
        self.inputs = Inputs()
        self.events = queue.Queue()
        self.engine = None

        self.root = tk.Tk()
        self.root.title("JUXK PS2")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self._build()
        self._apply_on_top()
        listen_hotkeys(self.cfg.start_key, self.cfg.stop_key,
                       lambda: self.events.put(("start", None)),
                       lambda: self.events.put(("stop", None)))
        self.root.after(100, self._poll)

    # ---- layout ----------------------------------------------------------
    def _build(self):
        card = tk.Frame(self.root, bg=CARD, padx=22, pady=18,
                        highlightbackground=GOLD, highlightthickness=2)
        card.pack(padx=14, pady=14)

        head = tk.Frame(card, bg=CARD)
        head.pack(fill="x")
        tk.Label(head, text="$", fg=GOLD, bg=CARD,
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(head, text="JUXK PS2", fg=TEXT, bg=CARD, padx=28, pady=4,
                 font=("Segoe UI", 18, "bold"), relief="solid", bd=2,
                 highlightbackground=TEXT).pack(side="left", padx=10, expand=True)
        tk.Label(head, text="$", fg=GOLD, bg=CARD,
                 font=("Segoe UI", 22, "bold")).pack(side="right")

        grid = tk.Frame(card, bg=CARD, pady=14)
        grid.pack()
        self.vars = {}
        for i, (key, label) in enumerate(TOGGLES):
            var = tk.BooleanVar(value=getattr(self.cfg.features, key))
            var.trace_add("write", lambda *_, k=key: self._toggle(k))
            self.vars[key] = var
            tk.Checkbutton(grid, text=label, variable=var, fg=TEXT, bg=CARD,
                           selectcolor=BG, activebackground=CARD,
                           activeforeground=TEXT, font=("Segoe UI", 11),
                           anchor="w", width=16
                           ).grid(row=i // 2, column=i % 2, sticky="w", padx=6, pady=3)

        tk.Button(card, text="Calibrate", command=self.open_calibrate,
                  bg=BG, fg=MUTED, relief="flat", font=("Segoe UI", 9),
                  activebackground=CARD).pack(pady=(0, 8))

        self.start_btn = tk.Button(card, text="Start Fish", command=self.toggle_run,
                                   bg=GREEN, fg="black", relief="flat", width=18,
                                   font=("Segoe UI", 14, "bold"))
        self.start_btn.pack()

        self.status = tk.Label(card, text=f"{self.cfg.start_key.upper()} start · "
                                          f"{self.cfg.stop_key.upper()} stop",
                               fg=MUTED, bg=CARD, font=("Segoe UI", 9))
        self.status.pack(pady=(10, 0))

    def _toggle(self, key):
        setattr(self.cfg.features, key, self.vars[key].get())
        self.cfg.save()
        if key == "always_on_top":
            self._apply_on_top()

    def _apply_on_top(self):
        self.root.attributes("-topmost", self.cfg.features.always_on_top)

    # ---- run / stop ------------------------------------------------------
    def toggle_run(self):
        if self.engine and self.engine.running:
            self.stop()
        else:
            self.start()

    def start(self):
        if self.engine and self.engine.running:
            return
        self.cfg.save()
        self.engine = FishingEngine(self.cfg, self.screen, self.inputs,
                                    on_status=lambda s: self.events.put(("status", s)))
        self.engine.start()
        self.start_btn.config(text="Stop Fish", bg=RED)

    def stop(self):
        if self.engine:
            self.engine.stop()

    def _poll(self):
        while not self.events.empty():
            kind, val = self.events.get()
            if kind == "start":
                self.start()
            elif kind == "stop":
                self.stop()
            elif kind == "status":
                self.status.config(text=val)
        if not (self.engine and self.engine.running):
            self.start_btn.config(text="Start Fish", bg=GREEN)
        self.root.after(100, self._poll)

    def quit(self):
        self.stop()
        self.inputs.mouse_up()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

    # ---- calibration -----------------------------------------------------
    def open_calibrate(self):
        CalibrateWindow(self)


class CalibrateWindow:
    def __init__(self, app: App):
        self.app = app
        self.cfg = app.cfg
        self.win = tk.Toplevel(app.root, bg=CARD, padx=16, pady=14)
        self.win.title("Calibrate")
        self.win.attributes("-topmost", True)

        tk.Label(self.win, text="Start a fish in Roblox so the reel bar is visible,\n"
                                "then set each item below.",
                 fg=MUTED, bg=CARD, justify="left").grid(row=0, columnspan=3, sticky="w")

        self.region_lbl = self._row(1, "Reel bar region", "Select", self.select_region)
        self.fish_sw = self._row(2, "Fish colour", "Pick (3s)",
                                 lambda: self.pick("fish_color"))
        self.bar_sw = self._row(3, "Your bar colour", "Pick (3s)",
                                lambda: self.pick("bar_color"))
        self.rod_sw = self._row(4, "Rod-held pixel", "Pick (3s)",
                                lambda: self.pick("rod_pixel"))

        self.tol = self._entry(5, "Colour tolerance", self.cfg.color_tolerance)
        self.hold = self._entry(6, "Cast hold (s)", self.cfg.cast_hold)
        self.timeout = self._entry(7, "Bite timeout (s)", self.cfg.bite_timeout)

        tk.Button(self.win, text="Save", command=self.save, bg=GREEN,
                  relief="flat", width=12).grid(row=8, columnspan=3, pady=(12, 0))
        self.refresh()

    def _row(self, r, text, btn, cmd):
        tk.Label(self.win, text=text, fg=TEXT, bg=CARD).grid(row=r, column=0, sticky="w", pady=4)
        info = tk.Label(self.win, text="not set", fg=MUTED, bg=CARD, width=16)
        info.grid(row=r, column=1, padx=8)
        tk.Button(self.win, text=btn, command=cmd, relief="flat").grid(row=r, column=2)
        return info

    def _entry(self, r, text, value):
        tk.Label(self.win, text=text, fg=TEXT, bg=CARD).grid(row=r, column=0, sticky="w", pady=4)
        e = tk.Entry(self.win, width=8)
        e.insert(0, str(value))
        e.grid(row=r, column=1, sticky="w", padx=8)
        return e

    def refresh(self):
        c = self.cfg
        self.region_lbl.config(text=str(c.bar_region) if c.bar_region else "not set")
        self.fish_sw.config(text=str(c.fish_color), bg=hex_color(c.fish_color))
        self.bar_sw.config(text=str(c.bar_color), bg=hex_color(c.bar_color))
        if c.rod_pixel:
            self.rod_sw.config(text=f"({c.rod_pixel['x']},{c.rod_pixel['y']})",
                               bg=hex_color(c.rod_pixel["color"]))

    def pick(self, what, left=3):
        """Hover the mouse over the thing, it is sampled after a countdown."""
        if left > 0:
            self.app.status.config(text=f"Hover over it... {left}")
            self.win.after(1000, lambda: self.pick(what, left - 1))
            return
        x, y = self.app.inputs.cursor()
        color = list(self.app.screen.pixel(x, y))
        if what == "rod_pixel":
            self.cfg.rod_pixel = {"x": x, "y": y, "color": color}
        else:
            setattr(self.cfg, what, color)
        self.app.status.config(text=f"Picked {color} at ({x},{y})")
        self.cfg.save()
        self.refresh()

    def select_region(self):
        RegionSelector(self.app.root, self._set_region)

    def _set_region(self, region):
        self.cfg.bar_region = region
        self.cfg.save()
        self.refresh()

    def save(self):
        try:
            self.cfg.color_tolerance = int(self.tol.get())
            self.cfg.cast_hold = float(self.hold.get())
            self.cfg.bite_timeout = float(self.timeout.get())
        except ValueError:
            self.app.status.config(text="Numbers only in the boxes")
            return
        self.cfg.save()
        self.win.destroy()


class RegionSelector:
    """Full-screen dim overlay; drag a box around the reel bar."""

    def __init__(self, root, on_done):
        self.on_done = on_done
        self.top = tk.Toplevel(root)
        self.top.attributes("-fullscreen", True)
        self.top.attributes("-alpha", 0.3)
        self.top.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.top, bg="black", cursor="cross",
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(self.top.winfo_screenwidth() // 2, 40, fill="white",
                                font=("Segoe UI", 16, "bold"),
                                text="Drag a box around the reel bar  (Esc to cancel)")
        self.start = None
        self.rect = None
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.top.bind("<Escape>", lambda _: self.top.destroy())
        self.top.focus_force()

    def _press(self, e):
        self.start = (e.x_root, e.y_root)
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x, e.y,
                                                 outline=GOLD, width=3)

    def _drag(self, e):
        if self.rect:
            x0 = self.start[0] - self.top.winfo_rootx()
            y0 = self.start[1] - self.top.winfo_rooty()
            self.canvas.coords(self.rect, x0, y0, e.x, e.y)

    def _release(self, e):
        if not self.start:
            return
        x0, y0 = self.start
        left, top = min(x0, e.x_root), min(y0, e.y_root)
        w, h = abs(e.x_root - x0), abs(e.y_root - y0)
        self.top.destroy()
        if w > 5 and h > 2:
            self.on_done([left, top, w, h])
