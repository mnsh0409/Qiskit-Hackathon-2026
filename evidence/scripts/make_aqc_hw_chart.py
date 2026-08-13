"""deck/fig_aqc_hw.png -- the AQC three-arm hardware result.

Reads evidence/aqc_hw_result.json (written by aqc_hardware_fetch.py); numbers never typed in.
Safe to run before results exist: exits with a message rather than drawing an empty chart.

The y-limit deliberately extends past 1: the exact-block arm returns |chi| = 1.21, which is
ABOVE the physical bound |chi| <= 1. Clipping it to [0,1] would hide the single most
important feature of this run -- that its apparent "survival" is a T1 relaxation floor
rather than preserved signal.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

path = os.path.join(REPO, "evidence/aqc_hw_result.json")
if not os.path.exists(path):
    print("no results yet -- run aqc_hardware_fetch.py first"); sys.exit(0)
R = json.load(open(path))
JOB = json.load(open(os.path.join(REPO, "evidence/aqc_hw_job.json")))
TIMES = JOB["times"]
EXACT = {t: complex(*JOB["chi_exact"][str(t)]) for t in TIMES}

COL = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "violet": "#4a3aa7",
       "ink": "#0b0b0b", "muted": "#898781", "grid": "#e1e0d9"}
BG = "#fcfcfb"
plt.rcParams.update({"figure.facecolor": BG, "savefig.facecolor": BG, "font.size": 12})
ARMS = ["exact", "trotter", "aqc"]
LBL = {"exact": "exact block", "trotter": "Trotter $r{=}2$", "aqc": "AQC $+$ phase fix"}
ARM_COL = {"exact": COL["orange"], "trotter": COL["muted"], "aqc": COL["blue"]}


def style(ax):
    ax.set_facecolor(BG)
    ax.grid(True, axis="y", color=COL["grid"], lw=0.9); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(COL["muted"])
    ax.tick_params(colors=COL["muted"], labelsize=11)
    ax.yaxis.label.set_color(COL["ink"]); ax.title.set_color(COL["ink"])


nb = len(R)
fig, axes = plt.subplots(1, nb + 1, figsize=(6.4 + 5.6 * nb, 4.6))
axes = np.atleast_1d(axes)

for ax, (bname, arms) in zip(axes[:nb], R.items()):
    ax.axhline(1.0, color=COL["ink"], ls=":", lw=1.6)
    ax.text(TIMES[0], 1.04, r"physical bound  $|\chi|\leq 1$", fontsize=10,
            color=COL["ink"], va="bottom")
    ax.plot(TIMES, [abs(EXACT[t]) for t in TIMES], "-", color=COL["ink"], lw=2.8,
            label="exact (what a working run gives)")
    for arm in ARMS:
        ys = [r["abs_measured"] for r in arms[arm]["rows"]]
        n2 = arms[arm]["prediction"]["median_2q"]
        ax.plot(TIMES, ys, "o--", color=ARM_COL[arm], lw=2.0, ms=8,
                label=f"{LBL[arm]}  ({n2:.0f} 2q)")
    ax.annotate("above the physical bound:\n$T_1$ relaxation floor, not signal",
                (TIMES[1], arms["exact"]["rows"][1]["abs_measured"]),
                xytext=(6, 18), textcoords="offset points", fontsize=10,
                color=COL["orange"],
                arrowprops=dict(arrowstyle="->", color=COL["orange"], lw=1.6))
    ax.set_xlabel("time $t$"); ax.set_ylabel(r"$|\chi(t)|$")
    ax.set_ylim(-0.06, 1.62)
    ax.set_title(bname.replace("_", " "), fontsize=12.5)
    # the band between the dead arms (~0.03) and the exact curve (~0.85) is the only
    # empty region on this panel
    ax.legend(frameon=False, fontsize=9.5, loc="center left",
              bbox_to_anchor=(0.0, 0.34))
    style(ax)

ax = axes[-1]
# One group per arm, 2 bars per backend (predicted, measured). A first version drew every
# backend at the SAME offsets, so the bars and their labels stacked on top of each other.
x = np.arange(len(ARMS))
nser = 2 * nb
w = 0.82 / nser
HATCH = ["", "//"]
for bi, (bname, arms) in enumerate(R.items()):
    short = bname.split("_")[-1]
    pred = [arms[a]["prediction"]["predicted_survival"] for a in ARMS]
    meas = [arms[a]["mean_survival"] for a in ARMS]
    xp = x - 0.41 + (2 * bi) * w + w / 2
    xm = x - 0.41 + (2 * bi + 1) * w + w / 2
    ax.bar(xp, pred, w, color=COL["muted"], alpha=0.45, hatch=HATCH[bi % 2],
           edgecolor="white", label=f"predicted ({short})")
    ax.bar(xm, meas, w, color=[ARM_COL[a] for a in ARMS], hatch=HATCH[bi % 2],
           edgecolor="white", label=f"measured ({short})")
    for xi, m in zip(xm, meas):
        ax.annotate(f"{m:.3g}", (xi, m), xytext=(0, 3), textcoords="offset points",
                    ha="center", fontsize=8.5, weight="bold", color=COL["ink"])
ax.axhline(1.0, color=COL["ink"], ls=":", lw=1.4)
ax.text(-0.45, 1.03, r"$|\chi|\leq 1$", fontsize=9.5, color=COL["ink"], va="bottom")
ax.set_xticks(x)
ax.set_xticklabels(["exact\nblock", "Trotter\n$r{=}2$", "AQC $+$\nphase fix"], fontsize=10.5)
ax.set_ylabel(r"mean $|\chi|$ survival"); ax.set_ylim(0, 1.85)
ax.set_title("Predicted before submission vs measured", fontsize=12.5)
ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper center")
style(ax)

fig.tight_layout()
fig.savefig(os.path.join(REPO, "deck/fig_aqc_hw.png"), dpi=200, bbox_inches="tight",
            facecolor=BG)
print("wrote deck/fig_aqc_hw.png for:", ", ".join(R))
