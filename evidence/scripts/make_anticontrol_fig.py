"""deck/fig_tb_anticontrol.png -- what "anti-control" is, and how it extends the Hadamard test.

Pedagogical schematic, not data. The circuit drawn is exactly the one
track_b_hardware_submit.build() constructs.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Wedge

COL = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "violet": "#4a3aa7",
       "ink": "#0b0b0b", "muted": "#898781", "grid": "#e1e0d9"}
BG = "#fcfcfb"
plt.rcParams.update({"figure.facecolor": BG, "savefig.facecolor": BG})

XLO, XHI, YLO, YHI = 0.0, 12.6, 0.0, 6.35
FW, FH = 13.0, 6.55
fig, ax = plt.subplots(figsize=(FW, FH))
ax.set_xlim(XLO, XHI); ax.set_ylim(YLO, YHI); ax.axis("off"); ax.set_facecolor(BG)
ASP = (FW / (XHI - XLO)) / (FH / (YHI - YLO))

BW, BH = 0.52, 0.40


def box(x, y, label, color=COL["ink"], w=BW, fs=12.5, fill="white"):
    ax.add_patch(Rectangle((x - w / 2, y - BH / 2), w, BH, facecolor=fill,
                           edgecolor=color, lw=2.0, zorder=4))
    ax.text(x, y, label, ha="center", va="center", fontsize=fs, color=color, zorder=5)


def meter(x, y):
    ax.add_patch(Rectangle((x - 0.26, y - BH / 2), 0.52, BH, facecolor="white",
                           edgecolor=COL["ink"], lw=1.8, zorder=4))
    ax.add_patch(Wedge((x, y - 0.09), 0.15, 20, 160, width=0.035, facecolor=COL["ink"],
                       zorder=5))
    ax.plot([x, x + 0.10], [y - 0.09, y + 0.10], color=COL["ink"], lw=1.3, zorder=5)


def ctrl(x, ya, ys, color):
    ax.plot([x, x], [ya, ys], color=color, lw=2.0, zorder=3)
    ax.add_patch(plt.Circle((x, ya), 0.075 / ASP * ASP, color=color, zorder=6))


def wire(y, x0, x1):
    ax.plot([x0, x1], [y, y], color=COL["ink"], lw=1.4, zorder=1)


def trash(x, y):
    ax.add_patch(Rectangle((x - 0.17, y - 0.19), 0.34, 0.34, facecolor="white",
                           edgecolor=COL["orange"], lw=1.8, zorder=4))
    for dx in (-0.06, 0, 0.06):
        ax.plot([x + dx, x + dx], [y - 0.10, y + 0.07], color=COL["orange"], lw=1.4, zorder=5)
    ax.plot([x - 0.21, x + 0.21], [y + 0.15, y + 0.15], color=COL["orange"], lw=2, zorder=5)


# ==================== TOP: the standard Hadamard test ====================
YA, YS = 5.62, 4.80
ax.text(0.05, 6.25, "Standard Hadamard test", fontsize=14, weight="bold",
        color=COL["ink"], va="top")
wire(YA, 0.95, 6.55); wire(YS, 0.95, 6.05)
ax.text(0.80, YA, r"$|0\rangle_a$", ha="right", va="center", fontsize=12.5)
ax.text(0.80, YS, r"$|\psi\rangle$", ha="right", va="center", fontsize=12.5)
box(1.45, YA, "$H$")
ctrl(2.45, YA, YS, COL["ink"]); box(2.45, YS, "$U$", COL["violet"], w=0.62)
box(3.55, YA, r"$P(\phi)$", COL["aqua"], w=0.80, fs=11.5)
box(4.55, YA, "$H$")
meter(5.55, YA)
trash(5.55, YS)
ax.text(6.85, YA, r"$\langle Z_a\rangle_\phi=\mathrm{Re}\!\left[e^{i\phi}"
                  r"\langle\psi|U|\psi\rangle\right]$", va="center", fontsize=12.5,
        color=COL["ink"])
ax.text(6.85, YS, "the system register is discarded", va="center", fontsize=11,
        color=COL["orange"])

ax.plot([0.05, 12.5], [4.25, 4.25], color=COL["grid"], lw=1.6)

# ==================== BOTTOM: Track B ====================
YA2, YS2 = 3.55, 2.73
ax.text(0.05, 4.10, "Track B: the anti-controlled (extended) Hadamard test",
        fontsize=14, weight="bold", color=COL["ink"], va="top")
wire(YA2, 0.95, 8.35); wire(YS2, 0.95, 8.35)
ax.text(0.80, YA2, r"$|0\rangle_a$", ha="right", va="center", fontsize=12.5)
ax.text(0.80, YS2, r"$|\psi\rangle$", ha="right", va="center", fontsize=12.5)

box(1.45, YA2, "$H$")
# the anti-control sandwich
ax.add_patch(FancyBboxPatch((2.02, YS2 - 0.32), 1.66, 1.24,
                            boxstyle="round,pad=0.06", facecolor="#fdf0e9",
                            edgecolor=COL["orange"], lw=1.8, zorder=0))
box(2.30, YA2, "$X$", COL["orange"])
ctrl(2.85, YA2, YS2, COL["ink"]); box(2.85, YS2, "$W$", COL["blue"], w=0.62)
box(3.40, YA2, "$X$", COL["orange"])
ax.text(2.85, YS2 - 0.52, "anti-control", ha="center", va="top", fontsize=11.5,
        color=COL["orange"], weight="bold")

ctrl(4.35, YA2, YS2, COL["ink"]); box(4.35, YS2, "$U$", COL["violet"], w=0.62)
box(5.30, YA2, r"$P(\phi)$", COL["aqua"], w=0.80, fs=11.5)
ax.add_patch(Rectangle((6.30 - BW / 2, YA2 - BH / 2), BW, BH, facecolor="white",
                       edgecolor=COL["orange"], lw=2.0, ls=(0, (3, 2)), zorder=4))
ax.text(6.30, YA2, "$H$", ha="center", va="center", fontsize=12.5, color=COL["orange"],
        zorder=5)
box(6.30, YS2, "$V_{b}$", COL["aqua"], w=0.62)
ax.text(6.30, YS2 - 0.30, "random basis", ha="center", va="top", fontsize=10,
        color=COL["aqua"])
meter(7.55, YA2); meter(7.55, YS2)

ax.text(8.70, YA2 + 0.16,
        r"$\langle Z_a\rangle_\phi=\mathrm{Re}\!\left[e^{i\phi}"
        r"\langle\psi|W^{\dagger}U|\psi\rangle\right]$", va="center", fontsize=12.5)
ax.text(8.70, YS2 + 0.02, "the register is now a classical shadow", va="center",
        fontsize=11, color=COL["aqua"])
ax.text(8.70, YS2 - 0.42, "dashed $H$: delete it for arm B\n"
        "($X$-basis readout $\\Rightarrow$ the difference)", va="center",
        fontsize=10.5, color=COL["orange"])

# ==================== the two explanations ====================
ax.plot([0.05, 12.5], [2.00, 2.00], color=COL["grid"], lw=1.6)

ax.text(0.05, 1.83, "Why the two $X$ gates:", fontsize=12.5, weight="bold",
        color=COL["orange"], va="top")
ax.text(0.05, 1.42,
        r"$X_a\left(|0\rangle\langle 0|\otimes I+|1\rangle\langle 1|\otimes W\right)X_a"
        r"=|1\rangle\langle 1|\otimes I+|0\rangle\langle 0|\otimes W$",
        fontsize=12.5, va="top", color=COL["ink"])
ax.text(0.05, 0.88, "Conjugating by $X$ swaps which ancilla state fires the gate, so $W$ acts on\n"
                    "the $|0\\rangle$ branch and $U$ on the $|1\\rangle$ branch. Nothing else changes.",
        fontsize=11, va="top", color=COL["muted"])

ax.text(6.95, 1.83, "What the ancilla then sees:", fontsize=12.5, weight="bold",
        color=COL["blue"], va="top")
ax.text(6.95, 1.40,
        r"$\frac{1}{\sqrt{2}}\left(|0\rangle\,W|\psi\rangle"
        r"+e^{i\phi}|1\rangle\,U|\psi\rangle\right)$",
        fontsize=13, va="top", color=COL["ink"])
ax.text(6.95, 0.88, "Two dynamics interfering on one ancilla. $W=I$ gives back the\n"
                    "standard test exactly, so this is a strict generalisation.",
        fontsize=11, va="top", color=COL["muted"])

fig.savefig(os.path.join(REPO, "deck/fig_tb_anticontrol.png"), dpi=200,
            bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_tb_anticontrol.png")
