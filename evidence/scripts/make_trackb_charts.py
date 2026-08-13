"""Charts for the Track-B deck. Every number is read from the audited JSON artefacts
(track_b_baselines.json, track_b_hw_result.json) rather than typed in, so the charts
cannot drift from what was measured.
"""
import os
# repo root derived from this file, so the script runs from any clone/checkout
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

BASE = json.load(open(R + "evidence/track_b_baselines.json"))
HW = json.load(open(R + "evidence/track_b_hw_result.json"))[0]
TIMES = [0.0, 0.9, 1.8, 2.7]
REF = json.load(open(R + "evidence/track_b_hw_jobs.json"))["exact_reference"]


def style(ax):
    ax.set_facecolor(BG)
    ax.grid(True, axis="y", color=COL["grid"], lw=0.9); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(COL["muted"])
    ax.tick_params(colors=COL["muted"], labelsize=11)
    ax.yaxis.label.set_color(COL["ink"]); ax.title.set_color(COL["ink"])


# ============ chart 1: cost of verification vs what it returns ============
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 4.6),
                             gridspec_kw={"width_ratios": [1.05, 1]})
sc = BASE["scaling"]
ns_ = [r["n"] for r in sc]
a1.plot(ns_, [r["echo_2q"] for r in sc], "o-", color=COL["aqua"], lw=2.4, ms=8,
        label="Loschmidt echo")
a1.plot(ns_, [r["track_b_2q"] for r in sc], "s-", color=COL["blue"], lw=2.4, ms=8,
        label="Track B (ours)")
for r in sc:
    a1.annotate(f"{r['ratio']:.0f}x", (r["n"], r["track_b_2q"]), textcoords="offset points",
                xytext=(6, 6), fontsize=11, color=COL["orange"], weight="bold")
a1.set_yscale("log"); a1.set_xticks(ns_); a1.set_xlabel("system size $n$")
a1.set_ylabel("two-qubit gates")
a1.set_title("Verification cost — the echo is cheaper at every $n$", fontsize=12.5)
a1.legend(frameon=False, fontsize=11); style(a1)
a1.text(2.0, 3.4, "the 52$\\times$ gap at $n{=}2$ is\nunitary-collapse artefact;\n"
                  "it falls to 4$\\times$ by $n{=}4$",
        fontsize=10, color=COL["muted"], va="bottom")

rows = [r for r in BASE["rows"]]
names = ["classical\nfidelity", "Loschmidt\necho", "Hilbert-\nSchmidt",
         "Track B\nancilla only", "Track B\n+ shadows"]
caps = [[1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 0, 0], [1, 1, 1, 0], [1, 1, 1, 1]]
labels = ["gives a number", "runs on a QPU", "keeps the phase", "says WHICH\nobservable broke"]
M = np.array(caps).T
a2.imshow(M, cmap=matplotlib.colors.ListedColormap([BG, COL["blue"]]), aspect="auto",
          vmin=0, vmax=1)
a2.set_xticks(range(5)); a2.set_xticklabels(names, fontsize=10)
a2.set_yticks(range(4)); a2.set_yticklabels(labels, fontsize=10)
for i in range(4):
    for j in range(5):
        a2.text(j, i, "yes" if M[i, j] else "--", ha="center", va="center", fontsize=10.5,
                color="white" if M[i, j] else COL["muted"],
                weight="bold" if M[i, j] else "normal")
a2.set_title("What each method actually returns", fontsize=12.5)
a2.tick_params(colors=COL["muted"], length=0)
for s in a2.spines.values():
    s.set_visible(False)
