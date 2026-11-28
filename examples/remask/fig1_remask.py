#!/usr/bin/env python3
"""Figure 1 for "Remask, Don't Regret": standard MDLM sampling vs. ReMask.

Layout adapted from Figure 1 of "Soft-Masked Diffusion Language Models"
(ICLR 2026, arXiv 2510.17206): two token grids side by side, rows = sampling steps.

Run:  python3 fig1_remask.py      ->  fig1_remask.pdf, fig1_remask.png (same folder)

Everything you are likely to change is in the EDIT block below.
All coordinates are in inches (the axes span the whole figure).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

# ----------------------------------------------------------------------------- EDIT
# Token states: "mask", "tok" (unmasked), "wrong" (unmasked, incorrect),
#               "remask" (being re-masked this step), "fixed" (re-predicted, correct)
M = ("[M]", "mask")


def t(word, state="tok"):
    return (word, state)


STEP_LABELS = ["0", "1", "2", "3", "T"]

# Placeholder sentence: replace with a real sample from your runs.
ROWS_BASELINE = [
    [M, M, M, M, M, M, M, M],
    [t("The"), t("chef"), t("flew", "wrong"), M, M, M, M, M],
    [t("The"), t("chef"), t("flew", "wrong"), t("the"), t("pasta"), M, M, M],
    [t("The"), t("chef"), t("flew", "wrong"), t("the"), t("pasta"), t("in"), t("a"), M],
    [t("The"), t("chef"), t("flew", "wrong"), t("the"), t("pasta"), t("in"), t("a"), t("pot")],
]
ROWS_REMASK = [
    [M, M, M, M, M, M, M, M],
    [t("The"), t("chef"), t("flew"), M, M, M, M, M],
    [t("The"), t("chef"), t("flew", "remask"), t("the"), t("pasta"), M, M, M],
    [t("The"), t("chef"), t("cooked", "fixed"), t("the"), t("pasta"), t("in"), M, M],
    [t("The"), t("chef"), t("cooked", "fixed"), t("the"), t("pasta"), t("in"), t("a"), t("pot")],
]

# Posterior-confidence bars drawn under one row of panel (b). Illustrative heights
# in [0, 1], one per unmasked token in that row; swap in real model posteriors.
CONF_ROW = 2
CONF = [0.95, 0.90, 0.12, 0.93, 0.85]

TITLE_A = "(a) Standard MDLM sampling: unmask, then frozen"
TITLE_B = "(b) ReMask (ours): score, re-mask, re-predict"
NOTE_A = "The early error is never revised; later tokens condition on it."
NOTE_B = "The same frozen model re-predicts the token with richer context."

# Bottom strip: (small label, headline value). Numbers are from the abstract.
STATS = [
    ("Network evaluations", "same as baseline"),
    ("Gen. PPL, OpenWebText, 64 steps", "42.1 → 27.8"),
    ("pass@1, code infilling", "31% → 44%"),
]
BUDGET_LABEL = "Re-mask budget $k_t$\ndecays linearly to 0"

# Colors. Text always uses the ink colors; state is carried by fill, border and a glyph.
INK, INK2 = "#191919", "#666666"
RED, GREEN, BLUE = "#dc3c3d", "#0aac23", "#84b9f3"
STYLE = {  # state: (fill, edge, linestyle, linewidth)
    "mask": ("#efefef", "#d0d0d0", "-", 0.6),
    "tok": ("#e8f2fe", BLUE, "-", 0.6),
    "wrong": ("#fbe3e3", RED, "-", 0.9),
    "remask": ("#efefef", RED, (0, (2, 1.2)), 0.9),
    "fixed": ("#dff3e2", GREEN, "-", 0.9),
}
GLYPH = {"wrong": ("✗", RED), "remask": ("↺", RED), "fixed": ("✓", GREEN)}

# Geometry (inches).
FIG_W, FIG_H = 7.2, 3.45
BOX_W, BOX_H, COL_GAP = 0.365, 0.24, 0.035
ROW_PITCH = 0.40
PANEL_X = (0.36, 3.92)  # left edge of each grid
TOP_Y = 2.82            # bottom edge of the first row
FS_TOK, FS_SMALL, FS_TITLE = 6.4, 6.2, 7.6
# ----------------------------------------------------------------------------- /EDIT

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def box_xy(x0, col, row):
    return x0 + col * (BOX_W + COL_GAP), TOP_Y - row * ROW_PITCH


def draw_token(ax, x, y, word, state):
    fill, edge, ls, lw = STYLE[state]
    ax.add_patch(FancyBboxPatch(
        (x, y), BOX_W, BOX_H, boxstyle="round,pad=0,rounding_size=0.035",
        fc=fill, ec=edge, ls=ls, lw=lw, zorder=2))
    color = INK2 if state in ("mask", "remask") else INK
    cx, cy = x + BOX_W / 2, y + BOX_H / 2
    ax.text(cx, cy, word, ha="center", va="center", fontsize=FS_TOK, color=color, zorder=3)
    if state == "remask":  # strike the token that is being re-masked
        half = 0.028 * len(word) + 0.02
        ax.plot([cx - half, cx + half], [cy, cy], color=RED, lw=0.8, zorder=4)
    if state in GLYPH:  # status glyph on the top-right corner, so color is never alone
        g, c = GLYPH[state]
        ax.text(x + BOX_W - 0.005, y + BOX_H + 0.002, g, ha="center", va="center",
                fontsize=FS_TOK + 1.2, color=c, fontweight="bold", zorder=5,
                bbox=dict(boxstyle="circle,pad=0.08", fc="white", ec="none"))


def draw_grid(ax, x0, rows, title, note):
    ncol = len(rows[0])
    width = ncol * BOX_W + (ncol - 1) * COL_GAP
    ax.text(x0, TOP_Y + BOX_H + 0.13, title, ha="left", va="bottom",
            fontsize=FS_TITLE, color=INK, fontweight="bold")
    for r, row in enumerate(rows):
        for c, (word, state) in enumerate(row):
            draw_token(ax, *box_xy(x0, c, r), word, state)
        ax.text(x0 - 0.07, TOP_Y - r * ROW_PITCH + BOX_H / 2, STEP_LABELS[r],
                ha="right", va="center", fontsize=FS_SMALL, color=INK2)
    y_last = TOP_Y - (len(rows) - 1) * ROW_PITCH
    ax.text(x0 + width / 2, y_last - 0.11, note, ha="center", va="top",
            fontsize=FS_SMALL, color=INK2, style="italic")
    return width


def main():
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    xa, xb = PANEL_X
    width = draw_grid(ax, xa, ROWS_BASELINE, TITLE_A, NOTE_A)
    draw_grid(ax, xb, ROWS_REMASK, TITLE_B, NOTE_B)
    n_rows = len(ROWS_BASELINE)
    y_last = TOP_Y - (n_rows - 1) * ROW_PITCH

    # Step axis: one arrow on the far left, shared by both grids.
    ax.annotate("", xy=(0.12, y_last), xytext=(0.12, TOP_Y + BOX_H),
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.8))
    ax.text(0.065, (TOP_Y + BOX_H + y_last) / 2, "sampling step", rotation=90,
            ha="center", va="center", fontsize=FS_SMALL, color=INK2)

    # (a) red connector through the frozen wrong token, plus a "frozen" tag.
    wrong = [(r, c) for r, row in enumerate(ROWS_BASELINE)
             for c, (_, s) in enumerate(row) if s == "wrong"]
    for (r0, c0), (r1, _) in zip(wrong, wrong[1:]):
        x, y0 = box_xy(xa, c0, r0)
        _, y1 = box_xy(xa, c0, r1)
        ax.plot([x + BOX_W / 2] * 2, [y0, y1 + BOX_H], color=RED, lw=1.0, zorder=1)
    if wrong:
        r0, c0 = wrong[0]
        x, y = box_xy(xa, c0, r0)
        ax.text(x + BOX_W / 2 + 0.05, y - (ROW_PITCH - BOX_H) / 2, "frozen",
                ha="left", va="center", fontsize=FS_SMALL, color=INK2)

    # (b) posterior-confidence bars under the scored row.
    gap = ROW_PITCH - BOX_H
    cols = [c for c, (_, s) in enumerate(ROWS_REMASK[CONF_ROW]) if s != "mask"]
    low = min(range(len(CONF)), key=CONF.__getitem__)
    for i, (c, v) in enumerate(zip(cols, CONF)):
        x, y = box_xy(xb, c, CONF_ROW)
        base = y - 0.075
        ax.add_patch(Rectangle((x + 0.04, base), BOX_W - 0.08, 0.035, fc="#efefef", ec="none"))
        ax.add_patch(Rectangle((x + 0.04, base), (BOX_W - 0.08) * v, 0.035,
                               fc=RED if i == low else "#2370cd", ec="none"))
    x_txt, y_row = box_xy(xb, cols[-1] + 1, CONF_ROW)
    ax.text(x_txt + 0.02, y_row - 0.058, "low confidence \u2192 re-mask",
            ha="left", va="center", fontsize=FS_SMALL - 0.2, color=INK2)

    # Legend for token states.
    y_leg = y_last - 0.56
    items = [("[M]", "mask", "masked"), ("tok", "tok", "unmasked"), ("tok", "wrong", "wrong, kept"),
             ("tok", "remask", "re-masked"), ("tok", "fixed", "corrected")]
    x = xa + 0.55
    for word, state, label in items:
        draw_token(ax, x, y_leg, word, state)
        ax.text(x + BOX_W + 0.07, y_leg + BOX_H / 2, label, ha="left", va="center",
                fontsize=FS_SMALL, color=INK)
        x += 1.27

    # Bottom strip: budget schedule + headline numbers.
    y_div = y_leg - 0.14
    ax.plot([xa, xb + width], [y_div, y_div], color="#d0d0d0", lw=0.6)
    strip_top = y_div - 0.10
    n_bars, bw, bh = 8, 0.05, 0.30
    for i in range(n_bars):  # schematic k_t: linear decay to 0
        h = bh * (1 - i / (n_bars - 1))
        ax.add_patch(Rectangle((xa + i * (bw + 0.02), strip_top - bh), bw, max(h, 0.008),
                               fc="#2370cd", ec="none"))
    ax.text(xa + n_bars * (bw + 0.02) + 0.06, strip_top - bh / 2, BUDGET_LABEL,
            ha="left", va="center", fontsize=FS_SMALL, color=INK, linespacing=1.3)
    x_stats = [2.18, 3.92, 5.92]
    for xs, (label, value) in zip(x_stats, STATS):
        ax.text(xs, strip_top - 0.02, label, ha="left", va="top", fontsize=FS_SMALL, color=INK2)
        ax.text(xs, strip_top - bh - 0.02, value, ha="left", va="bottom", fontsize=9.5,
                color=INK, fontweight="bold")

    out = Path(__file__).resolve().parent
    fig.savefig(out / "fig1_remask.pdf")
    fig.savefig(out / "fig1_remask.png", dpi=300)
    print("wrote", out / "fig1_remask.pdf")
    print("wrote", out / "fig1_remask.png")


if __name__ == "__main__":
    main()
