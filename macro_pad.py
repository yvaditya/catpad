"""CatPad — frameless Apple-style macro pad (pywebview + WebView2 shell)
driving the running 3DEXPERIENCE session. Add a macro to MACROS and, if it
needs a new icon, an entry in ICONS inside ui/index.html. A macro with an
"options" list gets a chooser sheet and its run() takes (log, option_key)."""
import ctypes
import json
import sys
import threading
import time
from pathlib import Path

import webview

from catia_pad import __author__, __version__
from catia_pad.macros import (camera_lens, color_bodies, color_hierarchy,
                              reset_colors, std_views)

MACROS = [
    {
        "key": "color_hierarchy",
        "icon": "palette",
        "label": "Color by<br>Hierarchy",
        "tip": ("Color everything under your CATIA selection with muted hues "
                "that follow the tree: distinct per component, tone-varied "
                "within a geoset. Lightweight components are loaded first."),
        "fn": color_hierarchy.run,
    },
    {
        "key": "color_bodies",
        "icon": "swatch",
        "label": "Color<br>Bodies",
        "tip": ("A clearly different flat color for every body/geoset "
                "across all visible parts — muted, well spread, never "
                "going inside geosets."),
        "fn": color_bodies.run,
    },
    {
        "key": "reset_colors",
        "icon": "reset",
        "label": "Reset<br>Colors",
        "tip": ("Give every visible item its inherited color back — undoes "
                "what the color cards (or anyone else) painted. Hidden "
                "items are left alone."),
        "fn": reset_colors.run,
    },
    {
        "key": "camera_lens",
        "icon": "camera",
        "label": "Camera<br>Lens",
        "tip": ("Pick a lens for the 3D view: orthographic, or 50 / 35 / 24 "
                "/ 16 mm full-frame perspective equivalents."),
        "fn": camera_lens.run,
        "options": camera_lens.OPTIONS,
        "sheet_title": "Lens for this view",
    },
    {
        "key": "std_views",
        "icon": "cube",
        "label": "Std<br>Views",
        "tip": ("Snap the 3D view to a standard orientation — front, top, "
                "side… — or square onto the selected planar face."),
        "fn": std_views.run,
        "options": std_views.OPTIONS,
        "sheet_title": "Point the camera",
    },
]

TOTAL_SLOTS = 8
WIDTH, HEIGHT = 210, 402


class _AccentPolicy(ctypes.Structure):
    _fields_ = [("AccentState", ctypes.c_int),
                ("AccentFlags", ctypes.c_int),
                ("GradientColor", ctypes.c_uint),
                ("AnimationId", ctypes.c_int)]


class _CompositionData(ctypes.Structure):
    _fields_ = [("Attrib", ctypes.c_int),
                ("pvData", ctypes.c_void_p),
                ("cbData", ctypes.c_size_t)]


def _dress_window(title):
    """Rounded corners, blur behind the transparent panel, and the 🐈
    taskbar icon. Best-effort — silently skipped on systems that refuse
    any given step."""
    try:
        user32 = ctypes.windll.user32
        hwnd = 0
        for _ in range(50):
            hwnd = user32.FindWindowW(None, title)
            if hwnd:
                break
            time.sleep(0.1)
        if not hwnd:
            return
        pref = ctypes.c_int(2)  # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(pref), 4)
        accent = _AccentPolicy()
        accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
        data = _CompositionData(19,  # WCA_ACCENT_POLICY
                                ctypes.addressof(accent),
                                ctypes.sizeof(accent))
        user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
        icon = _asset_path("catpad.ico")
        if icon.exists():
            hicon = user32.LoadImageW(
                None, str(icon), 1, 0, 0, 0x10)  # IMAGE_ICON, LOADFROMFILE
            if hicon:
                for which in (0, 1):  # ICON_SMALL, ICON_BIG
                    user32.SendMessageW(hwnd, 0x80, which, hicon)
    except Exception:
        pass


def _ui_path():
    """ui/index.html next to the source, or bundled inside the frozen app."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "ui" / "index.html"


def _asset_path(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "assets" / name


class Api:
    """Bridge exposed to the page as window.pywebview.api."""

    def __init__(self):
        self._window = None  # private: pywebview must not expose/serialize it
        self._busy = False

    def get_meta(self):
        return {
            "version": __version__,
            "author": __author__,
            "slots": TOTAL_SLOTS,
            "macros": [{k: m.get(k) for k in
                        ("key", "icon", "label", "tip", "options",
                         "sheet_title")}
                       for m in MACROS],
        }

    def _push(self, js):
        try:
            self._window.evaluate_js(js)
        except Exception:
            pass

    def set_status(self, text):
        self._push(f"CatPad.setStatus({json.dumps(text)})")

    def run_macro(self, key, option=None):
        macro = next((m for m in MACROS if m["key"] == key), None)
        if macro is None or self._busy:
            return
        self._busy = True
        self._push("CatPad.setBusy(true)")
        try:
            if macro.get("options"):
                result = macro["fn"](self.set_status, option)
            else:
                result = macro["fn"](self.set_status)
        except Exception as exc:
            result = f"Error: {exc}"
        finally:
            self._busy = False
            self._push("CatPad.setBusy(false)")
        self.set_status(result)

    def minimize(self):
        self._window.minimize()

    def close(self):
        self._window.destroy()


def main():
    api = Api()
    # geometry is in logical units — pywebview applies DPI scaling itself,
    # so no manual scale math here (doing it double-scales x off-screen)
    try:
        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
        x = max(screen_w - WIDTH - 40, 0)
    except Exception:
        x = 100
    api._window = webview.create_window(
        "CatPad", _ui_path().as_uri(), js_api=api,
        frameless=True, on_top=True, resizable=False, transparent=True,
        width=WIDTH, height=HEIGHT, x=x, y=120,
    )
    threading.Thread(target=_dress_window, args=("CatPad",),
                     daemon=True).start()
    webview.start()


if __name__ == "__main__":
    main()
