"""
ui/main_window.py — SignBridge Pro v3.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full feature set for the deaf/HoH community:

PANELS
  • Live Translate  — camera + real-time text, 3-tier save
  • Meeting Mode    — auto-caption overlay, Zoom/Teams/Meet integration guide
  • Voice Studio    — voice selection, pitch/speed, preview, emotion presets
  • History         — timestamped session log, export
  • Gesture Guide   — ASL/ISL alphabet + specials reference
  • Analytics       — real-time canvas graphs (words/min, accuracy, letter freq)
  • Settings        — confidence, camera, hotkeys, appearance

MODEL SWAP:
  gesture_handler.model = None  →  DEMO mode (random)
  Place sign_model.h5 + label_map.npy in model/ folder → auto-detected on start
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import queue, os, json, math, time, random
from datetime import datetime
from collections import deque
from PIL import Image, ImageTk

from ui.theme import Theme


# ═══════════════════════════════════════════════════════════════════
class MainWindow:
# ═══════════════════════════════════════════════════════════════════

    def __init__(self, base_path, camera_mgr, gesture_handler,
                 word_builder, sentence_mgr, tts, obs,
                 hotkeys, lang_switcher, theme):
        self.base_path       = base_path
        self.camera_mgr      = camera_mgr
        self.gesture_handler = gesture_handler
        self.word_builder    = word_builder
        self.sentence_mgr    = sentence_mgr
        self.tts             = tts
        self.obs             = obs
        self.hotkeys         = hotkeys
        self.ls              = lang_switcher
        self.T               = theme
        self._q              = queue.Queue()
        self.root            = None
        self._photo          = None

        # ── State ────────────────────────────────────────────────
        self._panels: dict       = {}
        self._nav_btns: dict     = {}
        self._conf_rect          = None
        self._hold_rect          = None
        self._hold_val           = 0.0
        self._sb_val: dict       = {}
        self._current_panel      = "live"

        # 3-tier save
        self._cache_sentence     = ""
        self._history: list      = []

        # Analytics data (rolling windows)
        self._wpm_history        = deque(maxlen=60)   # words per minute, last 60 samples
        self._acc_history        = deque(maxlen=60)   # accuracy %, last 60 samples
        self._letter_counts: dict= {}                 # letter frequency
        self._session_start      = None
        self._total_chars        = 0
        self._correct_chars      = 0                  # updated when model confirms
        self._words_this_minute  = 0
        self._minute_timer       = time.time()
        self._total_words        = 0
        self._total_sentences    = 0

        # Voice Studio state
        self._voice_preview_text = "Hello, I am using SignBridge Pro to communicate."
        self._selected_voice_idx = 0
        self._available_voices   = []

        # Meeting mode
        self._meeting_active     = False

    # ──────────────────────────────────────────────────────────────
    def run(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("SignBridge Pro")
        self.root.configure(bg=self.T.BG_BASE)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.resizable(True, True)
        self.root.minsize(1200, 750)

        # Wire callbacks
        self.camera_mgr.on_frame           = lambda f:    self._q.put(("frame",   f))
        self.camera_mgr.on_fps_update      = lambda v:    self._q.put(("fps",     v))
        self.camera_mgr.on_error           = lambda m:    self._q.put(("error",   m))
        self.camera_mgr.on_stopped         = lambda:      self._q.put(("stopped",))
        self.gesture_handler.on_prediction = lambda l, c: self._q.put(("pred",    l, c))
        self.gesture_handler.on_word_added = lambda w:    self._q.put(("word",    w))
        self.sentence_mgr.on_update        = lambda s:    self._q.put(("sent",    s))
        self.word_builder.on_char_update   = lambda p:    self._q.put(("partial", p))
        self.ls.on_change                  = self._apply_lang

        self.root.after(40, self._drain)
        self.root.after(1000, self._tick_analytics)
        self._show_splash()
        self.root.mainloop()

    # ═══════════════════════════════════════════════════════════════
    #  SPLASH
    # ═══════════════════════════════════════════════════════════════
    def _show_splash(self):
        T  = self.T
        sp = tk.Toplevel(self.root)
        sp.title("SignBridge Pro")
        sp.resizable(False, False)
        sp.configure(bg=T.BG_BASE)
        sp.protocol("WM_DELETE_WINDOW", lambda: None)
        self._splash = sp
        W, H = 660, 520
        sp.update_idletasks()
        sw, sh = sp.winfo_screenwidth(), sp.winfo_screenheight()
        sp.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        sp.overrideredirect(True)  # borderless splash

        # Background canvas with subtle gradient effect
        cv = tk.Canvas(sp, width=W, height=H, bg=T.BG_BASE, highlightthickness=0)
        cv.pack(fill="both", expand=True)

        # Decorative accent line at top
        cv.create_rectangle(0, 0, W, 3, fill=T.ACCENT, outline="")
        # Subtle glow dots
        for x, y, r, col in [(60,60,40,T.ACCENT),(600,460,30,T.ACCENT2),(320,480,50,T.ACCENT5)]:
            cv.create_oval(x-r, y-r, x+r, y+r, fill=T.BG_CARD, outline="")

        # Content frame
        outer = tk.Frame(cv, bg=T.BG_BASE)
        cv.create_window(W//2, H//2, window=outer, anchor="center")

        tk.Label(outer, text="🤟", font=("Segoe UI", 56), bg=T.BG_BASE).pack(pady=(0,2))
        tk.Label(outer, text="SignBridge Pro",
                 font=("Segoe UI", 34, "bold"),
                 bg=T.BG_BASE, fg=T.TEXT).pack()

        # Mint underline bar
        bar = tk.Frame(outer, bg=T.ACCENT, height=3, width=280)
        bar.pack(pady=(4, 10))

        tk.Label(outer, text="Real-time Sign Language  →  Voice & Text",
                 font=("Segoe UI", 12), bg=T.BG_BASE, fg=T.TEXT2).pack(pady=(0, 28))
        tk.Label(outer, text="Choose your language  /  अपनी भाषा चुनें",
                 font=("Segoe UI", 13, "bold"), bg=T.BG_BASE, fg=T.TEXT).pack(pady=(0, 16))

        row = tk.Frame(outer, bg=T.BG_BASE); row.pack()
        for flag, name, sub, lc, accent in [
            ("🇬🇧", "English", "Continue in English", "en", T.ACCENT),
            ("🇮🇳", "हिंदी",   "हिंदी में जारी रखें",  "hi", T.ACCENT2),
        ]:
            card = tk.Frame(row, bg=T.BG_CARD, width=200, height=180,
                            highlightbackground=T.BORDER2, highlightthickness=1)
            card.pack(side="left", padx=16)
            card.pack_propagate(False)
            inner = tk.Frame(card, bg=T.BG_CARD)
            inner.place(relx=.5, rely=.5, anchor="center")
            tk.Label(inner, text=flag, font=("Segoe UI", 38), bg=T.BG_CARD).pack()
            tk.Label(inner, text=name, font=("Segoe UI", 16, "bold"),
                     bg=T.BG_CARD, fg=T.TEXT).pack(pady=(4, 2))
            tk.Label(inner, text=sub, font=("Segoe UI", 9),
                     bg=T.BG_CARD, fg=T.TEXT2).pack()
            # Accent line at bottom of card
            tk.Frame(inner, bg=accent, height=2, width=60).pack(pady=(6, 0))

            def _hover_in(e, c=card, a=accent):  c.config(highlightbackground=a)
            def _hover_out(e, c=card):            c.config(highlightbackground=T.BORDER2)
            def _click(e, l=lc): self.ls.set_lang(l); self._launch_main()
            for w in [card, inner] + list(inner.winfo_children()):
                w.bind("<Enter>",    _hover_in)
                w.bind("<Leave>",    _hover_out)
                w.bind("<Button-1>", _click)

        tk.Label(outer, text="You can change this anytime  •  इसे बाद में भी बदल सकते हैं",
                 font=("Segoe UI", 9), bg=T.BG_BASE, fg=T.TEXT3).pack(pady=(22, 0))

        # Close button (top right)
        tk.Button(cv, text="✕", font=("Segoe UI", 10), bg=T.BG_BASE, fg=T.TEXT3,
                  relief="flat", bd=0, cursor="hand2",
                  command=lambda: None).place(x=W-30, y=8)

    def _launch_main(self):
        self._splash.destroy()
        self._build_ui()
        W, H = 1400, 860
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.root.deiconify()
        self.hotkeys.register_tkinter(self.root)
        self.root.focus_set()
        self._session_start = datetime.now()

    # ═══════════════════════════════════════════════════════════════
    #  MAIN UI SHELL
    # ═══════════════════════════════════════════════════════════════
    def _build_ui(self):
        T = self.T
        self.root.configure(bg=T.BG_BASE)

        # ── Titlebar ──────────────────────────────────────────────
        tb = tk.Frame(self.root, bg="#040810", height=48)
        tb.pack(fill="x"); tb.pack_propagate(False)
        # Accent strip at very top
        tk.Frame(tb, bg=T.ACCENT, height=2).place(x=0, y=0, relwidth=1)

        tk.Label(tb, text="🤟", font=("Segoe UI", 18),
                 bg="#040810", fg=T.ACCENT).pack(side="left", padx=(14, 6), pady=(4, 0))
        tk.Label(tb, text="SignBridge", font=("Segoe UI", 14, "bold"),
                 bg="#040810", fg=T.TEXT).pack(side="left", pady=(4, 0))
        tk.Label(tb, text=" Pro", font=("Segoe UI", 14, "bold"),
                 bg="#040810", fg=T.ACCENT).pack(side="left", pady=(4, 0))
        tk.Frame(tb, bg=T.BORDER2, width=1).pack(side="left", fill="y", padx=14, pady=10)
        self._lbl_tb_sub = tk.Label(tb, font=("Segoe UI", 10),
                                     bg="#040810", fg=T.TEXT2)
        self._lbl_tb_sub.pack(side="left", pady=(4, 0))

        # Right side of titlebar
        self._btn_lang = tk.Button(tb, font=("Segoe UI", 10, "bold"),
                                    bg=T.BG_CARD2, fg=T.TEXT2,
                                    relief="flat", bd=0, padx=12, pady=5,
                                    cursor="hand2", command=self.ls.toggle)
        self._btn_lang.pack(side="right", padx=12, pady=10)

        # Camera status pill
        self._lbl_tb_cam = tk.Label(tb, font=("Segoe UI", 9, "bold"),
                                     bg=T.ACCENT3, fg="#fff",
                                     padx=10, pady=4)
        self._lbl_tb_cam.pack(side="right", padx=(0, 8), pady=12)
        self._lbl_tb_cam.config(text=" ● Camera Inactive ")

        # Model badge
        model_ok = getattr(self.gesture_handler, "model_loaded", False)
        mbg = T.ACCENT if model_ok else T.ACCENT4
        mtxt = " 🧠 Model Ready " if model_ok else " 🎮 Demo Mode "
        tk.Label(tb, text=mtxt, font=("Segoe UI", 9, "bold"),
                 bg=mbg, fg="#000",
                 padx=8, pady=4).pack(side="right", padx=(0, 6), pady=12)

        # ── Body ──────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=T.BG_BASE)
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        self._content = tk.Frame(body, bg=T.BG_BASE)
        self._content.pack(side="left", fill="both", expand=True)

        # Build all panels
        self._build_panel_live()
        self._build_panel_meeting()
        self._build_panel_voice_studio()
        self._build_panel_history()
        self._build_panel_guide()
        self._build_panel_analytics()
        self._build_panel_settings()

        # Show live panel by default
        self._nav_go("live", "live")
        self._build_statusbar()
        self._apply_lang()

    # ═══════════════════════════════════════════════════════════════
    #  SIDEBAR
    # ═══════════════════════════════════════════════════════════════
    def _build_sidebar(self, parent):
        T  = self.T
        sb = tk.Frame(parent, bg=T.SIDEBAR_BG, width=T.SIDEBAR_W)
        sb.pack(side="left", fill="y"); sb.pack_propagate(False)
        # Right border
        tk.Frame(sb, bg=T.BORDER2, width=1).place(x=T.SIDEBAR_W-1, y=0, relheight=1)

        # Brand block
        brand = tk.Frame(sb, bg=T.SIDEBAR_BG, pady=20)
        brand.pack(fill="x", padx=16)
        tk.Label(brand, text="🤟", font=("Segoe UI", 22), bg=T.SIDEBAR_BG).pack(anchor="w")
        tk.Label(brand, text="SignBridge", font=("Segoe UI", 16, "bold"),
                 bg=T.SIDEBAR_BG, fg=T.TEXT).pack(anchor="w")
        tk.Label(brand, text="Pro  •  v3.0", font=("Segoe UI", 9),
                 bg=T.SIDEBAR_BG, fg=T.TEXT3).pack(anchor="w")
        tk.Frame(sb, bg=T.BORDER2, height=1).pack(fill="x", padx=16, pady=(0, 8))

        # Sign mode toggle
        mf = tk.Frame(sb, bg=T.SIDEBAR_BG, padx=14, pady=8)
        mf.pack(fill="x")
        tk.Label(mf, text="SIGN MODE", font=("Segoe UI", 8, "bold"),
                 bg=T.SIDEBAR_BG, fg=T.TEXT3).pack(anchor="w", pady=(0, 6))
        tr = tk.Frame(mf, bg=T.BG_CARD2, bd=0)
        tr.pack(fill="x")
        for mode in ("ASL", "ISL"):
            b = tk.Button(tr, text=mode, font=("Segoe UI", 11, "bold"),
                          width=5, relief="flat", bd=0, cursor="hand2",
                          command=lambda m=mode: self._set_sign_mode(m))
            b.pack(side="left", expand=True, fill="x", padx=2, pady=2)
            setattr(self, f"_mode_btn_{mode}", b)
        self._update_mode_btns("ASL")
        tk.Frame(sb, bg=T.BORDER2, height=1).pack(fill="x", padx=16, pady=(10, 4))

        # Nav items
        tk.Label(sb, text="NAVIGATION", font=("Segoe UI", 8, "bold"),
                 bg=T.SIDEBAR_BG, fg=T.TEXT3,
                 padx=14).pack(anchor="w", pady=(6, 2))

        NAV = [
            ("🎥", "Live Translate",  "live",      T.ACCENT),
            ("📺", "Meeting Mode",    "meeting",   T.ACCENT6),
            ("🎙️","Voice Studio",    "voice",     T.ACCENT5),
            ("📚", "History",         "history",   T.ACCENT2),
            ("📖", "Gesture Guide",   "guide",     T.ACCENT4),
            ("📊", "Analytics",       "analytics", T.GRAPH_2),
            ("⚙️","Settings",        "settings",  T.TEXT2),
        ]
        for icon, label, pid, accent_col in NAV:
            nid = pid
            row = tk.Frame(sb, bg=T.SIDEBAR_BG, cursor="hand2")
            row.pack(fill="x", pady=1)
            # Left accent bar (hidden by default, shown when active)
            acc_bar = tk.Frame(row, bg=accent_col, width=3)
            acc_bar.pack(side="left", fill="y")
            acc_bar.pack_propagate(False)
            inner_row = tk.Frame(row, bg=T.SIDEBAR_BG, padx=10, pady=9)
            inner_row.pack(side="left", fill="x", expand=True)
            ico_lbl = tk.Label(inner_row, text=icon, font=("Segoe UI", 13),
                                bg=T.SIDEBAR_BG, fg=T.TEXT2)
            ico_lbl.pack(side="left", padx=(0, 10))
            txt_lbl = tk.Label(inner_row, text=label, font=("Segoe UI", 11),
                                bg=T.SIDEBAR_BG, fg=T.TEXT2)
            txt_lbl.pack(side="left")
            self._nav_btns[nid] = (row, acc_bar, inner_row, ico_lbl, txt_lbl, accent_col)

            def _click(e, nid_=nid, pid_=pid):   self._nav_go(nid_, pid_)
            def _enter(e, r=row, ir=inner_row, il=ico_lbl, tl=txt_lbl):
                if r.cget("bg") != T.BG_CARD2:
                    for w in (r, ir, il, tl): w.config(bg=T.BG_CARD)
            def _leave(e, r=row, ir=inner_row, il=ico_lbl, tl=txt_lbl):
                if r.cget("bg") != T.BG_CARD2:
                    for w in (r, ir, il, tl): w.config(bg=T.SIDEBAR_BG)
            for w in (row, inner_row, ico_lbl, txt_lbl):
                w.bind("<Button-1>", _click)
                w.bind("<Enter>",    _enter)
                w.bind("<Leave>",    _leave)

        # System status card (bottom of sidebar)
        tk.Frame(sb, bg=T.BORDER2, height=1).pack(fill="x", padx=16, pady=(12, 0))
        sc = tk.Frame(sb, bg=T.SIDEBAR_BG, padx=14, pady=12)
        sc.pack(fill="x")
        tk.Label(sc, text="SYSTEM", font=("Segoe UI", 8, "bold"),
                 bg=T.SIDEBAR_BG, fg=T.TEXT3).pack(anchor="w", pady=(0, 8))
        self._sb_val = {}
        for key, dot_col, label, default in [
            ("cam",   T.ACCENT3, "Camera",  "Offline"),
            ("obs",   T.ACCENT4, "OBS",     "Standby"),
            ("model", T.ACCENT,  "Model",   "ASL Ready"),
        ]:
            r = tk.Frame(sc, bg=T.SIDEBAR_BG); r.pack(fill="x", pady=3)
            # Dot indicator
            dot = tk.Label(r, text="●", font=("Segoe UI", 8),
                           bg=T.SIDEBAR_BG, fg=dot_col)
            dot.pack(side="left")
            tk.Label(r, text=f" {label}", font=("Segoe UI", 10),
                     bg=T.SIDEBAR_BG, fg=T.TEXT2).pack(side="left")
            v = tk.Label(r, text=default, font=("Segoe UI", 10, "bold"),
                         bg=T.SIDEBAR_BG, fg=T.TEXT)
            v.pack(side="right")
            self._sb_val[key] = v

    def _nav_go(self, nav_id: str, panel_id: str):
        T = self.T
        for nid, (row, acc_bar, inner_row, ico, txt, acc_col) in self._nav_btns.items():
            if nid == nav_id:
                for w in (row, inner_row, ico, txt):
                    w.config(bg=T.BG_CARD2)
                ico.config(fg=acc_col); txt.config(fg=T.TEXT)
                acc_bar.config(bg=acc_col)
            else:
                for w in (row, inner_row, ico, txt):
                    w.config(bg=T.SIDEBAR_BG)
                ico.config(fg=T.TEXT2); txt.config(fg=T.TEXT2)
                acc_bar.config(bg=T.SIDEBAR_BG)
        for pid, frame in self._panels.items():
            (frame.pack if pid == panel_id else frame.pack_forget)(
                **({} if pid != panel_id else {"fill": "both", "expand": True})
            )
        self._current_panel = panel_id
        if panel_id == "history":    self._refresh_history_tree()
        if panel_id == "analytics":  self._redraw_all_graphs()

    # ═══════════════════════════════════════════════════════════════
    #  PANEL: LIVE TRANSLATE
    # ═══════════════════════════════════════════════════════════════
    def _build_panel_live(self):
        T   = self.T
        pnl = tk.Frame(self._content, bg=T.BG_BASE)
        self._panels["live"] = pnl

        # ── Control Bar ───────────────────────────────────────────
        ctrl = tk.Frame(pnl, bg=T.BG_BASE, pady=12, padx=16)
        ctrl.pack(fill="x")

        self._btn_start = tk.Button(ctrl, text="▶  Start Translation",
                                     command=self._start, **T.BTN_PRIMARY)
        self._btn_start.pack(side="left", padx=(0, 8))

        self._btn_stop = tk.Button(ctrl, text="■  Stop",
                                    command=self._stop, **T.BTN_DANGER)
        self._btn_stop.pack(side="left", padx=(0, 8))
        self._btn_stop.config(state="disabled")

        tk.Frame(ctrl, bg=T.BORDER2, width=1).pack(side="left", fill="y", padx=10, pady=4)

        self._btn_speak = tk.Button(ctrl, text="🔊  Speak Now",
                                     command=self._speak_now, **T.BTN_PURPLE)
        self._btn_speak.pack(side="left", padx=(0, 6))

        self._btn_clear = tk.Button(ctrl, text="🗑  Clear",
                                     command=self._clear, **T.BTN_GHOST)
        self._btn_clear.pack(side="left", padx=(0, 6))

        self._btn_save = tk.Button(ctrl, text="💾  Save",
                                    command=self._save_external, **T.BTN_GHOST)
        self._btn_save.pack(side="left", padx=(0, 6))

        self._btn_copy = tk.Button(ctrl, text="📋  Copy",
                                    command=self._copy, **T.BTN_GHOST)
        self._btn_copy.pack(side="left")

        # OBS badge (right)
        self._lbl_obs_badge = tk.Label(ctrl, text="● OBS — Standby",
                                        font=("Cascadia Code", 9),
                                        bg=T.BG_CARD2, fg=T.ACCENT4,
                                        padx=12, pady=8)
        self._lbl_obs_badge.pack(side="right")

        # ── Main split: camera + translation (bottom: settings row) ──
        # Build bottom FIRST so pack order ensures PanedWindow gets remaining space
        self._build_live_bottom(pnl)

        pw = tk.PanedWindow(pnl, orient="horizontal",
                            bg=T.BG_BASE, sashwidth=5,
                            sashrelief="flat", bd=0,
                            sashpad=2)
        pw.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        # ── Camera card ───────────────────────────────────────────
        cam_card = tk.Frame(pw, bg=T.BG_CARD,
                            highlightbackground=T.BORDER2, highlightthickness=1)
        pw.add(cam_card, minsize=440, stretch="always")

        # Camera header
        ch = tk.Frame(cam_card, bg=T.BG_CARD, pady=10, padx=14)
        ch.pack(fill="x")
        self._lbl_cam_title = tk.Label(ch, text="📷  Camera Feed",
                                        font=T.F_H2, bg=T.BG_CARD, fg=T.TEXT)
        self._lbl_cam_title.pack(side="left")
        self._lbl_cam_badge = tk.Label(ch, text=" ● OFFLINE ",
                                        font=("Segoe UI", 8, "bold"),
                                        bg=T.ACCENT3, fg="#fff", padx=6)
        self._lbl_cam_badge.pack(side="left", padx=8)
        self._lbl_fps = tk.Label(ch, text="— FPS", font=("Cascadia Code", 9),
                                  bg=T.BG_CARD, fg=T.TEXT3)
        self._lbl_fps.pack(side="right")
        tk.Frame(cam_card, bg=T.BORDER2, height=1).pack(fill="x")

        # Camera canvas — fills ALL remaining space
        self._cam_canvas = tk.Canvas(cam_card, bg="#02050A",
                                      highlightthickness=0, cursor="crosshair")
        self._cam_canvas.pack(fill="both", expand=True)
        self._draw_placeholder()
        tk.Frame(cam_card, bg=T.BORDER2, height=1).pack(fill="x")

        # Gesture strip (fixed 110px)
        gf = tk.Frame(cam_card, bg=T.BG_CARD2, pady=10, padx=14, height=110)
        gf.pack(fill="x"); gf.pack_propagate(False)

        # Large letter display
        letter_box = tk.Frame(gf, bg=T.BG_BASE, width=84, height=84)
        letter_box.pack(side="left", padx=(0, 16)); letter_box.pack_propagate(False)
        self._lbl_gesture_letter = tk.Label(letter_box, text="—",
                                             font=("Segoe UI", 42, "bold"),
                                             bg=T.BG_BASE, fg=T.ACCENT)
        self._lbl_gesture_letter.place(relx=.5, rely=.5, anchor="center")

        info = tk.Frame(gf, bg=T.BG_CARD2); info.pack(side="left", fill="both", expand=True)
        self._lbl_gest_name = tk.Label(info, text="No gesture detected",
                                        font=T.F_H2, bg=T.BG_CARD2, fg=T.TEXT)
        self._lbl_gest_name.pack(anchor="w", pady=(0, 6))

        self._lbl_conf = tk.Label(info, text="Confidence: 0%",
                                   font=("Segoe UI", 9), bg=T.BG_CARD2, fg=T.TEXT2)
        self._lbl_conf.pack(anchor="w")
        self._conf_canvas = tk.Canvas(info, height=5, bg=T.BG_BASE, highlightthickness=0)
        self._conf_canvas.pack(fill="x", pady=(2, 8))

        self._lbl_hold = tk.Label(info, text="Hold to confirm: 0%",
                                   font=("Segoe UI", 9), bg=T.BG_CARD2, fg=T.TEXT2)
        self._lbl_hold.pack(anchor="w")
        self._hold_canvas = tk.Canvas(info, height=5, bg=T.BG_BASE, highlightthickness=0)
        self._hold_canvas.pack(fill="x", pady=(2, 0))

        # ── Translation card ──────────────────────────────────────
        tr_card = tk.Frame(pw, bg=T.BG_CARD,
                           highlightbackground=T.BORDER2, highlightthickness=1)
        pw.add(tr_card, minsize=380, stretch="always")

        th = tk.Frame(tr_card, bg=T.BG_CARD, pady=10, padx=14)
        th.pack(fill="x")
        self._lbl_tr_title = tk.Label(th, text="📝  Real-time Translation",
                                       font=T.F_H2, bg=T.BG_CARD, fg=T.TEXT)
        self._lbl_tr_title.pack(side="left")
        self._lbl_lang_pill = tk.Label(th, text="English",
                                        font=("Segoe UI", 9, "bold"),
                                        bg=T.ACCENT, fg="#000", padx=10, pady=3)
        self._lbl_lang_pill.pack(side="left", padx=10)
        self._lbl_wc = tk.Label(th, text="Words: 0", font=("Cascadia Code", 9),
                                 bg=T.BG_CARD, fg=T.TEXT3)
        self._lbl_wc.pack(side="right")
        tk.Frame(tr_card, bg=T.BORDER2, height=1).pack(fill="x")

        # Partial word row
        pr = tk.Frame(tr_card, bg=T.BG_CARD2, height=32, padx=14)
        pr.pack(fill="x"); pr.pack_propagate(False)
        self._lbl_partial = tk.Label(pr, text="", font=("Cascadia Code", 11, "bold"),
                                      bg=T.BG_CARD2, fg=T.ACCENT4)
        self._lbl_partial.pack(side="left", pady=7)
        tk.Frame(tr_card, bg=T.BORDER2, height=1).pack(fill="x")

        # Main text area
        tf = tk.Frame(tr_card, bg=T.BG_CARD)
        tf.pack(fill="both", expand=True)
        self._txt = tk.Text(tf, font=("Segoe UI", 24, "bold"),
                             bg=T.BG_CARD, fg=T.TEXT,
                             wrap="word", padx=20, pady=20,
                             insertbackground=T.ACCENT,
                             selectbackground=T.ACCENT2,
                             relief="flat", bd=0, state="disabled",
                             spacing1=4, spacing2=2)
        vsb = tk.Scrollbar(tf, command=self._txt.yview,
                           bg=T.BG_CARD2, troughcolor=T.BG_CARD, relief="flat",
                           width=8)
        self._txt.config(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._txt.pack(fill="both", expand=True)

        # Footer
        tk.Frame(tr_card, bg=T.BORDER2, height=1).pack(fill="x")
        foot = tk.Frame(tr_card, bg=T.BG_CARD, pady=7, padx=14)
        foot.pack(fill="x")
        self._lbl_cc = tk.Label(foot, text="Chars: 0", font=("Cascadia Code", 9),
                                 bg=T.BG_CARD, fg=T.TEXT3)
        self._lbl_cc.pack(side="left")
        self._lbl_cache = tk.Label(foot, text="💾 Cache: —",
                                    font=("Cascadia Code", 9),
                                    bg=T.BG_CARD, fg=T.TEXT3)
        self._lbl_cache.pack(side="right")

    def _build_live_bottom(self, parent):
        T   = self.T
        bot = tk.Frame(parent, bg=T.BG_BASE, height=200)
        bot.pack(side="bottom", fill="x", padx=14, pady=(4, 10))
        bot.pack_propagate(False)
        for c in range(3): bot.columnconfigure(c, weight=1)

        def mkcard(col, icon, title, accent_color):
            c_frame = tk.Frame(bot, bg=T.BG_CARD,
                               highlightbackground=T.BORDER2, highlightthickness=1)
            c_frame.grid(row=0, column=col, sticky="nsew",
                         padx=(0, 8) if col < 2 else 0)
            # Accent top bar
            tk.Frame(c_frame, bg=accent_color, height=2).pack(fill="x")
            hdr = tk.Frame(c_frame, bg=T.BG_CARD, pady=8, padx=14)
            hdr.pack(fill="x")
            tk.Label(hdr, text=f"{icon}  {title}", font=T.F_H2,
                     bg=T.BG_CARD, fg=T.TEXT).pack(side="left")
            body = tk.Frame(c_frame, bg=T.BG_CARD, padx=14, pady=6)
            body.pack(fill="both", expand=True)
            return body

        # TTS Engine card
        tts_b = mkcard(0, "🔊", "Voice Engine", T.ACCENT5)
        pill_row = tk.Frame(tts_b, bg=T.BG_CARD); pill_row.pack(fill="x", pady=(0, 8))
        self._voice_btns = []
        for eng, col in [("pyttsx3", T.ACCENT), ("Coqui", T.ACCENT2),
                         ("Edge TTS", T.ACCENT5), ("gTTS", T.ACCENT4)]:
            b = tk.Button(pill_row, text=eng, font=("Segoe UI", 9, "bold"),
                          padx=8, pady=4, relief="flat", bd=0,
                          bg=T.BG_CARD2, fg=T.TEXT2, cursor="hand2",
                          command=lambda e=eng: self._set_voice(e))
            b.pack(side="left", padx=(0, 4))
            self._voice_btns.append((eng, b, col))
        self._set_voice("pyttsx3")

        def mk_bar(par, lbl, from_, to, init, fmt, resolution=0.1):
            f = tk.Frame(par, bg=T.BG_CARD); f.pack(fill="x", pady=2)
            top = tk.Frame(f, bg=T.BG_CARD); top.pack(fill="x")
            tk.Label(top, text=lbl, font=("Segoe UI", 9), bg=T.BG_CARD, fg=T.TEXT2).pack(side="left")
            vl = tk.Label(top, font=("Cascadia Code", 9), bg=T.BG_CARD, fg=T.ACCENT)
            vl.pack(side="right")
            sc = tk.Scale(f, from_=from_, to=to, resolution=resolution,
                          orient="horizontal", showvalue=False,
                          bg=T.BG_CARD, fg=T.ACCENT, troughcolor=T.BG_CARD2,
                          highlightthickness=0, relief="flat",
                          command=lambda v, vl_=vl, fn=fmt: vl_.config(text=fn(float(v))))
            sc.set(init); sc.pack(fill="x")
            vl.config(text=fmt(init)); return sc

        self._sc_spd = mk_bar(tts_b, "Speed", 0.5, 2.0, 1.0, lambda v: f"{v:.1f}×")
        self._sc_vol = mk_bar(tts_b, "Volume", 0, 100, 80, lambda v: f"{int(v)}%")

        # Auto-settings card
        auto_b = mkcard(1, "⚡", "Auto Settings", T.ACCENT)
        self._tgl = {}
        for key, lbl, default in [
            ("speak_end",   "Auto-speak on sentence end",  True),
            ("speak_pause", "Speak after 2s silence",      False),
            ("obs_overlay", "Write to OBS caption file",   True),
            ("skeleton",    "Show MediaPipe hand skeleton", True),
            ("meeting_bar", "Show Meeting caption bar",     False),
        ]:
            v = tk.BooleanVar(value=default); self._tgl[key] = v
            tk.Checkbutton(auto_b, text=lbl, variable=v,
                           font=("Segoe UI", 10), bg=T.BG_CARD, fg=T.TEXT2,
                           selectcolor=T.BG_CARD2, activebackground=T.BG_CARD,
                           cursor="hand2").pack(anchor="w", pady=2)

        # OBS card
        obs_b = mkcard(2, "📺", "OBS / Streaming", T.ACCENT6)
        tk.Label(obs_b, text=f"Caption file: {os.path.basename(self.obs.caption_path)}",
                 font=("Cascadia Code", 9), bg=T.BG_CARD, fg=T.ACCENT2).pack(anchor="w")
        self._btn_obs = tk.Button(obs_b, text="🔌  Connect to OBS WebSocket",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=T.BG_CARD2, fg=T.TEXT,
                                   relief="flat", bd=0, padx=12, pady=6,
                                   cursor="hand2", command=self._connect_obs)
        self._btn_obs.pack(fill="x", pady=(6, 6))
        for lbl, default in [("Virtual cam auto-start", False),
                              ("Captions → Zoom/Meet",  True),
                              ("Auto scene switch on start", False)]:
            v = tk.BooleanVar(value=default)
            tk.Checkbutton(obs_b, text=lbl, variable=v,
                           font=("Segoe UI", 10), bg=T.BG_CARD, fg=T.TEXT2,
                           selectcolor=T.BG_CARD2, activebackground=T.BG_CARD).pack(anchor="w", pady=1)

    # ═══════════════════════════════════════════════════════════════
    #  PANEL: MEETING MODE
    # ═══════════════════════════════════════════════════════════════
    def _build_panel_meeting(self):
        T   = self.T
        pnl = tk.Frame(self._content, bg=T.BG_BASE)
        self._panels["meeting"] = pnl

        # Header
        self._panel_header(pnl, "📺", "Meeting Mode", T.ACCENT6,
            "Auto-broadcast sign translations as live captions in Zoom, Teams, and Meet.")

        # Top control bar
        ctrl = tk.Frame(pnl, bg=T.BG_BASE, padx=16, pady=10)
        ctrl.pack(fill="x")
        self._btn_meeting_start = tk.Button(ctrl,
            text="▶  Start Meeting Mode", command=self._start_meeting, **T.BTN_ORANGE)
        self._btn_meeting_start.pack(side="left", padx=(0, 10))
        self._btn_meeting_stop = tk.Button(ctrl,
            text="■  Stop", command=self._stop_meeting, **T.BTN_DANGER)
        self._btn_meeting_stop.pack(side="left")
        self._btn_meeting_stop.config(state="disabled")
        tk.Label(ctrl, text="Caption auto-broadcasts to OBS text source in real time",
                 font=("Segoe UI", 10), bg=T.BG_BASE, fg=T.TEXT2).pack(side="right")

        # Main split
        body = tk.Frame(pnl, bg=T.BG_BASE)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        body.columnconfigure(0, weight=3); body.columnconfigure(1, weight=2)

        # Live caption preview
        left = tk.Frame(body, bg=T.BG_CARD,
                        highlightbackground=T.ACCENT6, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Frame(left, bg=T.ACCENT6, height=2).pack(fill="x")
        tk.Label(left, text="📡  Live Caption Preview", font=T.F_H2,
                 bg=T.BG_CARD, fg=T.TEXT, pady=12, padx=14).pack(anchor="w")
        tk.Frame(left, bg=T.BORDER2, height=1).pack(fill="x")

        # Caption display area (simulates what OBS shows)
        cap_bg = tk.Frame(left, bg="#000000")
        cap_bg.pack(fill="both", expand=True, padx=12, pady=12)
        self._lbl_meeting_caption = tk.Label(cap_bg, text="",
                                              font=("Segoe UI", 20, "bold"),
                                              bg="#000000", fg="#FFFFFF",
                                              wraplength=500, justify="left",
                                              padx=16, pady=24)
        self._lbl_meeting_caption.pack(fill="both", expand=True)

        # Format controls
        fmt = tk.Frame(left, bg=T.BG_CARD, padx=14, pady=10)
        fmt.pack(fill="x")
        tk.Label(fmt, text="Caption Style:", font=("Segoe UI", 10, "bold"),
                 bg=T.BG_CARD, fg=T.TEXT2).pack(side="left")
        self._caption_style_var = tk.StringVar(value="White on Black")
        for style in ["White on Black", "Black on White", "Mint on Dark", "Yellow on Black"]:
            tk.Radiobutton(fmt, text=style, variable=self._caption_style_var,
                           value=style, font=("Segoe UI", 9),
                           bg=T.BG_CARD, fg=T.TEXT2,
                           selectcolor=T.BG_CARD2,
                           activebackground=T.BG_CARD,
                           command=self._update_caption_style).pack(side="left", padx=8)

        # Right: integration guide
        right = tk.Frame(body, bg=T.BG_CARD,
                         highlightbackground=T.BORDER2, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Frame(right, bg=T.ACCENT6, height=2).pack(fill="x")
        tk.Label(right, text="🔗  Platform Setup", font=T.F_H2,
                 bg=T.BG_CARD, fg=T.TEXT, pady=12, padx=14).pack(anchor="w")
        tk.Frame(right, bg=T.BORDER2, height=1).pack(fill="x")

        guide_scroll = tk.Frame(right, bg=T.BG_CARD)
        guide_scroll.pack(fill="both", expand=True, padx=14, pady=10)

        steps = [
            ("🎥", "OBS Studio", T.ACCENT,
             ["1. Add Text (GDI+) source in OBS",
              "2. Enable 'Read from file'",
              f"3. Point to: dist/caption_output.txt",
              "4. Position over your webcam scene"]),
            ("💼", "Zoom", T.ACCENT5,
             ["1. Start your Zoom meeting",
              "2. Share the OBS Virtual Camera",
              "3. Captions appear via camera overlay",
              "4. Or use Zoom's CC feature"]),
            ("👥", "Google Meet", T.ACCENT2,
             ["1. Open Meet in Chrome",
              "2. Share OBS Virtual Camera",
              "3. Enable auto-captions in Meet settings",
              "4. SignBridge captions appear live"]),
            ("💬", "MS Teams", T.ACCENT6,
             ["1. Join Teams meeting",
              "2. Share OBS Virtual Camera as video",
              "3. Enable 'Turn on live captions'",
              "4. Both CC streams active"]),
        ]
        for icon, platform, color, step_list in steps:
            pf = tk.Frame(guide_scroll, bg=T.BG_CARD2,
                          highlightbackground=color, highlightthickness=1)
            pf.pack(fill="x", pady=(0, 8))
            tk.Label(pf, text=f"{icon}  {platform}", font=("Segoe UI", 11, "bold"),
                     bg=T.BG_CARD2, fg=color, pady=6, padx=10).pack(anchor="w")
            for step in step_list:
                tk.Label(pf, text=f"  {step}", font=("Segoe UI", 9),
                         bg=T.BG_CARD2, fg=T.TEXT2).pack(anchor="w", padx=8)
            tk.Frame(pf, bg=T.BG_CARD2, height=6).pack()

    # ═══════════════════════════════════════════════════════════════
    #  PANEL: VOICE STUDIO
    # ═══════════════════════════════════════════════════════════════
    def _build_panel_voice_studio(self):
        T   = self.T
        pnl = tk.Frame(self._content, bg=T.BG_BASE)
        self._panels["voice"] = pnl

        self._panel_header(pnl, "🎙️", "Voice Studio", T.ACCENT5,
            "Customise the synthetic voice that speaks your translations.")

        body = tk.Frame(pnl, bg=T.BG_BASE)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        body.columnconfigure(0, weight=2); body.columnconfigure(1, weight=3)

        # Left: voice settings
        left = tk.Frame(body, bg=T.BG_CARD,
                        highlightbackground=T.BORDER2, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Frame(left, bg=T.ACCENT5, height=2).pack(fill="x")
        tk.Label(left, text="🎛️  Voice Settings", font=T.F_H2,
                 bg=T.BG_CARD, fg=T.TEXT, pady=12, padx=14).pack(anchor="w")
        tk.Frame(left, bg=T.BORDER2, height=1).pack(fill="x")
        lbody = tk.Frame(left, bg=T.BG_CARD, padx=16, pady=12)
        lbody.pack(fill="both", expand=True)

        # Engine selector
        tk.Label(lbody, text="TTS ENGINE", font=("Segoe UI", 8, "bold"),
                 bg=T.BG_CARD, fg=T.TEXT3).pack(anchor="w", pady=(0, 6))
        eng_frame = tk.Frame(lbody, bg=T.BG_CARD)
        eng_frame.pack(fill="x", pady=(0, 14))
        self._vs_engine_var = tk.StringVar(value="pyttsx3")
        for eng, desc, col in [
            ("pyttsx3",  "Offline • Fast",    T.ACCENT),
            ("edge_tts", "Online • HD",       T.ACCENT5),
            ("gtts",     "Online • Google",   T.ACCENT2),
            ("coqui",    "Offline • Neural",  T.ACCENT4),
        ]:
            fr = tk.Frame(eng_frame, bg=T.BG_CARD2,
                          highlightbackground=T.BORDER2, highlightthickness=1)
            fr.pack(fill="x", pady=2)
            rb = tk.Radiobutton(fr, text=f"  {eng}", variable=self._vs_engine_var,
                                value=eng, font=("Segoe UI", 11, "bold"),
                                bg=T.BG_CARD2, fg=T.TEXT,
                                selectcolor=T.BG_CARD2, activebackground=T.BG_CARD2,
                                cursor="hand2")
            rb.pack(side="left", padx=8, pady=4)
            tk.Label(fr, text=desc, font=("Segoe UI", 9),
                     bg=T.BG_CARD2, fg=col).pack(side="right", padx=10)

        # Sliders
        def vs_slider(par, label, from_, to, init, fmt, res=0.05):
            f = tk.Frame(par, bg=T.BG_CARD); f.pack(fill="x", pady=6)
            top = tk.Frame(f, bg=T.BG_CARD); top.pack(fill="x")
            tk.Label(top, text=label, font=("Segoe UI", 10, "bold"),
                     bg=T.BG_CARD, fg=T.TEXT2).pack(side="left")
            vl = tk.Label(top, font=("Cascadia Code", 10),
                          bg=T.BG_CARD, fg=T.ACCENT5)
            vl.pack(side="right")
            sc = tk.Scale(f, from_=from_, to=to, resolution=res,
                          orient="horizontal", showvalue=False,
                          bg=T.BG_CARD, fg=T.ACCENT5, troughcolor=T.BG_CARD2,
                          highlightthickness=0, relief="flat",
                          command=lambda v, vl_=vl, fn=fmt: vl_.config(text=fn(float(v))))
            sc.set(init); sc.pack(fill="x", pady=2)
            vl.config(text=fmt(init)); return sc

        tk.Label(lbody, text="VOICE PARAMETERS", font=("Segoe UI", 8, "bold"),
                 bg=T.BG_CARD, fg=T.TEXT3).pack(anchor="w", pady=(0, 4))
        self._vs_speed  = vs_slider(lbody, "Speed / Rate",  0.5, 2.0, 1.0, lambda v: f"{v:.1f}×")
        self._vs_pitch  = vs_slider(lbody, "Pitch",         0.5, 2.0, 1.0, lambda v: f"{v:.1f}")
        self._vs_vol    = vs_slider(lbody, "Volume",          0, 100, 80,  lambda v: f"{int(v)}%", res=1)
        self._vs_pause  = vs_slider(lbody, "Sentence Pause",  0,   3, 0.5, lambda v: f"{v:.1f}s", res=0.1)

        # Emotion presets
        tk.Label(lbody, text="EMOTION PRESETS", font=("Segoe UI", 8, "bold"),
                 bg=T.BG_CARD, fg=T.TEXT3).pack(anchor="w", pady=(10, 6))
        preset_row = tk.Frame(lbody, bg=T.BG_CARD)
        preset_row.pack(fill="x")
        for preset, spd, vol in [("Calm", 0.85, 75), ("Clear", 1.0, 90),
                                   ("Urgent", 1.3, 100), ("Gentle", 0.75, 65)]:
            tk.Button(preset_row, text=preset, font=("Segoe UI", 10, "bold"),
                      bg=T.BG_CARD2, fg=T.TEXT2, relief="flat", bd=0,
                      padx=10, pady=5, cursor="hand2",
                      command=lambda s=spd, v=vol: (
                          self._vs_speed.set(s), self._vs_vol.set(v)
                      )).pack(side="left", padx=(0, 6))

        # Right: preview + voice list
        right = tk.Frame(body, bg=T.BG_CARD,
                         highlightbackground=T.BORDER2, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Frame(right, bg=T.ACCENT5, height=2).pack(fill="x")
        tk.Label(right, text="🎤  Voice Preview & Testing", font=T.F_H2,
                 bg=T.BG_CARD, fg=T.TEXT, pady=12, padx=14).pack(anchor="w")
        tk.Frame(right, bg=T.BORDER2, height=1).pack(fill="x")
        rbody = tk.Frame(right, bg=T.BG_CARD, padx=16, pady=12)
        rbody.pack(fill="both", expand=True)

        # Preview text
        tk.Label(rbody, text="PREVIEW TEXT", font=("Segoe UI", 8, "bold"),
                 bg=T.BG_CARD, fg=T.TEXT3).pack(anchor="w", pady=(0, 6))
        self._vs_preview_text = tk.Text(rbody, height=4, font=("Segoe UI", 11),
                                         bg=T.BG_CARD2, fg=T.TEXT,
                                         relief="flat", bd=0, padx=10, pady=8,
                                         insertbackground=T.ACCENT5,
                                         wrap="word")
        self._vs_preview_text.pack(fill="x", pady=(0, 10))
        self._vs_preview_text.insert("1.0", self._voice_preview_text)

        btn_row = tk.Frame(rbody, bg=T.BG_CARD); btn_row.pack(fill="x", pady=(0, 16))
        tk.Button(btn_row, text="🔊  Speak Preview", command=self._vs_speak_preview,
                  **T.BTN_CYAN).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="🎵  Test All Engines", command=self._vs_test_all,
                  **T.BTN_GHOST).pack(side="left")

        # Visual waveform (simulated)
        tk.Label(rbody, text="WAVEFORM (SIMULATED)", font=("Segoe UI", 8, "bold"),
                 bg=T.BG_CARD, fg=T.TEXT3).pack(anchor="w", pady=(0, 6))
        self._wave_canvas = tk.Canvas(rbody, height=80, bg=T.BG_CARD2,
                                       highlightthickness=0)
        self._wave_canvas.pack(fill="x", pady=(0, 16))
        self._draw_waveform()

        # Quick phrase buttons
        tk.Label(rbody, text="QUICK PHRASES", font=("Segoe UI", 8, "bold"),
                 bg=T.BG_CARD, fg=T.TEXT3).pack(anchor="w", pady=(0, 8))
        phrases = [
            "Hello, how are you?",
            "I need help, please.",
            "Thank you very much.",
            "Can you please repeat that?",
            "I understand you.",
            "Please speak slowly.",
            "I am deaf, please write.",
            "Nice to meet you!",
        ]
        phrase_grid = tk.Frame(rbody, bg=T.BG_CARD)
        phrase_grid.pack(fill="x")
        for i, phrase in enumerate(phrases):
            row, col = divmod(i, 2)
            tk.Button(phrase_grid, text=phrase,
                      font=("Segoe UI", 10), padx=10, pady=6,
                      bg=T.BG_CARD2, fg=T.TEXT2, relief="flat", bd=0,
                      cursor="hand2", wraplength=200, anchor="w",
                      command=lambda p=phrase: self.tts.speak(p)
                      ).grid(row=row, column=col, sticky="ew", padx=(0, 6), pady=2)
        phrase_grid.columnconfigure(0, weight=1)
        phrase_grid.columnconfigure(1, weight=1)

    # ═══════════════════════════════════════════════════════════════
    #  PANEL: HISTORY
    # ═══════════════════════════════════════════════════════════════
    def _build_panel_history(self):
        T   = self.T
        pnl = tk.Frame(self._content, bg=T.BG_BASE)
        self._panels["history"] = pnl

        self._panel_header(pnl, "📚", "Session History", T.ACCENT2,
            "All translated sentences — timestamped, searchable, and exportable.")

        # Toolbar
        tb = tk.Frame(pnl, bg=T.BG_BASE, padx=14, pady=4)
        tb.pack(fill="x")
        tk.Button(tb, text="📤  Export All (.txt)", command=self._export_history,
                  **T.BTN_PURPLE).pack(side="left", padx=(0, 8))
        tk.Button(tb, text="📊  Export CSV", command=self._export_history_csv,
                  **T.BTN_GHOST).pack(side="left", padx=(0, 8))
        tk.Button(tb, text="🗑  Clear History", command=self._clear_history,
                  **T.BTN_DANGER).pack(side="left")

        # Save tier info
        tier_bar = tk.Frame(pnl, bg=T.BG_CARD2)
        tier_bar.pack(fill="x", padx=14, pady=(0, 8))
        tk.Label(tier_bar,
                 text="  💾 Tier 1: OBS cache (auto)   •   "
                      "📚 Tier 2: Session history (here)   •   "
                      "📁 Tier 3: External .txt (Save button)",
                 font=("Segoe UI", 9), bg=T.BG_CARD2, fg=T.TEXT3, pady=5).pack(anchor="w")

        # Treeview
        tf = tk.Frame(pnl, bg=T.BG_BASE)
        tf.pack(fill="both", expand=True, padx=14)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("SB.Treeview",
                        background=T.BG_CARD, fieldbackground=T.BG_CARD,
                        foreground=T.TEXT, rowheight=38,
                        font=("Segoe UI", 11))
        style.configure("SB.Treeview.Heading",
                        background=T.BG_CARD2, foreground=T.TEXT2,
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("SB.Treeview",
                  background=[("selected", T.BG_CARD2)],
                  foreground=[("selected", T.ACCENT)])

        self._hist_tree = ttk.Treeview(
            tf, columns=("time", "words", "chars", "text"),
            show="headings", style="SB.Treeview")
        self._hist_tree.heading("time",  text="Time")
        self._hist_tree.heading("words", text="Words")
        self._hist_tree.heading("chars", text="Chars")
        self._hist_tree.heading("text",  text="Sentence")
        self._hist_tree.column("time",  width=80,  stretch=False)
        self._hist_tree.column("words", width=60,  stretch=False)
        self._hist_tree.column("chars", width=60,  stretch=False)
        self._hist_tree.column("text",  stretch=True)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._hist_tree.yview)
        self._hist_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._hist_tree.pack(fill="both", expand=True)

        # Summary
        self._lbl_hist_sum = tk.Label(pnl, text="No sessions yet.",
                                       font=("Segoe UI", 10),
                                       bg=T.BG_BASE, fg=T.TEXT3)
        self._lbl_hist_sum.pack(pady=(6, 10))

    # ═══════════════════════════════════════════════════════════════
    #  PANEL: GESTURE GUIDE
    # ═══════════════════════════════════════════════════════════════
    def _build_panel_guide(self):
        T   = self.T
        pnl = tk.Frame(self._content, bg=T.BG_BASE)
        self._panels["guide"] = pnl

        self._panel_header(pnl, "📖", "Gesture Guide", T.ACCENT4,
            "Complete ASL & ISL alphabet reference with confidence tips.")

        # Toggle ASL / ISL view
        toggle_bar = tk.Frame(pnl, bg=T.BG_BASE, padx=14)
        toggle_bar.pack(fill="x", pady=(0, 8))
        self._guide_mode_var = tk.StringVar(value="ASL")
        for mode in ("ASL", "ISL"):
            tk.Radiobutton(toggle_bar, text=f"  {mode}  ",
                           variable=self._guide_mode_var, value=mode,
                           font=("Segoe UI", 11, "bold"),
                           bg=T.BG_BASE, fg=T.TEXT2,
                           selectcolor=T.BG_BASE,
                           activebackground=T.BG_BASE,
                           cursor="hand2").pack(side="left", padx=4)

        body = tk.Frame(pnl, bg=T.BG_BASE)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # Alphabet grid
        left = tk.Frame(body, bg=T.BG_CARD,
                        highlightbackground=T.BORDER2, highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Frame(left, bg=T.ACCENT4, height=2).pack(fill="x")
        tk.Label(left, text="🔤  ASL Alphabet",
                 font=T.F_H2, bg=T.BG_CARD, fg=T.TEXT, pady=12, padx=14).pack(anchor="w")
        tk.Frame(left, bg=T.BORDER2, height=1).pack(fill="x")
        grid_f = tk.Frame(left, bg=T.BG_CARD, padx=14, pady=14)
        grid_f.pack(fill="both", expand=True)

        COLOURS = [T.ACCENT, T.ACCENT2, T.ACCENT5, T.ACCENT4, T.ACCENT3,
                   T.ACCENT6, T.ACCENT, T.ACCENT2, T.ACCENT5]
        for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            r, c = divmod(i, 9)
            color = COLOURS[c % len(COLOURS)]
            cell = tk.Frame(grid_f, bg=T.BG_CARD2, width=62, height=62,
                            highlightbackground=color, highlightthickness=1)
            cell.grid(row=r, column=c, padx=3, pady=3)
            cell.pack_propagate(False)
            tk.Label(cell, text=ch, font=("Segoe UI", 20, "bold"),
                     bg=T.BG_CARD2, fg=color).place(relx=.5, rely=.4, anchor="center")
            tk.Label(cell, text=str(i+1), font=("Segoe UI", 7),
                     bg=T.BG_CARD2, fg=T.TEXT3).place(relx=.5, rely=.82, anchor="center")

        # Right: specials + tips
        right = tk.Frame(body, bg=T.BG_BASE, width=320)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)

        spec = tk.Frame(right, bg=T.BG_CARD,
                        highlightbackground=T.BORDER2, highlightthickness=1)
        spec.pack(fill="x", pady=(0, 8))
        tk.Frame(spec, bg=T.ACCENT4, height=2).pack(fill="x")
        tk.Label(spec, text="⚡  Special Gestures", font=T.F_H2,
                 bg=T.BG_CARD, fg=T.TEXT, pady=10, padx=14).pack(anchor="w")
        tk.Frame(spec, bg=T.BORDER2, height=1).pack(fill="x")
        for g, d, col in [
            ("space",   "Commit word + add space",    T.ACCENT),
            ("del",     "Backspace last character",    T.ACCENT3),
            ("nothing", "End sentence with period (.).",T.ACCENT4),
        ]:
            r = tk.Frame(spec, bg=T.BG_CARD, padx=14, pady=6)
            r.pack(fill="x")
            tk.Label(r, text=g, font=("Cascadia Code", 11, "bold"),
                     bg=col, fg="#000", padx=10, pady=4,
                     width=9).pack(side="left", padx=(0, 12))
            tk.Label(r, text=d, font=("Segoe UI", 10),
                     bg=T.BG_CARD, fg=T.TEXT2, wraplength=180, justify="left").pack(side="left")

        tips = tk.Frame(right, bg=T.BG_CARD,
                        highlightbackground=T.BORDER2, highlightthickness=1)
        tips.pack(fill="both", expand=True)
        tk.Frame(tips, bg=T.ACCENT4, height=2).pack(fill="x")
        tk.Label(tips, text="💡  Tips for Best Accuracy", font=T.F_H2,
                 bg=T.BG_CARD, fg=T.TEXT, pady=10, padx=14).pack(anchor="w")
        tk.Frame(tips, bg=T.BORDER2, height=1).pack(fill="x")
        for tip in [
            "📐  Keep hand within the green bounding box",
            "💡  Ensure good, even front lighting",
            "🤚  Hold gesture steady for 1–2 seconds",
            "📷  Camera at eye level gives best results",
            "↔️   Arm's length distance is optimal",
            "🔢  Higher confidence = fewer errors",
            "⚡   Adjust threshold in Settings > Detection",
            "🎯  Practice letters with Gesture Guide open",
        ]:
            tk.Label(tips, text=tip, font=("Segoe UI", 10),
                     bg=T.BG_CARD, fg=T.TEXT2,
                     padx=14, pady=3, anchor="w").pack(fill="x")

    # ═══════════════════════════════════════════════════════════════
    #  PANEL: ANALYTICS  (real-time canvas graphs)
    # ═══════════════════════════════════════════════════════════════
    def _build_panel_analytics(self):
        T   = self.T
        pnl = tk.Frame(self._content, bg=T.BG_BASE)
        self._panels["analytics"] = pnl

        self._panel_header(pnl, "📊", "Session Analytics", T.GRAPH_2,
            "Real-time performance graphs — words/min, accuracy, letter frequency and more.")

        body = tk.Frame(pnl, bg=T.BG_BASE)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # ── Row 1: stat pills ─────────────────────────────────────
        stats_row = tk.Frame(body, bg=T.BG_BASE)
        stats_row.pack(fill="x", pady=(0, 10))
        self._stat_lbl = {}
        stat_defs = [
            ("Sentences",    "0",    "sents",    T.ACCENT),
            ("Total Words",  "0",    "words",    T.ACCENT2),
            ("Accuracy",     "—",    "accuracy", T.ACCENT5),
            ("Words/Min",    "0",    "wpm",      T.ACCENT4),
            ("Session Time", "0:00", "duration", T.ACCENT6),
            ("Avg Conf.",    "—",    "avg_conf", T.ACCENT3),
        ]
        for col, (label, default, key, color) in enumerate(stat_defs):
            stats_row.columnconfigure(col, weight=1)
            cell = tk.Frame(stats_row, bg=T.BG_CARD,
                            highlightbackground=color, highlightthickness=1)
            cell.grid(row=0, column=col, sticky="ew",
                      padx=(0, 8) if col < len(stat_defs)-1 else 0)
            tk.Frame(cell, bg=color, height=2).pack(fill="x")
            tk.Label(cell, text=label, font=("Segoe UI", 9),
                     bg=T.BG_CARD, fg=T.TEXT2, pady=4).pack()
            vl = tk.Label(cell, text=default,
                          font=("Segoe UI", 22, "bold"),
                          bg=T.BG_CARD, fg=color)
            vl.pack(pady=(0, 8))
            self._stat_lbl[key] = vl

        # ── Row 2: 3-column graph area ────────────────────────────
        graphs_row = tk.Frame(body, bg=T.BG_BASE)
        graphs_row.pack(fill="both", expand=True)
        graphs_row.columnconfigure(0, weight=2)
        graphs_row.columnconfigure(1, weight=2)
        graphs_row.columnconfigure(2, weight=3)

        def graph_card(col, title, subtitle, color):
            c = tk.Frame(graphs_row, bg=T.BG_CARD,
                         highlightbackground=T.BORDER2, highlightthickness=1)
            c.grid(row=0, column=col, sticky="nsew",
                   padx=(0, 8) if col < 2 else 0)
            tk.Frame(c, bg=color, height=2).pack(fill="x")
            hdr = tk.Frame(c, bg=T.BG_CARD, pady=8, padx=12)
            hdr.pack(fill="x")
            tk.Label(hdr, text=title, font=T.F_H2, bg=T.BG_CARD, fg=T.TEXT).pack(side="left")
            tk.Label(hdr, text=subtitle, font=("Segoe UI", 9),
                     bg=T.BG_CARD, fg=T.TEXT3).pack(side="right")
            tk.Frame(c, bg=T.BORDER2, height=1).pack(fill="x")
            cv = tk.Canvas(c, bg=T.BG_CARD, highlightthickness=0)
            cv.pack(fill="both", expand=True, padx=8, pady=8)
            return cv

        self._cv_wpm  = graph_card(0, "Words / Minute",    "rolling 60s",  T.GRAPH_1)
        self._cv_acc  = graph_card(1, "Accuracy Score",    "per sentence", T.GRAPH_2)
        self._cv_freq = graph_card(2, "Letter Frequency",  "A–Z heatmap",  T.GRAPH_3)

        # Bind resize so we can redraw graphs when window resizes
        self._cv_wpm.bind("<Configure>", lambda e: self._redraw_all_graphs())
        self._cv_acc.bind("<Configure>", lambda e: self._redraw_all_graphs())
        self._cv_freq.bind("<Configure>", lambda e: self._redraw_all_graphs())

    # ═══════════════════════════════════════════════════════════════
    #  PANEL: SETTINGS
    # ═══════════════════════════════════════════════════════════════
    def _build_panel_settings(self):
        T   = self.T
        pnl = tk.Frame(self._content, bg=T.BG_BASE)
        self._panels["settings"] = pnl

        self._panel_header(pnl, "⚙️", "Settings", T.TEXT2,
            "Detection thresholds, camera, hotkeys and appearance.")

        body = tk.Frame(pnl, bg=T.BG_BASE)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=1)

        def settings_card(row, col, icon, title, color):
            c = tk.Frame(body, bg=T.BG_CARD,
                         highlightbackground=T.BORDER2, highlightthickness=1)
            c.grid(row=row, column=col, sticky="nsew", padx=(0, 8) if col == 0 else 0, pady=(0, 8))
            tk.Frame(c, bg=color, height=2).pack(fill="x")
            tk.Label(c, text=f"{icon}  {title}", font=T.F_H2,
                     bg=T.BG_CARD, fg=T.TEXT, pady=10, padx=14).pack(anchor="w")
            tk.Frame(c, bg=T.BORDER2, height=1).pack(fill="x")
            b = tk.Frame(c, bg=T.BG_CARD, padx=16, pady=12)
            b.pack(fill="both", expand=True)
            return b

        # Detection settings
        det = settings_card(0, 0, "🎯", "Detection", T.ACCENT)

        def det_slider(par, label, from_, to, init, fmt, res=0.05):
            f = tk.Frame(par, bg=T.BG_CARD); f.pack(fill="x", pady=8)
            top = tk.Frame(f, bg=T.BG_CARD); top.pack(fill="x")
            tk.Label(top, text=label, font=("Segoe UI", 11, "bold"),
                     bg=T.BG_CARD, fg=T.TEXT2).pack(side="left")
            vl = tk.Label(top, font=("Cascadia Code", 11),
                          bg=T.BG_CARD, fg=T.ACCENT)
            vl.pack(side="right")
            sc = tk.Scale(f, from_=from_, to=to, resolution=res,
                          orient="horizontal", showvalue=False,
                          bg=T.BG_CARD, fg=T.ACCENT, troughcolor=T.BG_CARD2,
                          highlightthickness=0, relief="flat",
                          command=lambda v, vl_=vl, fn=fmt: vl_.config(text=fn(float(v))))
            sc.set(init); sc.pack(fill="x", pady=4)
            vl.config(text=fmt(init)); return sc

        self._sc_conf     = det_slider(det, "Confidence Threshold",
                                       0.50, 1.0, 0.80, lambda v: f"{v:.0%}")
        self._sc_frames   = det_slider(det, "Confirmation Frames",
                                       5, 30, 15, lambda v: f"{int(v)} frames", res=1)
        self._sc_interval = det_slider(det, "Repeat Delay (s)",
                                       0.5, 5.0, 2.0, lambda v: f"{v:.1f}s", res=0.5)
        tk.Button(det, text="Apply Detection Settings",
                  font=("Segoe UI", 11, "bold"),
                  bg=T.ACCENT, fg="#000", relief="flat", bd=0,
                  padx=16, pady=8, cursor="hand2",
                  command=self._apply_detection).pack(anchor="w", pady=(8, 0))

        # Camera settings
        cam = settings_card(0, 1, "📷", "Camera", T.ACCENT5)
        tk.Label(cam, text="Camera Index (0 = default):",
                 font=("Segoe UI", 11, "bold"), bg=T.BG_CARD, fg=T.TEXT2).pack(anchor="w")
        self._cam_idx_var = tk.IntVar(value=0)
        spin_f = tk.Frame(cam, bg=T.BG_CARD); spin_f.pack(anchor="w", pady=8)
        tk.Spinbox(spin_f, from_=0, to=5, textvariable=self._cam_idx_var,
                   font=("Segoe UI", 12), bg=T.BG_CARD2, fg=T.TEXT,
                   relief="flat", width=6,
                   buttonbackground=T.BG_CARD2).pack(side="left")

        tk.Label(cam, text="Resolution:", font=("Segoe UI", 11, "bold"),
                 bg=T.BG_CARD, fg=T.TEXT2).pack(anchor="w", pady=(8, 4))
        self._res_var = tk.StringVar(value="1280×720")
        for res in ("640×480", "1280×720", "1920×1080"):
            tk.Radiobutton(cam, text=res, variable=self._res_var, value=res,
                           font=("Segoe UI", 10), bg=T.BG_CARD, fg=T.TEXT2,
                           selectcolor=T.BG_CARD2,
                           activebackground=T.BG_CARD).pack(anchor="w", pady=2)

        tk.Label(cam, text="Mirror Mode:", font=("Segoe UI", 11, "bold"),
                 bg=T.BG_CARD, fg=T.TEXT2).pack(anchor="w", pady=(8, 4))
        self._mirror_var = tk.BooleanVar(value=False)
        tk.Checkbutton(cam, text="Flip camera horizontally",
                       variable=self._mirror_var, font=("Segoe UI", 10),
                       bg=T.BG_CARD, fg=T.TEXT2,
                       selectcolor=T.BG_CARD2,
                       activebackground=T.BG_CARD).pack(anchor="w")

        # Hotkeys settings
        hk = settings_card(1, 0, "⌨️", "Hotkeys", T.ACCENT2)
        hotkey_defs = [
            ("Start / Stop Translation", "F5"),
            ("Speak Current Text",       "F6"),
            ("Clear Text",               "F7"),
            ("Save Session",             "Ctrl+S"),
            ("Toggle Language",          "Ctrl+L"),
            ("Emergency Stop Camera",    "Escape"),
        ]
        for action, key in hotkey_defs:
            r = tk.Frame(hk, bg=T.BG_CARD); r.pack(fill="x", pady=4)
            tk.Label(r, text=action, font=("Segoe UI", 10),
                     bg=T.BG_CARD, fg=T.TEXT2).pack(side="left")
            tk.Label(r, text=key, font=("Cascadia Code", 10, "bold"),
                     bg=T.BG_CARD2, fg=T.ACCENT2, padx=8, pady=3).pack(side="right")

        # Save / About
        about = settings_card(1, 1, "💾", "Save & About", T.ACCENT4)
        tk.Button(about, text="💾  Save All Settings",
                  font=("Segoe UI", 11, "bold"),
                  bg=T.ACCENT, fg="#000", relief="flat", bd=0,
                  padx=16, pady=8, cursor="hand2",
                  command=self._save_settings_file).pack(anchor="w", pady=(0, 10))
        tk.Button(about, text="↩️  Reset to Defaults",
                  font=("Segoe UI", 11, "bold"),
                  bg=T.BG_CARD2, fg=T.TEXT2, relief="flat", bd=0,
                  padx=16, pady=8, cursor="hand2",
                  command=lambda: messagebox.showinfo("Reset", "Settings reset to defaults.")).pack(anchor="w")

        tk.Frame(about, bg=T.BORDER2, height=1).pack(fill="x", pady=12)
        for line in [
            "SignBridge Pro  v3.0",
            "Real-time Sign Language → Voice & Text",
            "Built for the Deaf/HoH Community",
            "",
            "Technologies: Python 3.11 • Tkinter",
            "MediaPipe • TensorFlow/Keras • pyttsx3",
            "OpenCV • PyInstaller",
            "",
            "Model: Drop sign_model.h5 + label_map.npy",
            "into the model/ folder to go live.",
        ]:
            tk.Label(about, text=line, font=("Segoe UI", 9),
                     bg=T.BG_CARD, fg=T.TEXT2 if line else T.TEXT3).pack(anchor="w")

    # ═══════════════════════════════════════════════════════════════
    #  STATUS BAR
    # ═══════════════════════════════════════════════════════════════
    def _build_statusbar(self):
        T  = self.T
        sb = tk.Frame(self.root, bg="#02050A", height=26)
        sb.pack(fill="x", side="bottom"); sb.pack_propagate(False)
        tk.Frame(sb, bg=T.BORDER2, height=1).place(x=0, y=0, relwidth=1)

        model_ok = getattr(self.gesture_handler, "model_loaded", False)
        items = [
            (f"🧠 {'Model Ready' if model_ok else 'Demo Mode'}",
             T.ACCENT if model_ok else T.ACCENT4),
            ("● OBS: Standby", T.ACCENT4),
        ]
        for text, col in items:
            tk.Label(sb, text=f"  {text}  ", font=("Cascadia Code", 8),
                     bg="#02050A", fg=col).pack(side="left")
            tk.Frame(sb, bg=T.BORDER2, width=1).pack(side="left", fill="y", pady=4)

        self._lbl_sb_cam = tk.Label(sb, text="  📷 Camera: Offline",
                                     font=("Cascadia Code", 8),
                                     bg="#02050A", fg=T.TEXT3)
        self._lbl_sb_cam.pack(side="left")

        self._lbl_sb_fps = tk.Label(sb, text="— FPS",
                                     font=("Cascadia Code", 8),
                                     bg="#02050A", fg=T.ACCENT)
        self._lbl_sb_fps.pack(side="right", padx=10)
        tk.Label(sb, text="MediaPipe  •  TensorFlow  •  Tkinter  ",
                 font=("Cascadia Code", 8),
                 bg="#02050A", fg=T.TEXT3).pack(side="right")

    # ═══════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════
    def _panel_header(self, parent, icon, title, color, subtitle=""):
        T = self.T
        hdr = tk.Frame(parent, bg=T.BG_CARD,
                       highlightbackground=T.BORDER2, highlightthickness=0)
        hdr.pack(fill="x", padx=14, pady=(12, 8))
        tk.Frame(hdr, bg=color, height=2).pack(fill="x")
        inner = tk.Frame(hdr, bg=T.BG_CARD, pady=12, padx=16)
        inner.pack(fill="x")
        tk.Label(inner, text=f"{icon}  {title}",
                 font=("Segoe UI", 16, "bold"),
                 bg=T.BG_CARD, fg=T.TEXT).pack(side="left")
        if subtitle:
            tk.Label(inner, text=subtitle, font=("Segoe UI", 10),
                     bg=T.BG_CARD, fg=T.TEXT2).pack(side="left", padx=14)

    # ═══════════════════════════════════════════════════════════════
    #  LANGUAGE
    # ═══════════════════════════════════════════════════════════════
    def _apply_lang(self):
        s  = self.ls.t
        en = self.ls.lang == "en"
        try:
            self._lbl_tb_sub.config(text=s("tagline"))
            self._btn_lang.config(text="🇬🇧 English" if en else "🇮🇳 हिंदी")
            self._lbl_lang_pill.config(text="English" if en else "हिंदी")
            cam_up = self.camera_mgr.is_running
            self._lbl_tb_cam.config(
                text=f" ● {'Camera Active' if cam_up else 'Camera Inactive'} ",
                bg=T.ACCENT if cam_up else T.ACCENT3)
        except Exception: pass

    # ═══════════════════════════════════════════════════════════════
    #  GRAPH DRAWING (pure-Tkinter canvas charts)
    # ═══════════════════════════════════════════════════════════════
    def _redraw_all_graphs(self):
        self._draw_wpm_graph()
        self._draw_acc_graph()
        self._draw_freq_graph()

    def _draw_line_graph(self, canvas, data, color, title="", y_fmt=str, y_range=None):
        canvas.delete("all")
        canvas.update_idletasks()
        W = max(canvas.winfo_width(),  100)
        H = max(canvas.winfo_height(), 60)
        PAD_L, PAD_R, PAD_T, PAD_B = 36, 10, 8, 24

        cw = W - PAD_L - PAD_R
        ch = H - PAD_T - PAD_B

        # Background grid
        for i in range(5):
            gy = PAD_T + i * ch // 4
            canvas.create_line(PAD_L, gy, W - PAD_R, gy,
                               fill=self.T.BG_CARD2, dash=(3, 4))

        if not data:
            canvas.create_text(W//2, H//2, text="Waiting for data…",
                               fill=self.T.TEXT3, font=("Segoe UI", 9))
            return

        vals = list(data)
        mn   = y_range[0] if y_range else min(vals)
        mx   = y_range[1] if y_range else max(vals)
        if mx == mn: mx = mn + 1

        def px(i): return PAD_L + int(i / max(len(vals)-1, 1) * cw)
        def py(v): return PAD_T + ch - int((v - mn) / (mx - mn) * ch)

        # Fill area under line
        pts = [PAD_L, PAD_T + ch]
        for i, v in enumerate(vals): pts += [px(i), py(v)]
        pts += [px(len(vals)-1), PAD_T + ch]
        # Create gradient fill using stipple
        canvas.create_polygon(pts, fill=color, outline="", stipple="gray25")

        # Line
        for i in range(1, len(vals)):
            canvas.create_line(px(i-1), py(vals[i-1]), px(i), py(vals[i]),
                               fill=color, width=2, smooth=True)

        # Last value dot + label
        lx, ly = px(len(vals)-1), py(vals[-1])
        canvas.create_oval(lx-4, ly-4, lx+4, ly+4, fill=color, outline="")
        canvas.create_text(lx, ly-12, text=y_fmt(vals[-1]),
                           fill=color, font=("Cascadia Code", 8, "bold"))

        # Y axis labels
        for i in range(5):
            v   = mn + (mx - mn) * i / 4
            gy  = PAD_T + ch - int(i * ch / 4)
            canvas.create_text(PAD_L - 4, gy, text=y_fmt(v),
                               fill=self.T.TEXT3, font=("Cascadia Code", 7), anchor="e")

    def _draw_wpm_graph(self):
        self._draw_line_graph(
            self._cv_wpm,
            self._wpm_history,
            self.T.GRAPH_1,
            y_fmt=lambda v: f"{int(v)}",
            y_range=(0, max(list(self._wpm_history) or [1]) * 1.2 + 1),
        )

    def _draw_acc_graph(self):
        self._draw_line_graph(
            self._cv_acc,
            self._acc_history,
            self.T.GRAPH_2,
            y_fmt=lambda v: f"{v:.0f}%",
            y_range=(0, 100),
        )

    def _draw_freq_graph(self):
        cv = self._cv_freq
        cv.delete("all")
        cv.update_idletasks()
        W = max(cv.winfo_width(), 100)
        H = max(cv.winfo_height(), 60)

        if not self._letter_counts:
            cv.create_text(W//2, H//2, text="Sign letters to build heatmap",
                           fill=self.T.TEXT3, font=("Segoe UI", 9))
            return

        letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        counts  = [self._letter_counts.get(l, 0) for l in letters]
        mx      = max(counts) or 1
        n       = len(letters)
        bw      = (W - 20) / n
        colours = [self.T.GRAPH_1, self.T.GRAPH_2, self.T.GRAPH_3,
                   self.T.GRAPH_4, self.T.GRAPH_5]

        for i, (l, c) in enumerate(zip(letters, counts)):
            x0 = 10 + i * bw
            x1 = x0 + bw - 1
            bh = int((c / mx) * (H - 30))
            col = colours[i % len(colours)]
            if bh > 0:
                cv.create_rectangle(x0, H - 20 - bh, x1, H - 20,
                                    fill=col, outline="")
            cv.create_text(x0 + bw/2, H - 10, text=l,
                           fill=self.T.TEXT3, font=("Segoe UI", 7))

    def _draw_waveform(self):
        """Simulated TTS waveform on voice studio canvas."""
        cv = self._wave_canvas
        cv.delete("all")
        cv.update_idletasks()
        W = max(cv.winfo_width(), 200)
        H = max(cv.winfo_height(), 80)
        mid = H // 2
        pts = [0, mid]
        for x in range(1, W, 3):
            amp = random.gauss(0, H * 0.22) * math.exp(-((x/W - 0.5)**2) * 3)
            pts += [x, mid + amp]
        pts += [W, mid]
        cv.create_line(pts, fill=self.T.ACCENT5, width=1, smooth=True)

    # ═══════════════════════════════════════════════════════════════
    #  ANALYTICS TICK  (called every 1000ms)
    # ═══════════════════════════════════════════════════════════════
    def _tick_analytics(self):
        # WPM — count words in this window
        now = time.time()
        if now - self._minute_timer >= 10.0:  # update every 10s
            wpm = self._words_this_minute * 6  # extrapolate to per-minute
            self._wpm_history.append(wpm)
            self._words_this_minute = 0
            self._minute_timer = now

        # Session duration
        if self._session_start:
            elapsed = datetime.now() - self._session_start
            total_s = int(elapsed.total_seconds())
            mm, ss  = divmod(total_s, 60)
            try:
                self._stat_lbl["duration"].config(text=f"{mm}:{ss:02d}")
            except Exception: pass

        # Redraw graphs if analytics panel is visible
        if self._current_panel == "analytics":
            self._redraw_all_graphs()

        self.root.after(1000, self._tick_analytics)

    def _update_analytics_stats(self):
        try:
            total_w = sum(h["words"] for h in self._history)
            avg_c   = (self._correct_chars / max(self._total_chars, 1)) * 100
            wpm_now = self._wpm_history[-1] if self._wpm_history else 0
            avg_conf_val = (sum(self._acc_history) / max(len(self._acc_history), 1))

            self._stat_lbl["sents"].config(text=str(len(self._history)))
            self._stat_lbl["words"].config(text=str(total_w))
            self._stat_lbl["accuracy"].config(text=f"{avg_c:.0f}%")
            self._stat_lbl["wpm"].config(text=f"{wpm_now:.0f}")
            self._stat_lbl["avg_conf"].config(text=f"{avg_conf_val:.0f}%")
        except Exception: pass

    # ═══════════════════════════════════════════════════════════════
    #  3-TIER SAVE
    # ═══════════════════════════════════════════════════════════════
    def _tier1_update(self, sentence: str):
        """Tier 1: auto-write to OBS caption file every word."""
        self._cache_sentence = sentence
        if self._tgl.get("obs_overlay", tk.BooleanVar()).get():
            self.obs.update_caption(sentence)
        words = len(sentence.split()) if sentence else 0
        try:
            self._lbl_cache.config(text=f"💾 Cache: {words}w")
            if self._meeting_active:
                self._lbl_meeting_caption.config(text=sentence)
        except Exception: pass

    def _tier2_commit(self, sentence: str):
        """Tier 2: save to in-app history at sentence end."""
        if not sentence.strip(): return
        entry = {
            "time":  datetime.now().strftime("%H:%M:%S"),
            "text":  sentence.strip(),
            "words": len(sentence.split()),
            "chars": len(sentence),
        }
        self._history.append(entry)
        # Accuracy sample (based on current model confidence history)
        if self._acc_history:
            # Already appended via pred handler
            pass
        self._total_sentences += 1
        self._update_analytics_stats()

    def _save_external(self):
        """Tier 3: Save As .txt dialog."""
        text = self.sentence_mgr.current_sentence
        if not text:
            if self._history and messagebox.askyesno("Save",
                    "No active sentence.\nExport full session history?"):
                self._export_history()
            else:
                messagebox.showwarning("Save", "Nothing to save yet.")
            return
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            initialfile=f"signbridge_{ts}.txt",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("SignBridge Pro — Translation Export\n")
                f.write(f"Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(text)
            messagebox.showinfo("Saved", f"Saved to:\n{path}")

    # ═══════════════════════════════════════════════════════════════
    #  ACTIONS
    # ═══════════════════════════════════════════════════════════════
    def _start(self):
        cam_idx = getattr(self, "_cam_idx_var", None)
        idx = cam_idx.get() if cam_idx else 0
        if self.camera_mgr.start(camera_index=idx):
            T = self.T
            self._btn_start.config(state="disabled")
            self._btn_stop.config(state="normal")
            self._lbl_cam_badge.config(text=" ● LIVE ", bg=T.ACCENT, fg="#000")
            self._lbl_tb_cam.config(text=" ● Camera Active ", bg=T.ACCENT, fg="#000")
            self._sb_val["cam"].config(text="Active", fg=T.ACCENT)
            self._lbl_sb_cam.config(text="  📷 Camera: Active", fg=T.ACCENT)
            self._animate_hold()
            if not self._session_start:
                self._session_start = datetime.now()

    def _stop(self):
        self.camera_mgr.stop()

    def _speak_now(self):
        s = self.sentence_mgr.current_sentence
        if s: self.tts.speak(s)

    def _clear(self):
        self.sentence_mgr.clear()
        self.word_builder.reset()
        self.obs.clear()
        self._set_txt("")
        self._lbl_partial.config(text="")
        self._lbl_wc.config(text="Words: 0")
        self._lbl_cc.config(text="Chars: 0")
        self._cache_sentence = ""
        self._lbl_cache.config(text="💾 Cache: cleared")

    def _copy(self):
        s = self.sentence_mgr.current_sentence
        if s:
            self.root.clipboard_clear()
            self.root.clipboard_append(s)

    def _connect_obs(self):
        ok = self.obs.connect_websocket()
        if ok:
            self._btn_obs.config(text="✅  OBS Connected", fg=self.T.ACCENT)
            self._sb_val["obs"].config(text="Connected", fg=self.T.ACCENT)
            self._lbl_obs_badge.config(text="● OBS — Live", fg=self.T.ACCENT)
        else:
            messagebox.showinfo("OBS",
                f"Using file-based captions.\nPath:\n{self.obs.caption_path}")

    def _set_voice(self, eng: str):
        T = self.T
        for e, b, col in self._voice_btns:
            b.config(bg=col if e == eng else T.BG_CARD2,
                     fg="#000" if e == eng else T.TEXT2)
        self.tts.set_engine(eng.lower().replace(" ", "_"))

    def _set_sign_mode(self, mode: str):
        self.ls.set_sign_mode(mode)
        self._update_mode_btns(mode)
        self._sb_val["model"].config(text=f"{mode} Ready")

    def _update_mode_btns(self, active: str):
        T = self.T
        for mode in ("ASL", "ISL"):
            b = getattr(self, f"_mode_btn_{mode}", None)
            if b:
                b.config(
                    bg=T.ACCENT if mode == active else T.BG_CARD3,
                    fg="#000"   if mode == active else T.TEXT2)

    def _apply_detection(self):
        try:
            self.gesture_handler.confidence_threshold = self._sc_conf.get()
            self.gesture_handler.FRAME_THRESHOLD      = int(self._sc_frames.get())
            self.gesture_handler.REPEAT_DELAY         = self._sc_interval.get()
            messagebox.showinfo("Detection", "Detection settings applied!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_settings_file(self):
        cfg = {
            "confidence_threshold": getattr(self._sc_conf, 'get', lambda: 0.8)(),
            "camera_index":         getattr(self._cam_idx_var, 'get', lambda: 0)(),
        }
        path = os.path.join(self.base_path, "config", "settings.json")
        try:
            with open(path, "w") as f:
                json.dump(cfg, f, indent=2)
            messagebox.showinfo("Settings", "Settings saved!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _start_meeting(self):
        self._meeting_active = True
        self._btn_meeting_start.config(state="disabled")
        self._btn_meeting_stop.config(state="normal")
        if not self.camera_mgr.is_running:
            self._start()

    def _stop_meeting(self):
        self._meeting_active = False
        self._btn_meeting_start.config(state="normal")
        self._btn_meeting_stop.config(state="disabled")
        self._lbl_meeting_caption.config(text="")

    def _update_caption_style(self):
        styles = {
            "White on Black":  ("#000000", "#FFFFFF"),
            "Black on White":  ("#FFFFFF", "#000000"),
            "Mint on Dark":    ("#001a0f", "#00FFB2"),
            "Yellow on Black": ("#000000", "#FFE500"),
        }
        bg, fg = styles.get(self._caption_style_var.get(), ("#000000", "#FFFFFF"))
        self._lbl_meeting_caption.config(bg=bg, fg=fg)
        self._lbl_meeting_caption.master.config(bg=bg)

    def _vs_speak_preview(self):
        text = self._vs_preview_text.get("1.0", "end").strip()
        if text:
            eng = self._vs_engine_var.get()
            self.tts.set_engine(eng)
            self.tts.speak(text)
            # Redraw waveform to simulate activity
            self.root.after(200, self._draw_waveform)

    def _vs_test_all(self):
        messagebox.showinfo("Engine Test",
            "Testing all engines in sequence...\nCheck console for results.")
        for eng in ["pyttsx3"]:
            self.tts.set_engine(eng)
            self.tts.speak(f"Testing {eng} engine.")

    # ── Hold bar animation ────────────────────────────────────────
    def _animate_hold(self):
        if not self.camera_mgr.is_running:
            self._hold_val = 0; return
        self._hold_val = (self._hold_val + 0.022) % 1.05
        pct = min(self._hold_val, 1.0)
        self._draw_bar(self._hold_canvas, "_hold_rect", pct, self.T.ACCENT4)
        self._lbl_hold.config(text=f"Hold to confirm: {int(pct*100)}%")
        if pct >= 1.0: self._hold_val = 0
        self.root.after(80, self._animate_hold)

    def _draw_bar(self, canvas, rect_attr, pct, color):
        canvas.update_idletasks()
        w  = max(canvas.winfo_width(), 80)
        fw = int(w * pct)
        if getattr(self, rect_attr) is None:
            setattr(self, rect_attr,
                    canvas.create_rectangle(0, 0, fw, 5, fill=color, outline=""))
        else:
            canvas.coords(getattr(self, rect_attr), 0, 0, fw, 5)
            canvas.itemconfig(getattr(self, rect_attr), fill=color)

    def _draw_placeholder(self):
        c = self._cam_canvas
        c.delete("all")
        c.create_text(350, 180, text="📷", font=("Segoe UI", 64), fill="#0A1420")
        c.create_text(350, 260, text="Camera is inactive",
                      font=("Segoe UI", 14), fill="#111D2E")
        c.create_text(350, 290, text='Click  "Start Translation"  to begin',
                      font=("Segoe UI", 10), fill="#0C1828")

    def _set_txt(self, text: str):
        self._txt.config(state="normal")
        self._txt.delete("1.0", "end")
        if text: self._txt.insert("1.0", text)
        self._txt.config(state="disabled")
        self._txt.see("end")

    # ── History helpers ───────────────────────────────────────────
    def _refresh_history_tree(self):
        self._hist_tree.delete(*self._hist_tree.get_children())
        for item in reversed(self._history):
            self._hist_tree.insert("", "end", values=(
                item["time"], item["words"], item["chars"], item["text"]))
        total_w = sum(h["words"] for h in self._history)
        self._lbl_hist_sum.config(
            text=f"{len(self._history)} sentences  •  {total_w} total words  •  "
                 f"Cache: {len(self._cache_sentence.split())} words in OBS file")

    def _export_history(self):
        if not self._history:
            messagebox.showwarning("Export", "No history yet."); return
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            initialfile=f"signbridge_history_{ts}.txt",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("SignBridge Pro — Session History\n")
                f.write("=" * 52 + "\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for item in self._history:
                    f.write(f"[{item['time']}]  ({item['words']} words)  {item['text']}\n")
            messagebox.showinfo("Exported", f"Saved to:\n{path}")

    def _export_history_csv(self):
        if not self._history:
            messagebox.showwarning("Export", "No history yet."); return
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            initialfile=f"signbridge_history_{ts}.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("time,words,chars,text\n")
                for item in self._history:
                    text = item["text"].replace('"', '""')
                    f.write(f"{item['time']},{item['words']},{item['chars']},\"{text}\"\n")
            messagebox.showinfo("Exported CSV", f"Saved to:\n{path}")

    def _clear_history(self):
        if messagebox.askyesno("Clear", "Clear all session history?"):
            self._history.clear()
            self._refresh_history_tree()

    # ═══════════════════════════════════════════════════════════════
    #  GUI QUEUE DRAIN
    # ═══════════════════════════════════════════════════════════════
    def _drain(self):
        try:
            while True: self._handle(self._q.get_nowait())
        except queue.Empty: pass
        self.root.after(40, self._drain)

    def _handle(self, item):
        kind = item[0]
        T    = self.T

        if kind == "frame":
            try:
                rgb  = item[1][:, :, ::-1]
                img  = Image.fromarray(rgb)
                cw   = max(self._cam_canvas.winfo_width(),  10)
                ch   = max(self._cam_canvas.winfo_height(), 10)
                img  = img.resize((cw, ch), Image.LANCZOS)
                self._photo = ImageTk.PhotoImage(img)
                self._cam_canvas.delete("all")
                self._cam_canvas.create_image(0, 0, anchor="nw", image=self._photo)
            except Exception: pass

        elif kind == "fps":
            fps = item[1]
            self._lbl_fps.config(text=f"{fps:.0f} FPS")
            self._lbl_sb_fps.config(text=f"{fps:.0f} FPS")

        elif kind == "pred":
            label, conf = item[1], item[2]
            disp = "—" if label in ("No hand", "space", "del", "nothing") else label
            self._lbl_gesture_letter.config(text=disp)
            self._lbl_gest_name.config(
                text="No gesture detected" if label == "No hand" else f"Letter  {label}")
            self._lbl_conf.config(text=f"Confidence: {int(conf*100)}%")
            clr = T.ACCENT if conf >= 0.80 else T.ACCENT4
            self._draw_bar(self._conf_canvas, "_conf_rect", conf, clr)

            # Track accuracy for analytics
            if label not in ("No hand",):
                self._acc_history.append(conf * 100)
                # Track letter frequency
                if label.upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    self._letter_counts[label.upper()] = \
                        self._letter_counts.get(label.upper(), 0) + 1

        elif kind == "word":
            word = item[1]
            self._total_words += 1
            self._words_this_minute += 1
            self._total_chars += len(word)
            self._correct_chars += len(word)  # all model-confirmed words count as correct
            try:
                self._lbl_wc.config(text=f"Words: {self.sentence_mgr.word_count}")
                self._lbl_cc.config(text=f"Chars: {self.sentence_mgr.char_count}")
            except Exception: pass

        elif kind == "sent":
            sentence = item[1]
            self._set_txt(sentence)
            try:
                self._lbl_wc.config(text=f"Words: {self.sentence_mgr.word_count}")
                self._lbl_cc.config(text=f"Chars: {self.sentence_mgr.char_count}")
            except Exception: pass
            self._tier1_update(sentence)
            if sentence.endswith((".", "।", "?", "!")):
                self._tier2_commit(sentence)
            if self._tgl.get("speak_end", tk.BooleanVar(value=True)).get():
                if sentence.endswith((".", "।", "?", "!")):
                    self.tts.speak(sentence)

        elif kind == "partial":
            p = item[1]
            self._lbl_partial.config(text=f"Building: {p}" if p else "")

        elif kind == "error":
            messagebox.showerror("SignBridge Error", item[1])

        elif kind == "stopped":
            self._btn_start.config(state="normal")
            self._btn_stop.config(state="disabled")
            try:
                self._lbl_cam_badge.config(text=" ● OFFLINE ", bg=T.ACCENT3, fg="#fff")
                self._lbl_tb_cam.config(text=" ● Camera Inactive ", bg=T.ACCENT3)
                self._sb_val["cam"].config(text="Offline", fg=T.TEXT)
                self._lbl_sb_cam.config(text="  📷 Camera: Offline", fg=T.TEXT3)
            except Exception: pass
            self._draw_placeholder()

    # ═══════════════════════════════════════════════════════════════
    #  CLOSE
    # ═══════════════════════════════════════════════════════════════
    def _on_close(self):
        if messagebox.askokcancel("Quit", "Close SignBridge Pro?"):
            self.camera_mgr.stop()
            self.obs.disconnect()
            self.root.quit()
            self.root.destroy()