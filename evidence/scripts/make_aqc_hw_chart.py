"""deck/fig_aqc_hw.png -- the AQC three-arm hardware result, once the jobs land.
Reads evidence/aqc_hw_result.json (written by aqc_hardware_fetch.py); numbers never typed in.
Safe to run before results exist: it exits with a message instead of drawing an empty chart.
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
ARM_LABEL = {"exact": "exact block", "trotter": "Trotter $r{=}2$", "aqc": "AQC $+$ phase fix"}
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
fig, axes = plt.subplots(1, nb + 1, figsize=(6.2 * (nb + 1) * 0.62, 4.4),
                         gridspec_kw={"width_ratios": [1.15] * nb + [1]})
axes = np.atleast_1d(axes)

# ---- per-backend |chi(t)|: measured vs exact ----
for ax, (bname, arms) in zip(axes[:nb], R.items()):
    ts = TIMES
    ax.plot(ts, [abs(EXACT[t]) for t in ts], "-", color=COL["ink"], lw=2.6, label="exact")
    for arm in ARMS:
        ys = [r["abs_measured"] for r in arms[arm]["rows"]]
        n2 = arms[arm]["prediction"]["median_2q"]
        ax.plot(ts, ys, "o--", color=ARM_COL[arm], lw=2.0, ms=8,
                label=f"{ARM_LABEL[arm]} ({n2:.0f} 2q)")
    ax.set_xlabel("time $t$"); ax.set_ylabel(r"$|\chi(t)|$")
    ax.set_ylim(-0.05, 1.1)
    ax.set_title(bname.replace("ibm_", "ibm\\_") if "_" in bname else bname, fontsize=12.5)
    ax.legend(frameon=False, fontsize=9)
    style(ax)

# ---- predicted vs measured survival, all backends ----
ax = axes[-1]
x = np.arange(len(ARMS))
w = 0.8 / (2 * nb)
for bi, (bname, arms) in enumerate(R.items()):
    pred = [arms[a]["prediction"]["predicted_survival"] for a in ARMS]
    meas = [arms[a]["mean_survival"] for a in ARMS]
    ax.bar(x + (2 * bi) * w - 0.4 + w / 2, pred, w, color=COL["muted"], alpha=0.55,
           label=f"predicted ({bname.split('_')[-1]})" if bi == 0 else None)
    ax.bar(x + (2 * bi + 1) * w - 0.4 + w / 2, meas, w,
           color=[ARM_COL[a] for a in ARMS],
           label=f"measured" if bi == 0 else None)
ax.set_xticks(x); ax.set_xticklabels([ARM_LABEL[a] for a in ARMS], fontsize=9.5)
ax.set_ylabel(r"mean $|\chi|$ survival")
ax.set_title("Predicted before submission vs measured", fontsize=12)
ax.legend(frameon=False, fontsize=9)
style(ax)

fig.tight_layout()
fig.savefig(os.path.join(REPO, "deck/fig_aqc_hw.png"), dpi=200, bbox_inches="tight",
            facecolor=BG)
print("wrote deck/fig_aqc_hw.png for backends:", ", ".join(R))
