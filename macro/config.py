"""Settings for the fishing macro, saved to config.json next to main.py / the exe."""

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

if getattr(sys, "frozen", False):   # built .exe: keep config beside the exe
    CONFIG_PATH = Path(sys.executable).resolve().parent / "config.json"
else:
    CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


@dataclass
class Features:
    auto_cast: bool = True       # hold click to cast the rod
    rod_check: bool = True       # only cast when the fishing rod is held
    tracking: bool = True        # follow the fish in the reel minigame
    auto_recast: bool = True     # cast again after every catch
    anti_afk: bool = False       # tap a key now and then so you are not kicked
    always_on_top: bool = True   # keep this window above Roblox


@dataclass
class Config:
    features: Features = field(default_factory=Features)

    # Reel minigame bar on screen: [left, top, width, height]
    bar_region: list | None = None
    # Colour of the fish / target marker inside the bar (RGB)
    fish_color: list = field(default_factory=lambda: [255, 255, 255])
    # Colour of the bar you control (RGB)
    bar_color: list = field(default_factory=lambda: [85, 170, 255])
    color_tolerance: int = 25

    # A pixel that only has this colour while the rod is held,
    # e.g. the highlighted hotbar slot of the rod: {"x", "y", "color"}
    rod_pixel: dict | None = None
    rod_tolerance: int = 20

    cast_hold: float = 0.6        # seconds to hold click when casting
    bite_timeout: float = 30.0    # recast if no minigame shows up in this time
    recast_delay: float = 2.0     # wait after a catch before casting again
    lost_frames: int = 15         # frames without the bar = minigame over

    deadzone: int = 4             # px the fish can be off centre before reacting
    lookahead: float = 0.08       # seconds of bar velocity to predict ahead
    min_pixels: int = 3           # pixels needed to count a colour as found

    anti_afk_key: str = "space"
    anti_afk_every: float = 300.0

    start_key: str = "f1"
    stop_key: str = "f2"

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        feats = Features(**{k: v for k, v in data.pop("features", {}).items()
                            if k in Features.__dataclass_fields__})
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(features=feats, **known)

    def save(self, path: Path = CONFIG_PATH) -> None:
        path.write_text(json.dumps(asdict(self), indent=2))
