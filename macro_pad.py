"""CatPad — frameless, Apple-styled macro pad driving the running
3DEXPERIENCE session. Add a macro by appending to MACROS."""
import ctypes
import threading
import tkinter as tk
import tkinter.font as tkfont

from catia_pad import __author__, __version__
from catia_pad.macros import color_bodies

# (icon, button label, hover tooltip, callable taking log(str))
# Append here — the grid keeps TOTAL_SLOTS positions, unfilled ones show
# as reserved "+" slots.
MACROS = [
    ("🎨", "Color by\nHierarchy",
     "Color everything under your CATIA selection with muted hues that "
     "follow the tree: distinct per component, tone-varied within a "
     "geoset. Lightweight components are loaded first.",
     color_bodies.run),
]

SLOT_TIP = "Free slot — a future macro lands here."

COLUMNS = 2
TOTAL_SLOTS = 8

BG = "#F4F4F6"
CARD = "#FCFCFE"
CARD_HOVER = "#F0F0F5"
CARD_BORDER = "#E4E4E9"
SLOT_FILL = "#EDEDF1"
TEXT = "#1D1D1F"
SUBTEXT = "#6E6E73"
FOOTER_FG = "#A5A5AA"
DISABLED = "#A8A8AD"
CLOSE_RED = "#FF5F57"
CLOSE_GLYPH = "#7E0508"
MIN_YELLOW = "#FEBC2E"
MIN_GLYPH = "#9A6B00"

CARD_W, CARD_H, RADIUS = 116, 88, 16
GLASS_ALPHA = 0.94


class _AccentPolicy(ctypes.Structure):
    _fields_ = [("AccentState", ctypes.c_int),
                ("AccentFlags", ctypes.c_int),
                ("GradientColor", ctypes.c_uint),
                ("AnimationId", ctypes.c_int)]


class _CompositionData(ctypes.Structure):
    _fields_ = [("Attrib", ctypes.c_int),
                ("pvData", ctypes.c_void_p),
                ("cbData", ctypes.c_size_t)]


def _apply_glass(root):
    """Liquid-glass backdrop: blur whatever sits behind the window and let
    a little of it show through. Safe no-op where unsupported."""
    try:
        root.attributes("-alpha", GLASS_ALPHA)
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
        accent = _AccentPolicy()
        accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
        data = _CompositionData(19,  # WCA_ACCENT_POLICY
                                ctypes.addressof(accent),
                                ctypes.sizeof(accent))
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd,
                                                           ctypes.byref(data))
    except Exception:
        pass

TIP_BG = "#3A3A3C"
TIP_FG = "#F5F5F7"
TIP_DELAY_MS = 450


