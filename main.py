"""JUXK PS2 fishing macro for Project Slayer 2. Run: python main.py"""

import sys


def main():
    if sys.platform == "win32":
        # Real pixel coordinates on scaled (125%/150%) displays.
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()

    from macro.gui import App
    App().run()


if __name__ == "__main__":
    main()