fig.tight_layout()
fig.savefig(R + "deck/fig_tb_baselines.png", dpi=200, bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_tb_baselines.png")

# ============ chart 2: what came back from the QPU (both devices) ============
ALL = json.load(open(R + "evidence/track_b_hw_result.json"))
fig, (b1, b2) = plt.subplots(1, 2, figsize=(12.4, 4.5))
ex_echo = [REF[str(t)]["echo_p0"] for t in TIMES]
b1.plot(TIMES, ex_echo, "-", color=COL["muted"], lw=2.8, label="exact", zorder=1)
MK = {"ibm_marrakesh": ("o", "-"), "ibm_kingston": ("D", "--")}
for r in ALL:
    mk, ls = MK.get(r["backend"], ("s", ":"))
    dev = r["backend"].replace("ibm_", "")
    b1.plot(TIMES, [r["C"][str(t)] for t in TIMES], mk + ls, color=COL["aqua"], lw=2.0,
            ms=7, label=f"echo, {dev}")
    b1.plot(TIMES, [abs(complex(np.mean(r["A"][str(t)]["_pool_re"]),
                                np.mean(r["A"][str(t)]["_pool_im"]))) ** 2 for t in TIMES],
            mk + ls, color=COL["blue"], lw=2.0, ms=7, label=f"Track B, {dev}")
b1.set_xlabel("time $t$"); b1.set_ylabel(r"$|\langle\psi|W^\dagger U|\psi\rangle|^2$")
b1.set_title("Two devices, same job: the 2-gate baseline holds", fontsize=12.5)
b1.legend(frameon=False, fontsize=9); style(b1)

# worst-case error per method, across both devices -- the honest scoreboard
meth, errs, cols = [], [], []
for nm, key, ref, col in (("Loschmidt\necho\n(2 CX)", "C", "echo_p0", COL["aqua"]),
                          ("Hilbert-\nSchmidt\n(16 CX)", "D", "hst_p0", COL["violet"]),
                          ("Track B\nours\n(136 CX)", None, None, COL["blue"])):
    if key:
        e = max(abs(r[key][str(t)] - REF[str(t)][ref]) for r in ALL for t in TIMES)
    else:
        e = max(abs(complex(np.mean(r["A"][str(t)]["_pool_re"]),
                            np.mean(r["A"][str(t)]["_pool_im"]))
                    - complex(*REF[str(t)]["chi_AB"])) for r in ALL for t in TIMES)
    meth.append(nm); errs.append(e); cols.append(col)
bars = b2.bar(range(3), errs, 0.55, color=cols)
for i, e in enumerate(errs):
    b2.annotate(f"{e:.3f}", (i, e), textcoords="offset points", xytext=(0, 5),
                ha="center", fontsize=12, weight="bold", color=COL["ink"])
b2.set_xticks(range(3)); b2.set_xticklabels(meth, fontsize=10.5)
b2.set_ylabel("worst error vs exact"); b2.set_ylim(0, max(errs) * 1.25)
b2.set_title("Worst case over both devices and all times", fontsize=12.5)
style(b2)
fig.tight_layout()
fig.savefig(R + "deck/fig_tb_hardware.png", dpi=200, bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_tb_hardware.png")

# ============ chart 3: the symmetry channel as a free trust indicator ============
fig, ax = plt.subplots(figsize=(7.4, 4.2))
qdis = [np.mean(HW["B"][str(t)]["Q"]["dif"]) * 2 for t in TIMES]
ax.axhline(0, color=COL["muted"], lw=2, ls="--")
ax.plot(TIMES, qdis, "o-", color=COL["orange"], lw=2.6, ms=9)
for t, v in zip(TIMES, qdis):
    ax.annotate(f"{v:+.2f}", (t, v), textcoords="offset points", xytext=(0, -16),
                ha="center", fontsize=10.5, color=COL["orange"])
ax.set_xlabel("time $t$")
ax.set_ylabel(r"$\langle Q\rangle_W-\langle Q\rangle_U$")
ax.set_title("A free error bar: this must be exactly zero", fontsize=12.5)
ax.text(0.05, 0.06, "$[H,Q]=0$ and every Trotter factor conserves $Q$,\n"
                    "so both dynamics preserve it — any deviation is\n"
                    "pure device error, detected with no reference.",
        transform=ax.transAxes, fontsize=10.5, color=COL["muted"], va="bottom")
style(ax)
fig.tight_layout()
fig.savefig(R + "deck/fig_tb_symmetry.png", dpi=200, bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_tb_symmetry.png")


# ============ chart 4: the DOS proof of concept (Track B with mixed input) ============
DOS = json.load(open(R + "evidence/track_b_dos.json"))
TD = np.array(DOS["times"])
fig, (d1, d2) = plt.subplots(1, 2, figsize=(12.4, 4.3))
# rms goes in the TITLE: at bottom-right it sat directly on the Im markers in both panels
for ax, key, ttl in ((d1, "identity", r"$W=I$:  $\mathrm{Tr}[U(t)]/d$ — the DOS signal"),
                     (d2, "trotter", r"$W=$ Trotter:  $\mathrm{Tr}[W^\dagger U]/d$")):
    m = np.array([complex(*v) for v in DOS["curves"][key]["measured"]])
    e = np.array([complex(*v) for v in DOS["curves"][key]["exact"]])
    ax.plot(TD, e.real, "-", color=COL["muted"], lw=2.6, label="exact Re")
    ax.plot(TD, e.imag, "--", color=COL["muted"], lw=2.2, label="exact Im")
    ax.plot(TD, m.real, "o", color=COL["blue"], ms=7, label="measured Re")
    ax.plot(TD, m.imag, "^", color=COL["orange"], ms=7, label="measured Im")
    ax.set_xlabel("time $t$")
    ax.set_title(f"{ttl}   (rms {DOS['curves'][key]['rms']:.4f})", fontsize=12)
    ax.legend(frameon=False, fontsize=9.5, ncol=2); style(ax)
d2.text(0.04, 0.42, "Im $\\equiv 0$ here: real $H$ plus a\npalindromic product formula\n"
                    "force $\\mathrm{Tr}[W^\\dagger U]$ real",
        transform=d2.transAxes, fontsize=10.5, color=COL["orange"], ha="left", va="top")
fig.tight_layout()
fig.savefig(R + "deck/fig_tb_dos.png", dpi=200, bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_tb_dos.png")
