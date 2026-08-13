"""deck/fig_skqd_boundary.png -- where SKQD helps, and where our benchmark sits.
Numbers read from evidence/skqd_geometry.json, never typed in.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import NullFormatter, NullLocator

COL = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "violet": "#4a3aa7",
       "ink": "#0b0b0b", "muted": "#898781", "grid": "#e1e0d9"}
BG = "#fcfcfb"
plt.rcParams.update({"figure.facecolor": BG, "savefig.facecolor": BG, "font.size": 12})
D = json.load(open(os.path.join(REPO, "evidence/skqd_geometry.json")))
ROWS, SEC = D["rows"], D["sector_dim"]
RATIOS = sorted({r["delta_over_J"] for r in ROWS})
GEOMS = ["1D chain (11 bonds)", "2D grid 3x4 (17 bonds)"]
STYLE = {GEOMS[0]: ("o-", COL["blue"]), GEOMS[1]: ("s--", COL["orange"])}
CAP = 1.0     # "never converged" is plotted at 100% of the sector, and labelled as such


def style(ax):
    ax.set_facecolor(BG)
    ax.grid(True, axis="y", color=COL["grid"], lw=0.9); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(COL["muted"])
    ax.tick_params(colors=COL["muted"], labelsize=11)
    ax.yaxis.label.set_color(COL["ink"]); ax.title.set_color(COL["ink"])


fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 4.5))

# ---------- left: subspace fraction needed ----------
for g in GEOMS:
    mk, c = STYLE[g]
    ys, miss = [], []
    for rt in RATIOS:
        r = next(x for x in ROWS if x["geometry"] == g and x["delta_over_J"] == rt)
        ys.append(r["frac"] if r["frac"] else CAP)
        miss.append(r["frac"] is None)
    a1.plot(RATIOS, ys, mk, color=c, lw=2.6, ms=9, label=g.replace(" 3x4", ""))
    for rt, y, m in zip(RATIOS, ys, miss):
        if m:
            a1.annotate("never", (rt, y), textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=10, color=c, weight="bold")
a1.set_xscale("log"); a1.set_xticks(RATIOS)
a1.set_xticklabels([f"{r:g}" for r in RATIOS])
a1.xaxis.set_minor_locator(NullLocator()); a1.xaxis.set_minor_formatter(NullFormatter())
a1.set_ylim(0, 1.18)
a1.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
a1.set_yticklabels(["0", "25%", "50%", "75%", "100%"])
a1.set_xlabel(r"$\Delta/J$   (larger $=$ Ising-like $=$ localised)")
a1.set_ylabel("sector fraction needed")
a1.set_title(r"How much of the sector SKQD needs", fontsize=12.5)
a1.axvline(0.38, color=COL["aqua"], ls=":", lw=2)
a1.annotate("our benchmark\n$\\Delta/J=0.38$", (0.38, 0.30), xytext=(14, 0),
            textcoords="offset points", fontsize=10.5, color=COL["aqua"], va="center")
a1.legend(frameon=False, fontsize=10.5, loc="lower left")
style(a1)

# ---------- right: why -- ground-state concentration ----------
for g in GEOMS:
    mk, c = STYLE[g]
    ys = [next(x for x in ROWS if x["geometry"] == g
               and x["delta_over_J"] == rt)["ground_90pct_frac"] for rt in RATIOS]
    a2.plot(RATIOS, ys, mk, color=c, lw=2.6, ms=9, label=g.replace(" 3x4", ""))
a2.set_xscale("log"); a2.set_xticks(RATIOS)
a2.set_xticklabels([f"{r:g}" for r in RATIOS])
a2.xaxis.set_minor_locator(NullLocator()); a2.xaxis.set_minor_formatter(NullFormatter())
a2.set_xlabel(r"$\Delta/J$")
a2.set_ylabel("fraction holding 90% of the ground state")
a2.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
a2.set_yticklabels(["0", "10%", "20%", "30%", "40%", "50%"])
a2.set_title("Why: how spread out the ground state is", fontsize=12.5)
a2.axvline(0.38, color=COL["aqua"], ls=":", lw=2)
a2.legend(frameon=False, fontsize=10.5)
style(a2)
a2.text(0.98, 0.94, "more bonds $\\Rightarrow$ more delocalised,\nbut only where hopping wins",
        transform=a2.transAxes, ha="right", va="top", fontsize=10, color=COL["muted"])

fig.tight_layout()
fig.savefig(os.path.join(REPO, "deck/fig_skqd_boundary.png"), dpi=200,
            bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_skqd_boundary.png")
