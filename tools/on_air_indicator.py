#!/usr/bin/env python3
"""
MarketBullets ON AIR Indicator — compact strip widget
=====================================================
Slim floating bar (~300x46px) that controls Audacity record/pause.
Drag anywhere to reposition. Always on top.

SETUP:      pip install pywin32
RUN:        python on_air_indicator.py

AUDACITY KEYS USED:
    R     = Start recording
    P     = Pause / Resume
    Space = Stop
"""

import tkinter as tk
import threading
import time
import math

try:
    import win32gui
    import win32com.client
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# ── Colors ──────────────────────────────────────────────────────────────────
C_BG         = "#0e0e0e"
C_OFF        = "#333333"
C_REC        = "#ff2020"
C_PAUSE_CLR  = "#ffaa00"
C_DIM        = "#444444"
C_BTN_REC    = "#8b0000"
C_BTN_STOP   = "#2a0000"
C_BTN_PAUSE  = "#7a5000"
C_BTN_RESUME = "#1a4a1a"
C_BTN_DIS    = "#1e1e1e"


class OnAirIndicator:

    def __init__(self):
        self.state        = "IDLE"
        self.start_time   = None
        self.elapsed_base = 0.0
        self._pulse_val   = 0.0
        self._pulse_dir   = 1
        self._drag_x      = 0
        self._drag_y      = 0

        self.root = tk.Tk()
        self._setup_window()
        self._build_ui()
        self._update_display()
        self.root.after(60, self._pulse_tick)

    # ── Window ───────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.root.overrideredirect(True)          # no title bar
        # Position bottom-left: calculate from screen dimensions
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        W, H = 300, 70   # 46 top bar + 1 divider + 23 symbol row
        x = 10
        y = sh - H - 50   # 50px up from taskbar
        self.root.geometry(f"{W}x{H}+{x}+{y}")
        self.root.configure(bg=C_BG)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.93)
        self.root.after(3000, self._keep_topmost)

        self.root.bind("<Button-1>",  self._drag_start)
        self.root.bind("<B1-Motion>", self._drag_move)
        # Hotkeys
        self.root.bind("<Control-Alt-r>", lambda e: self._toggle_record())
        self.root.bind("<Control-Alt-p>", lambda e: self._toggle_pause())

    def _keep_topmost(self):
        self.root.attributes("-topmost", True)
        self.root.after(3000, self._keep_topmost)

    def _drag_start(self, e):
        self._drag_x, self._drag_y = e.x, e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        bar = tk.Frame(self.root, bg=C_BG, pady=4, padx=6)
        bar.pack(fill="both", expand=True)

        # Antenna tower red light — glow + core
        self.dot_cv = tk.Canvas(bar, width=28, height=28,
                                bg=C_BG, highlightthickness=0)
        self.dot_cv.pack(side="left", padx=(2, 4))
        # outer glow, mid glow, bright core
        self.dot_glow2 = self.dot_cv.create_oval( 1,  1, 27, 27, fill=C_BG,  outline="")
        self.dot_glow1 = self.dot_cv.create_oval( 5,  5, 23, 23, fill=C_BG,  outline="")
        self.dot_core  = self.dot_cv.create_oval(10, 10, 18, 18, fill=C_OFF, outline="")

        # Status label
        self.status_lbl = tk.Label(
            bar, text="OFF AIR", font=("Helvetica", 11, "bold"),
            fg=C_DIM, bg=C_BG, width=7, anchor="w"
        )
        self.status_lbl.pack(side="left")

        # Timer
        self.timer_lbl = tk.Label(
            bar, text="00:00:00", font=("Courier New", 10, "bold"),
            fg=C_DIM, bg=C_BG, width=8
        )
        self.timer_lbl.pack(side="left", padx=(0, 6))

        # REC / STOP button
        self.rec_btn = tk.Button(
            bar, text="REC", font=("Helvetica", 8, "bold"),
            bg=C_BTN_REC, fg="#ff8888",
            activebackground="#cc0000", activeforeground="white",
            relief="flat", padx=6, pady=1, cursor="hand2",
            command=self._toggle_record
        )
        self.rec_btn.pack(side="left", padx=2)

        # PAUSE / RESUME button
        self.pause_btn = tk.Button(
            bar, text="PAUSE", font=("Helvetica", 8, "bold"),
            bg=C_BTN_DIS, fg="#444444",
            activebackground=C_BTN_PAUSE, activeforeground="white",
            relief="flat", padx=6, pady=1, cursor="hand2",
            command=self._toggle_pause, state="disabled"
        )
        self.pause_btn.pack(side="left", padx=2)

        # Close ×
        close_lbl = tk.Label(
            bar, text="×", font=("Helvetica", 12),
            fg="#333333", bg=C_BG, cursor="hand2"
        )
        close_lbl.pack(side="right", padx=(4, 2))
        close_lbl.bind("<Button-1>", lambda e: self.root.destroy())

        # ── 1px divider ───────────────────────────────────────────────────────
        tk.Frame(self.root, bg="#2a2a2a", height=1).pack(fill="x")

        # ── Symbol transport row (full width, 23px) ───────────────────────────
        sym_row = tk.Frame(self.root, bg="#181818", height=23)
        sym_row.pack(fill="x")
        sym_row.pack_propagate(False)

        for symbol, cmd, tip in [
            ("⏹", self._toggle_record,  "STOP"),
            ("⏺", self._toggle_record,  "REC"),
            ("⏸", self._toggle_pause,   "PAUSE"),
        ]:
            btn = tk.Button(
                sym_row, text=symbol,
                font=("Segoe UI Symbol", 11),
                bg="#181818", fg="#666666",
                activebackground="#2a2a2a", activeforeground="white",
                relief="flat", cursor="hand2",
                command=cmd
            )
            btn.pack(side="left", expand=True, fill="both")

    # ── Audacity helpers ─────────────────────────────────────────────────────

    def _find_audacity(self):
        if not HAS_WIN32:
            return None
        found = []
        def cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and "Audacity" in win32gui.GetWindowText(hwnd):
                found.append(hwnd)
        win32gui.EnumWindows(cb, None)
        return found[0] if found else None

    def _send_to_audacity(self, key):
        if not HAS_WIN32:
            return
        hwnd = self._find_audacity()
        if not hwnd:
            return
        prev = win32gui.GetForegroundWindow()
        try:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.07)
            win32com.client.Dispatch("WScript.Shell").SendKeys(key)
            time.sleep(0.05)
            if prev and prev != hwnd:
                try:
                    win32gui.SetForegroundWindow(prev)
                except Exception:
                    pass
        except Exception:
            pass

    # ── State machine ─────────────────────────────────────────────────────────

    def _toggle_record(self):
        if self.state == "IDLE":
            self._send_to_audacity("r")
            self.state        = "RECORDING"
            self.start_time   = time.time()
            self.elapsed_base = 0.0
            self._start_timer()
        else:
            self._send_to_audacity(" ")
            self.state      = "IDLE"
            self.start_time = None
        self._update_display()

    def _toggle_pause(self):
        if self.state == "RECORDING":
            self._send_to_audacity("p")
            self.elapsed_base += time.time() - (self.start_time or time.time())
            self.start_time    = None
            self.state         = "PAUSED"
        elif self.state == "PAUSED":
            self._send_to_audacity("p")
            self.start_time = time.time()
            self.state      = "RECORDING"
        self._update_display()

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _start_timer(self):
        def tick():
            while self.state in ("RECORDING", "PAUSED"):
                self.root.after(0, self._refresh_timer)
                time.sleep(0.5)
        threading.Thread(target=tick, daemon=True).start()

    def _refresh_timer(self):
        if self.state == "RECORDING" and self.start_time:
            total = self.elapsed_base + (time.time() - self.start_time)
        elif self.state == "PAUSED":
            total = self.elapsed_base
        else:
            total = 0.0
        h, rem = divmod(int(total), 3600)
        m, s   = divmod(rem, 60)
        self.timer_lbl.config(text=f"{h:02d}:{m:02d}:{s:02d}")

    # ── Display ───────────────────────────────────────────────────────────────

    def _update_display(self):
        if self.state == "IDLE":
            self.status_lbl.config(text="OFF AIR", fg=C_DIM)
            self.timer_lbl.config(text="00:00:00", fg=C_DIM)
            self.rec_btn.config(text="REC",  bg=C_BTN_REC,  fg="#ff8888")
            self.pause_btn.config(text="PAUSE", bg=C_BTN_DIS, fg="#444444", state="disabled")

        elif self.state == "RECORDING":
            self.status_lbl.config(text="ON AIR", fg=C_REC)
            self.timer_lbl.config(fg=C_REC)
            self.rec_btn.config(text="STOP", bg=C_BTN_STOP, fg="#ff4444")
            self.pause_btn.config(text="PAUSE",  bg=C_BTN_PAUSE,  fg="white", state="normal")

        elif self.state == "PAUSED":
            self.status_lbl.config(text="PAUSED", fg=C_PAUSE_CLR)
            self.timer_lbl.config(fg=C_PAUSE_CLR)
            self.rec_btn.config(text="STOP",   bg=C_BTN_STOP,   fg="#ff4444")
            self.pause_btn.config(text="RESUME", bg=C_BTN_RESUME, fg="white", state="normal")

    # ── Pulse ─────────────────────────────────────────────────────────────────

    def _pulse_tick(self):
        if self.state == "RECORDING":
            # Sine wave: full cycle ~3.5 seconds (period = 3.5s, tick = 50ms)
            self._pulse_val += 0.09   # radians per tick
            t = (math.sin(self._pulse_val) + 1) / 2  # 0.0 → 1.0 smooth

            # Core: full red at peak
            rc = int(220 * t + 30)
            core_color = f"#{rc:02x}0000"

            # Inner glow: softer, slightly smaller range
            tg1 = t * 0.55
            rg1 = int(180 * tg1)
            glow1_color = f"#{rg1:02x}0000" if rg1 > 0 else C_BG

            # Outer glow: very faint halo
            tg2 = t * 0.25
            rg2 = int(120 * tg2)
            glow2_color = f"#{rg2:02x}0000" if rg2 > 0 else C_BG

            self.dot_cv.itemconfig(self.dot_core,  fill=core_color)
            self.dot_cv.itemconfig(self.dot_glow1, fill=glow1_color)
            self.dot_cv.itemconfig(self.dot_glow2, fill=glow2_color)

        elif self.state == "PAUSED":
            self.dot_cv.itemconfig(self.dot_core,  fill=C_PAUSE_CLR)
            self.dot_cv.itemconfig(self.dot_glow1, fill=C_BG)
            self.dot_cv.itemconfig(self.dot_glow2, fill=C_BG)

        elif self.state == "IDLE":
            self.dot_cv.itemconfig(self.dot_core,  fill=C_OFF)
            self.dot_cv.itemconfig(self.dot_glow1, fill=C_BG)
            self.dot_cv.itemconfig(self.dot_glow2, fill=C_BG)

        self.root.after(50, self._pulse_tick)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    OnAirIndicator().run()
