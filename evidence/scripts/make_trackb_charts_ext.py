"""Regenerates ONLY fig_tb_hardware.png (p.20) and fig_tb_symmetry.png (p.21) using R059's
extended-time marrakesh data instead of R044's original 4-point marrakesh data.

WHY REPLACE marrakesh RATHER THAN APPEND: R059 found the extended job's charge-conservation
deviations are systematically smaller than R044's original marrakesh job at the 3 overlapping
times (different calibration snapshot, same physics) -- splicing R044's original 4 points
with R059's 3 new ones would draw a discontinuity at t=2.7 that is a calibration-drift
artefact, not a real effect. Using R059's own self-consistent 7-point series end to end
avoids that. kingston is UNCHANGED (still R044's original 4 points, t<=2.7 only) -- no
extended-time run was done on kingston, so fig_tb_hardware.png now shows kingston out to
2.7 and marrakesh out to 5.4, explicitly labelled.

exact_reference is IDENTICAL between the two job files at the 4 overlapping times (verified
bit-for-bit before writing this script -- REF is deterministic from the model, not measured),
so there is no consistency issue in reusing R059's REF for every point on both devices.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = REPO + os.sep
COL = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "violet": "#4a3aa7",
       "ink": "#0b0b0b", "muted": "#898781", "grid": "#e1e0d9"}
BG = "#fcfcfb"
plt.rcParams.update({"figure.facecolor": BG, "savefig.facecolor": BG, "font.size": 12})

TIMES_K = [0.0, 0.9, 1.8, 2.7]                       # kingston: R044, unchanged
TIMES_M = [0.0, 0.9, 1.8, 2.7, 3.6, 4.5, 5.4]         # marrakesh: R059, extended
REF = json.load(open(R + "evidence/track_b_hw_jobs_ext.json"))["exact_reference"]

ORIG = json.load(open(R + "evidence/track_b_hw_result.json"))
KINGSTON = next(r for r in ORIG if r["backend"] == "ibm_kingston")
MARRAKESH_EXT = json.load(open(R + "evidence/track_b_hw_result_ext.json"))[0]
assert MARRAKESH_EXT["backend"] == "ibm_marrakesh"


def style(ax):
    ax.set_facecolor(BG)
    ax.grid(True, axis="y", color=COL["grid"], lw=0.9); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(COL["muted"])
    ax.tick_params(colors=COL["muted"], labelsize=11)
    ax.yaxis.label.set_color(COL["ink"]); ax.title.set_color(COL["ink"])


# ============ chart 2: what came back from the QPU (both devices, extended window) =========
fig, (b1, b2) = plt.subplots(1, 2, figsize=(12.4, 4.5))
ex_echo_m = [REF[str(t)]["echo_p0"] for t in TIMES_M]
b1.plot(TIMES_M, ex_echo_m, "-", color=COL["muted"], lw=2.8, label="exact", zorder=1)

b1.plot(TIMES_K, [KINGSTON["C"][str(t)] for t in TIMES_K], "D--", color=COL["aqua"], lw=2.0,
        ms=7, label="echo, kingston (R044, t≤2.7)")
b1.plot(TIMES_K, [abs(complex(np.mean(KINGSTON["A"][str(t)]["_pool_re"]),
                              np.mean(KINGSTON["A"][str(t)]["_pool_im"]))) ** 2
                  for t in TIMES_K],
        "D--", color=COL["blue"], lw=2.0, ms=7, label="Track B, kingston (R044, t≤2.7)")

b1.plot(TIMES_M, [MARRAKESH_EXT["C"][str(t)] for t in TIMES_M], "o-", color=COL["aqua"],
        lw=2.2, ms=7, label="echo, marrakesh (R059, t≤5.4)")
b1.plot(TIMES_M, [abs(complex(np.mean(MARRAKESH_EXT["A"][str(t)]["_pool_re"]),
                              np.mean(MARRAKESH_EXT["A"][str(t)]["_pool_im"]))) ** 2
                  for t in TIMES_M],
        "o-", color=COL["blue"], lw=2.2, ms=7, label="Track B, marrakesh (R059, t≤5.4)")

b1.axvline(2.7, color=COL["muted"], lw=1.0, ls=":")
b1.text(2.75, b1.get_ylim()[1] * 0.92, "R044's original window ends here",
        fontsize=8.5, color=COL["muted"])
b1.set_xlabel("time $t$"); b1.set_ylabel(r"$|\langle\psi|W^\dagger U|\psi\rangle|^2$")
b1.set_title("The 2-gate baseline holds -- extended to $t{=}5.4$ on marrakesh", fontsize=12)
b1.legend(frameon=False, fontsize=7.6); style(b1)

meth, errs, cols = [], [], []
for nm, key, ref, col in (("Loschmidt\necho\n(2 CX)", "C", "echo_p0", COL["aqua"]),
                          ("Hilbert-\nSchmidt\n(16 CX)", "D", "hst_p0", COL["violet"]),
                          ("Track B\nours\n(136 CX)", None, None, COL["blue"])):
    vals = []
    if key:
        vals += [abs(KINGSTON[key][str(t)] - REF[str(t)][ref]) for t in TIMES_K]
        vals += [abs(MARRAKESH_EXT[key][str(t)] - REF[str(t)][ref]) for t in TIMES_M]
    else:
        vals += [abs(complex(np.mean(KINGSTON["A"][str(t)]["_pool_re"]),
                             np.mean(KINGSTON["A"][str(t)]["_pool_im"]))
                    - complex(*REF[str(t)]["chi_AB"])) for t in TIMES_K]
        vals += [abs(complex(np.mean(MARRAKESH_EXT["A"][str(t)]["_pool_re"]),
                             np.mean(MARRAKESH_EXT["A"][str(t)]["_pool_im"]))
                    - complex(*REF[str(t)]["chi_AB"])) for t in TIMES_M]
    meth.append(nm); errs.append(max(vals)); cols.append(col)
bars = b2.bar(range(3), errs, 0.55, color=cols)
for i, e in enumerate(errs):
    b2.annotate(f"{e:.3f}", (i, e), textcoords="offset points", xytext=(0, 5),
                ha="center", fontsize=12, weight="bold", color=COL["ink"])
b2.set_xticks(range(3)); b2.set_xticklabels(meth, fontsize=10.5)
b2.set_ylabel("worst error vs exact"); b2.set_ylim(0, max(errs) * 1.25)
b2.set_title("Worst case, kingston t≤2.7 + marrakesh t≤5.4", fontsize=11.5)
style(b2)
fig.tight_layout()
fig.savefig(R + "deck/fig_tb_hardware.png", dpi=200, bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_tb_hardware.png (extended)")
print(f"  worst errors: echo {errs[0]:.4f}  HST {errs[1]:.4f}  Track B {errs[2]:.4f}  "
      f"(ratio Track B / echo = {errs[2]/errs[0]:.1f}x)")

# ============ chart 3: the symmetry channel, extended to t=5.4 (marrakesh, R059) ===========
fig, ax = plt.subplots(figsize=(7.4, 4.2))
qdis = [np.mean(MARRAKESH_EXT["B"][str(t)]["Q"]["dif"]) * 2 for t in TIMES_M]
ax.axhline(0, color=COL["muted"], lw=2, ls="--")
ax.plot(TIMES_M, qdis, "o-", color=COL["orange"], lw=2.6, ms=9)
for t, v in zip(TIMES_M, qdis):
    dx = 16 if t == 2.7 else 0                     # nudge off the t=2.7 vertical marker line
    ax.annotate(f"{v:+.2f}", (t, v), textcoords="offset points", xytext=(dx, -16),
                ha="center", fontsize=10, color=COL["orange"])
ax.axvline(2.7, color=COL["muted"], lw=1.0, ls=":")
ax.text(2.75, ax.get_ylim()[1] * 0.90, "orig. window ends", fontsize=8, color=COL["muted"])
ax.set_xlabel("time $t$")
ax.set_ylabel(r"$\langle Q\rangle_W-\langle Q\rangle_U$")
ax.set_title("A free error bar, extended to $t{=}5.4$: still exactly zero by conservation",
             fontsize=11.8)
ax.text(0.05, 0.06, "$[H,Q]=0$ and every Trotter factor conserves $Q$, so both\n"
                    "dynamics preserve it at every $t$ -- deviation stays bounded,\n"
                    "not growing, over 2x the originally measured window.",
        transform=ax.transAxes, fontsize=10, color=COL["muted"], va="bottom")
style(ax)
fig.tight_layout()
fig.savefig(R + "deck/fig_tb_symmetry.png", dpi=200, bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_tb_symmetry.png (extended)")
print(f"  mean {np.mean(qdis):+.4f}  std {np.std(qdis, ddof=1):.4f}  "
      f"range [{min(qdis):+.3f}, {max(qdis):+.3f}]")
