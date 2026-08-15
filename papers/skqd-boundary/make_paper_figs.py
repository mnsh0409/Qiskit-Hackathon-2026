"""Paper-2 figure: (a) the Delta/J boundary at n=12 with 20-seed bootstrap CIs (R057),
(b) the Fermi-Hubbard U/t boundary on the 2x3 grid (R050). Reads the audited evidence
JSONs; nothing typed in, per house rule."""
import os, json
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COL = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "muted": "#898781"}
plt.rcParams.update({"font.size": 11, "figure.facecolor": "white"})

BOOT = json.load(open(os.path.join(REPO, "evidence/skqd_boundary_bootstrap.json")))
HUB = json.load(open(os.path.join(REPO, "evidence/hubbard_2d.json")))

fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 3.9))

# (a) Delta/J with bootstrap CIs
d = BOOT["dim"]
x = [r["delta_over_J"] for r in BOOT["rows"]]
mean = [r["stats"]["mean"] / d * 100 for r in BOOT["rows"]]
lo = [r["stats"]["ci95"][0] / d * 100 for r in BOOT["rows"]]
hi = [r["stats"]["ci95"][1] / d * 100 for r in BOOT["rows"]]
g90 = [r["ground_90pct_frac"] * 100 for r in BOOT["rows"]]
a.errorbar(x, mean, yerr=[np.subtract(mean, lo), np.subtract(hi, mean)],
           fmt="o-", color=COL["blue"], lw=2, ms=6, capsize=4,
           label="sector fraction needed (1% error)")
a.plot(x, g90, "s--", color=COL["aqua"], lw=1.8, ms=6,
       label="fraction holding 90% of ground state")
a.axvline(0.3846, color=COL["muted"], lw=1, ls=":")
a.text(0.42, 55, "benchmark\n$\\Delta/J=0.38$", fontsize=9, color=COL["muted"])
a.set_xscale("log"); a.set_xticks(x); a.set_xticklabels(["0.38", "1", "2", "5", "10"])
a.set_xlabel(r"$\Delta/J$"); a.set_ylabel("% of sector (dim 924)")
a.set_title("(a) XXZ chain, $n=12$: 20 seeds, bootstrap 95% CI", fontsize=11)
a.legend(frameon=False, fontsize=9)

# (b) Hubbard U/t
dim = HUB["sector_dim"]
ut = [r["U_over_t"] for r in HUB["skqd"]]
frac = [(r["frac"] * 100 if r["frac"] else None) for r in HUB["skqd"]]
g90h = [r["ground_90pct_frac"] * 100 for r in HUB["skqd"]]
never_x = [u for u, f in zip(ut, frac) if f is None]
ok_x = [u for u, f in zip(ut, frac) if f is not None]
ok_y = [f for f in frac if f is not None]
b.plot(ok_x, ok_y, "o-", color=COL["blue"], lw=2, ms=6,
       label="sector fraction needed (1% bandwidth)")
b.plot(never_x, [100] * len(never_x), "x", color=COL["orange"], ms=10, mew=2.5,
       label="never converged (all observed configs insufficient)")
b.plot(ut, g90h, "s--", color=COL["aqua"], lw=1.8, ms=6,
       label="fraction holding 90% of ground state")
b.set_xscale("log"); b.set_xticks(ut); b.set_xticklabels(["0.5", "2", "4", "8", "16"])
b.set_xlabel(r"$U/t$"); b.set_ylabel(f"% of sector (dim {dim})")
b.set_title(r"(b) $2{\times}3$ Fermi--Hubbard, half filling", fontsize=11)
b.legend(frameon=False, fontsize=8.5)

for ax in (a, b):
    ax.grid(True, axis="y", color="#e1e0d9", lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

fig.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_boundary_ci_hubbard.png")
fig.savefig(out, dpi=200, bbox_inches="tight")
print("wrote", out)
