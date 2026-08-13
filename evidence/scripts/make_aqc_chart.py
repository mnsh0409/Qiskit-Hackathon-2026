"""deck/fig_aqc_scaling.png -- the AQC crossover and the phase trap.
Numbers read from evidence/aqc_scaling.json, never typed in.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COL = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "violet": "#4a3aa7",
       "ink": "#0b0b0b", "muted": "#898781", "grid": "#e1e0d9"}
BG = "#fcfcfb"
plt.rcParams.update({"figure.facecolor": BG, "savefig.facecolor": BG, "font.size": 12})
D = json.load(open(os.path.join(REPO, "evidence/aqc_scaling.json")))["rows"]
NS = [r["n"] for r in D]


def style(ax):
    ax.set_facecolor(BG)
    ax.grid(True, axis="y", color=COL["grid"], lw=0.9); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(COL["muted"])
    ax.tick_params(colors=COL["muted"], labelsize=11)
    ax.yaxis.label.set_color(COL["ink"]); ax.title.set_color(COL["ink"])


fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 4.6),
                             gridspec_kw={"width_ratios": [1.15, 1]})

# ---------- left: the crossover ----------
a1.plot(NS, [r["exact_cx"] for r in D], "s-", color=COL["orange"], lw=2.6, ms=9,
        label="exact controlled block  ($\\sim\\!4^{\\,n+1}$)")
a1.plot(NS, [r["trotter_cx"] for r in D], "^-", color=COL["muted"], lw=2.2, ms=8,
        label="controlled Trotter, $r{=}2$")
a1.plot(NS, [r["aqc_cx"] for r in D], "o-", color=COL["blue"], lw=2.8, ms=9,
        label="controlled AQC (ours)")
a1.set_yscale("log"); a1.set_xticks(NS)
a1.set_xlabel("system size $n$"); a1.set_ylabel("two-qubit gates")
a1.set_title("What a Hadamard test actually pays", fontsize=13)
a1.legend(frameon=False, fontsize=10.5, loc="upper left")
style(a1)
cross = next(r["n"] for r in D if r["aqc_vs_exact"] > 1)
a1.axvline(cross - 0.5, color=COL["aqua"], ls="--", lw=1.8)
a1.text(cross - 0.45, 45, f"crossover at $n={cross}$", fontsize=10.5, color=COL["aqua"],
        va="bottom", ha="left")
best = max(D, key=lambda r: r["aqc_vs_exact"])
a1.annotate(f"{best['aqc_vs_exact']:.0f}$\\times$ fewer",
            (best["n"], best["aqc_cx"]), xytext=(-14, 46), textcoords="offset points",
            fontsize=13, weight="bold", color=COL["blue"], ha="center",
            arrowprops=dict(arrowstyle="->", color=COL["blue"], lw=2))

# ---------- right: the phase trap ----------
x = np.arange(len(NS)); w = 0.36
a2.bar(x - w / 2, [r["chi_err_naive"] for r in D], w, color=COL["orange"],
       label="AQC as shipped")
a2.bar(x + w / 2, [r["chi_err_phase_fixed"] for r in D], w, color=COL["aqua"],
       label="$+$ one ancilla $P(-\\theta)$")
a2.axhline(1.0, color=COL["muted"], ls=":", lw=1.6)
a2.set_ylim(0, 1.72)
a2.text(len(NS) / 2 - 0.5, 1.60,
        "$|\\chi|\\leq 1$, so the error is as large as the signal itself",
        fontsize=10, color=COL["muted"], ha="center")
for i, r in enumerate(D):
    a2.annotate(f"{r['chi_err_naive']:.2f}", (i - w / 2, r["chi_err_naive"]),
                textcoords="offset points", xytext=(0, 4), ha="center", fontsize=9.5,
                color=COL["orange"], weight="bold")
a2.annotate(f"{D[0]['chi_err_phase_fixed']:.3f}", (0 + w / 2, D[0]["chi_err_phase_fixed"]),
            textcoords="offset points", xytext=(0, 4), ha="center", fontsize=9.5,
            color=COL["aqua"], weight="bold")
a2.set_xticks(x); a2.set_xticklabels([f"$n{{=}}{n}$" for n in NS], fontsize=11)
a2.set_ylabel(r"$|\chi_{\rm measured}-\chi_{\rm exact}|$")
a2.set_title("The trap: a phase-blind objective", fontsize=13)
a2.legend(frameon=False, fontsize=10.5, loc="center right")
style(a2)

fig.tight_layout()
fig.savefig(os.path.join(REPO, "deck/fig_aqc_scaling.png"), dpi=200,
            bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_aqc_scaling.png")
