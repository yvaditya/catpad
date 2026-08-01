"""CatPad — frameless Apple-style macro pad (pywebview + WebView2 shell)
driving the running 3DEXPERIENCE session. Add a macro to MACROS and, if it
needs a new icon, an entry in ICONS inside ui/index.html."""
import ctypes
import json
import threading
import time
from pathlib import Path

import webview

from catia_pad import __author__, __version__
from catia_pad.macros import color_bodies

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
]

TOTAL_SLOTS = 8
WIDTH, HEIGHT = 300, 574
ALPHA = 247  # ~97% opaque — just enough see-through for the glass to read


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
    """Rounded corners, slight translucency, blur-behind. Best-effort —
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
        GWL_EXSTYLE, WS_EX_LAYERED, LWA_ALPHA = -20, 0x80000, 0x2
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
        user32.SetLayeredWindowAttributes(hwnd, 0, ALPHA, LWA_ALPHA)
        accent = _AccentPolicy()
        accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
        data = _CompositionData(19,  # WCA_ACCENT_POLICY
                                ctypes.addressof(accent),
                                ctypes.sizeof(accent))
        user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
    except Exception:
        pass


class Api:
    """Bridge exposed to the page as window.pywebview.api."""

    def __init__(self):
        self.window = None
        self._busy = False

    def get_meta(self):
        return {
            "version": __version__,
            "author": __author__,
            "slots": TOTAL_SLOTS,
            "macros": [{k: m[k] for k in ("key", "icon", "label", "tip")}
                       for m in MACROS],
        }

    def _push(self, js):
        try:
            self.window.evaluate_js(js)
        except Exception:
            pass

    def set_status(self, text):
        self._push(f"CatPad.setStatus({json.dumps(text)})")

    def run_macro(self, key):
        macro = next((m for m in MACROS if m["key"] == key), None)
        if macro is None or self._busy:
            return
        self._busy = True
        self._push("CatPad.setBusy(true)")
        try:
            msg = macro["fn"](self.set_status)
        except Exception as exc:
            msg = f"Error: {exc}"
        finally:
            self._busy = False
            self._push("CatPad.setBusy(false)")
        self.set_status(msg)

    def minimize(self):
        self.window.minimize()

    def close(self):
        self.window.destroy()


def main():
    api = Api()
    ui = Path(__file__).resolve().parent / "ui" / "index.html"
    try:
        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
        x = max(screen_w - WIDTH - 40, 0)
    except Exception:
        x = 100
    api.window = webview.create_window(
        "CatPad", ui.as_uri(), js_api=api,
        frameless=True, on_top=True, resizable=False,
        width=WIDTH, height=HEIGHT, x=x, y=120,
    )
    threading.Thread(target=_dress_window, args=("CatPad",),
                     daemon=True).start()
    webview.start()


if __name__ == "__main__":
    main()
