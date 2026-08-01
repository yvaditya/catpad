"""CATIA Macro Pad — a small always-on-top button panel that drives the
running 3DEXPERIENCE session. Add a macro by appending to MACROS."""
import threading
import tkinter as tk

from catia_pad.macros import color_bodies

# (button label, callable taking a log(str) callback, returning a summary)
# Append here — the grid keeps TOTAL_SLOTS positions, unfilled ones show
# as reserved slots.
MACROS = [
    ("Color by\nHierarchy", color_bodies.run),
]

BG = "#23262b"
BTN_BG = "#3a4048"
BTN_ACTIVE = "#4a525c"
FG = "#e8e4da"
STATUS_FG = "#a8b0a0"
SLOT_BG = "#2b2f35"
SLOT_FG = "#565d66"
COLUMNS = 2
TOTAL_SLOTS = 8


def main():
    root = tk.Tk()
    root.title("CATIA Macro Pad")
    root.configure(bg=BG, padx=10, pady=10)
    root.attributes("-topmost", True)
    root.resizable(False, False)

    status = tk.StringVar(value="Ready — select a node in CATIA, then hit a button.")

    def set_status(msg):
        root.after(0, status.set, msg)

    buttons = []

    def launch(button, fn):
        for b in buttons:
            b.config(state="disabled")
        set_status("Working…")

        def work():
            try:
                msg = fn(set_status)
            except Exception as exc:
                msg = f"Error: {exc}"
            set_status(msg)
            root.after(0, lambda: [b.config(state="normal") for b in buttons])

        threading.Thread(target=work, daemon=True).start()

    grid = tk.Frame(root, bg=BG)
    grid.pack()
    for i in range(max(TOTAL_SLOTS, len(MACROS))):
        if i < len(MACROS):
            label, fn = MACROS[i]
            btn = tk.Button(
                grid, text=label, width=12, height=3,
                bg=BTN_BG, fg=FG, activebackground=BTN_ACTIVE,
                activeforeground=FG, relief="flat",
                font=("Segoe UI", 10, "bold"), cursor="hand2",
            )
            btn.config(command=lambda b=btn, f=fn: launch(b, f))
            buttons.append(btn)
        else:
            btn = tk.Button(
                grid, text="+", width=12, height=3, state="disabled",
                bg=SLOT_BG, disabledforeground=SLOT_FG, relief="flat",
                font=("Segoe UI", 12),
            )
        btn.grid(row=i // COLUMNS, column=i % COLUMNS, padx=5, pady=5)

    tk.Label(
        root, textvariable=status, bg=BG, fg=STATUS_FG,
        font=("Segoe UI", 9), wraplength=260, justify="left",
    ).pack(anchor="w", pady=(8, 0))

    root.mainloop()


if __name__ == "__main__":
    main()
