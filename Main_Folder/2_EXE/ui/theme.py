"""
ui/theme.py — SignBridge Pro v3.0
Vibrant, high-contrast dark theme. Deep navy base with electric accents.
"""


class Theme:
    # ── BASE PALETTE ────────────────────────────────────────────
    BG_BASE     = "#080D14"    # deep space black
    BG_CARD     = "#0F1724"    # card surface
    BG_CARD2    = "#162033"    # elevated card
    BG_CARD3    = "#1C2940"    # hover state
    BG_INPUT    = "#0D1929"    # input fields

    # ── ACCENT COLOURS ───────────────────────────────────────────
    ACCENT      = "#00FFB2"    # electric mint — primary
    ACCENT_DIM  = "#00B87A"    # dimmed mint
    ACCENT2     = "#7B61FF"    # vivid violet — secondary
    ACCENT2_DIM = "#5546CC"
    ACCENT3     = "#FF4D6A"    # hot pink-red — danger/stop
    ACCENT4     = "#FFB020"    # golden amber — warning
    ACCENT5     = "#00C8FF"    # cyan — info / voice
    ACCENT6     = "#FF6B2B"    # orange — meeting

    # ── GRAPH COLOURS ────────────────────────────────────────────
    GRAPH_1     = "#00FFB2"
    GRAPH_2     = "#7B61FF"
    GRAPH_3     = "#00C8FF"
    GRAPH_4     = "#FFB020"
    GRAPH_5     = "#FF4D6A"

    # ── TEXT ─────────────────────────────────────────────────────
    TEXT        = "#E4EBF5"
    TEXT2       = "#6B7FA3"
    TEXT3       = "#2E3D5C"
    TEXT_ACCENT = "#00FFB2"

    # ── BORDERS / DIVIDERS ───────────────────────────────────────
    BORDER      = "#162033"
    BORDER2     = "#1E3050"
    GLOW        = "#00FFB230"  # semi-transparent mint glow

    # ── SIDEBAR ──────────────────────────────────────────────────
    SIDEBAR_BG  = "#080D14"
    SIDEBAR_W   = 240

    # ── FONTS ────────────────────────────────────────────────────
    F_DISPLAY   = ("Segoe UI", 28, "bold")
    F_TITLE     = ("Segoe UI", 18, "bold")
    F_H1        = ("Segoe UI", 15, "bold")
    F_H2        = ("Segoe UI", 12, "bold")
    F_BODY      = ("Segoe UI", 11)
    F_SMALL     = ("Segoe UI", 9)
    F_MONO      = ("Cascadia Code", 10)
    F_MONO2     = ("Consolas", 10)
    F_GESTURE   = ("Segoe UI", 44, "bold")
    F_BIG       = ("Segoe UI", 32, "bold")

    # ── BUTTON STYLE DICTS ───────────────────────────────────────
    BTN_PRIMARY = dict(
        bg="#00FFB2", fg="#040A12",
        font=("Segoe UI", 12, "bold"),
        padx=22, pady=11, relief="flat", cursor="hand2", bd=0,
        activebackground="#00E8A0", activeforeground="#040A12",
    )
    BTN_DANGER = dict(
        bg="#FF4D6A", fg="#FFFFFF",
        font=("Segoe UI", 12, "bold"),
        padx=22, pady=11, relief="flat", cursor="hand2", bd=0,
        activebackground="#E03058", activeforeground="#FFFFFF",
    )
    BTN_PURPLE = dict(
        bg="#7B61FF", fg="#FFFFFF",
        font=("Segoe UI", 11, "bold"),
        padx=18, pady=9, relief="flat", cursor="hand2", bd=0,
        activebackground="#6450E8", activeforeground="#FFFFFF",
    )
    BTN_CYAN = dict(
        bg="#00C8FF", fg="#040A12",
        font=("Segoe UI", 11, "bold"),
        padx=18, pady=9, relief="flat", cursor="hand2", bd=0,
        activebackground="#00B0E0", activeforeground="#040A12",
    )
    BTN_ORANGE = dict(
        bg="#FF6B2B", fg="#FFFFFF",
        font=("Segoe UI", 11, "bold"),
        padx=18, pady=9, relief="flat", cursor="hand2", bd=0,
        activebackground="#E85A20", activeforeground="#FFFFFF",
    )
    BTN_GHOST = dict(
        bg="#162033", fg="#6B7FA3",
        font=("Segoe UI", 11, "bold"),
        padx=16, pady=9, relief="flat", cursor="hand2", bd=0,
        activebackground="#1C2940", activeforeground="#E4EBF5",
    )
    BTN_GHOST_SM = dict(
        bg="#162033", fg="#6B7FA3",
        font=("Segoe UI", 10, "bold"),
        padx=12, pady=7, relief="flat", cursor="hand2", bd=0,
        activebackground="#1C2940", activeforeground="#E4EBF5",
    )