class Tooltip:
    """macOS-style dark hover tooltip, shown after a short delay."""

    def __init__(self, widget, text, font):
        self.widget, self.text, self.font = widget, text, font
        self.tip = None
        self.pending = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<Button-1>", self._hide, add="+")

    def _schedule(self, _event):
        self._hide()
        self.pending = self.widget.after(TIP_DELAY_MS, self._show)

    def _show(self):
        if self.tip:
            return
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.attributes("-topmost", True)
        lbl = tk.Label(self.tip, text=self.text, bg=TIP_BG, fg=TIP_FG,
                       font=self.font, padx=9, pady=5, justify="left",
                       wraplength=220)
        lbl.pack()
        self.tip.update_idletasks()
        x = (self.widget.winfo_rootx() + self.widget.winfo_width() // 2
             - self.tip.winfo_reqwidth() // 2)
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip.geometry(f"+{max(x, 0)}+{y}")
        _apply_round_corners(self.tip)

    def _hide(self, _event=None):
        if self.pending:
            self.widget.after_cancel(self.pending)
            self.pending = None
        if self.tip:
            self.tip.destroy()
            self.tip = None


def _apply_round_corners(root):
    """Windows 11 DWM rounded corners for the frameless window."""
    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
        pref = ctypes.c_int(2)  # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(pref), 4)
    except Exception:
        pass


def _round_rect(cv, x1, y1, x2, y2, r, **kw):
    pts = (x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1)
    return cv.create_polygon(pts, smooth=True, **kw)


class Card(tk.Canvas):
    """Rounded macOS-style button card; without a command it renders as a
    reserved '+' slot for a future macro."""

    def __init__(self, master, icon, label, fonts, command=None):
        super().__init__(master, width=CARD_W, height=CARD_H, bg=BG,
                         highlightthickness=0,
                         cursor="hand2" if command else "arrow")
        self.icon, self.label = icon, label
        self.fonts, self.command = fonts, command
        self.runnable = command is not None
        self.enabled = self.runnable
        self._render(CARD if self.runnable else SLOT_FILL)
        if self.runnable:
            self.bind("<Enter>", lambda e: self.enabled and self._render(CARD_HOVER))
            self.bind("<Leave>", lambda e: self.enabled and self._render(CARD))
            self.bind("<Button-1>", self._click)

    def _render(self, fill):
        self.delete("all")
        border = CARD_BORDER if self.runnable else SLOT_FILL
        _round_rect(self, 2, 2, CARD_W - 2, CARD_H - 2, RADIUS,
                    fill=fill, outline=border)
        if self.runnable:
            # specular top edge — the "glass" catchlight
            self.create_line(2 + RADIUS, 3, CARD_W - 2 - RADIUS, 3,
                             fill="#FFFFFF")
            fg = TEXT if self.enabled else DISABLED
            self.create_text(CARD_W / 2, 31, text=self.icon,
                             font=self.fonts["icon"])
            self.create_text(CARD_W / 2, 64, text=self.label, fill=fg,
                             font=self.fonts["label"], justify="center")
        else:
            self.create_text(CARD_W / 2, CARD_H / 2, text="+",
                             font=self.fonts["plus"], fill=DISABLED)

    def _click(self, _event):
        if self.enabled and self.command:
            self.command()

    def set_enabled(self, on):
        if self.runnable:
            self.enabled = on
            self._render(CARD)


def main():
    root = tk.Tk()
    root.title("CatPad")
    root.overrideredirect(True)
    root.configure(bg=BG)
    root.attributes("-topmost", True)

    fams = set(tkfont.families())
    base = ("Segoe UI Variable Display"
            if "Segoe UI Variable Display" in fams else "Segoe UI")
    fonts = {
        "title": (base, 10, "bold"),
        "label": (base, 9),
        "status": (base, 9),
        "icon": ("Segoe UI Emoji", 18),
        "plus": (base, 16),
        "dot": (base, 7, "bold"),
    }

    status = tk.StringVar(value="Ready — select a node in CATIA, then tap a card.")

    def set_status(msg):
        root.after(0, status.set, msg)

    # ---- header: drag zone, title left, traffic-light dots top right ----
    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", padx=12, pady=(10, 2))
    title = tk.Label(header, text="CatPad", bg=BG, fg=SUBTEXT,
                     font=fonts["title"])
    title.pack(side="left")

    dots = tk.Canvas(header, width=42, height=16, bg=BG, highlightthickness=0)
    dots.pack(side="right")

    def minimize():
        root.overrideredirect(False)  # give it back a frame so iconify works
        root.iconify()

    def on_map(_event):
        if root.state() == "normal":
            root.overrideredirect(True)

            def redecorate():
                _apply_round_corners(root)
                _apply_glass(root)

            root.after(10, redecorate)

    root.bind("<Map>", on_map)

    def dot(x, fill, glyph, glyph_fill, tag, action):
        dots.create_oval(x - 6, 2, x + 6, 14, fill=fill, outline=fill, tags=tag)
        dots.create_text(x, 8, text=glyph, font=fonts["dot"],
                         fill=glyph_fill, tags=tag)
        dots.tag_bind(tag, "<Button-1>", lambda e: action())

    dot(10, MIN_YELLOW, "–", MIN_GLYPH, "min", minimize)
    dot(30, CLOSE_RED, "✕", CLOSE_GLYPH, "close", root.destroy)

    drag = {}

    def press(e):
        drag.update(x=e.x_root - root.winfo_x(), y=e.y_root - root.winfo_y())

    def move(e):
        root.geometry(f"+{e.x_root - drag['x']}+{e.y_root - drag['y']}")

    for w in (header, title):
        w.bind("<Button-1>", press)
        w.bind("<B1-Motion>", move)

    # ---- macro card grid ----
    cards = []

    def launch(fn):
        for c in cards:
            c.set_enabled(False)
        set_status("Working…")

        def work():
            try:
                msg = fn(set_status)
            except Exception as exc:
                msg = f"Error: {exc}"
            set_status(msg)
            root.after(0, lambda: [c.set_enabled(True) for c in cards])

        threading.Thread(target=work, daemon=True).start()

    grid = tk.Frame(root, bg=BG)
    grid.pack(padx=12, pady=4)
    for i in range(max(TOTAL_SLOTS, len(MACROS))):
        if i < len(MACROS):
            icon, label, tip, fn = MACROS[i]
            card = Card(grid, icon, label, fonts,
                        command=lambda f=fn: launch(f))
            cards.append(card)
        else:
            tip = SLOT_TIP
            card = Card(grid, "", "", fonts)
        card.grid(row=i // COLUMNS, column=i % COLUMNS, padx=5, pady=5)
        Tooltip(card, tip, fonts["status"])

    tk.Label(root, textvariable=status, bg=BG, fg=SUBTEXT,
             font=fonts["status"], wraplength=CARD_W * COLUMNS + 10,
             justify="left").pack(anchor="w", padx=14, pady=(4, 0))

    tk.Label(root, text=f"CatPad · v{__version__} · by {__author__}",
             bg=BG, fg=FOOTER_FG, font=(base, 8)).pack(pady=(6, 10))

    root.update_idletasks()
    _apply_round_corners(root)
    _apply_glass(root)
    x = root.winfo_screenwidth() - root.winfo_width() - 40
    root.geometry(f"+{x}+120")
    root.mainloop()


if __name__ == "__main__":
    main()
