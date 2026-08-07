"""CatPad — frameless Apple-style macro pad (pywebview + WebView2 shell)
driving the running 3DEXPERIENCE session. Add a macro to MACROS and, if it
needs a new icon, an entry in ICONS inside ui/index.html. A macro with an
"options" list gets a chooser sheet; one with a "toggles" list renders as
a double-width card of side-by-side on/off segments. Either way its run()
takes (log, option_key)."""
import ctypes
import json
import sys
import threading
import time
from pathlib import Path

import webview

from catia_pad import __author__, __version__
from catia_pad.macros import camera_lens, color_bodies, toggle_visibility

MACROS = [
    {
        "key": "color_hierarchy",
        "icon": "palette",
        "label": "Color by<br>Hierarchy",
        "tip": ("Color everything under your CATIA selection with muted hues "
                "that follow the tree: distinct per component, tone-varied "
                "within a geoset. Lightweight components are loaded first."),
        "fn": color_bodies.run,
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
        "key": "toggle_visibility",
        "wide": True,
        "toggles": toggle_visibility.TOGGLES,
        "fn": toggle_visibility.run,
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
    """Rounded corners + blur behind the transparent panel. Best-effort —
    silently skipped on systems that refuse any given step."""
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
    except Exception:
        pass


def _ui_path():
    """ui/index.html next to the source, or bundled inside the frozen app."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "ui" / "index.html"


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
                         "sheet_title", "wide", "toggles")}
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
            if macro.get("options") or macro.get("toggles"):
                msg = macro["fn"](self.set_status, option)
            else:
                msg = macro["fn"](self.set_status)
        except Exception as exc:
            msg = f"Error: {exc}"
        finally:
            self._busy = False
            self._push("CatPad.setBusy(false)")
        self.set_status(msg)

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
