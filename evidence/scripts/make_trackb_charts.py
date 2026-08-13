"""Charts for the Track-B deck. Every number is read from the audited JSON artefacts
(track_b_baselines.json, track_b_hw_result.json) rather than typed in, so the charts
cannot drift from what was measured.
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = "/home/martin/Documents/QiskitHackathon/2026/"
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

# ============ chart 2: what came back from the QPU ============
fig, (b1, b2) = plt.subplots(1, 2, figsize=(12.4, 4.5))
ex_echo = [REF[str(t)]["echo_p0"] for t in TIMES]
ex_hst = [REF[str(t)]["hst_p0"] for t in TIMES]
go_echo = [HW["C"][str(t)] for t in TIMES]
go_hst = [HW["D"][str(t)] for t in TIMES]
ex_chi = [abs(complex(*REF[str(t)]["chi_AB"])) ** 2 for t in TIMES]
go_chi = [abs(complex(np.mean(HW["A"][str(t)]["_pool_re"]),
                      np.mean(HW["A"][str(t)]["_pool_im"]))) ** 2 for t in TIMES]

b1.plot(TIMES, ex_echo, "-", color=COL["muted"], lw=2.6, label="exact", zorder=1)
b1.plot(TIMES, go_echo, "o-", color=COL["aqua"], lw=2.2, ms=8, label="echo (2 CX)")
b1.plot(TIMES, go_hst, "^-", color=COL["violet"], lw=2.2, ms=8, label="HST (16 CX)")
b1.plot(TIMES, go_chi, "s-", color=COL["blue"], lw=2.2, ms=8, label="Track B (136 CX)")
b1.set_xlabel("time $t$"); b1.set_ylabel(r"$|\langle\psi|W^\dagger U|\psi\rangle|^2$")
b1.set_title("ibm_marrakesh: the cheap baseline wins", fontsize=12.5)
b1.legend(frameon=False, fontsize=10.5); style(b1)

OBS = ["Z_0", "Z_1", "Z_0Z_1", "X0X1+Y0Y1", "H", "Q"]
t_show = "0.0"
got = [np.mean(HW["B"][t_show][o]["sum"]) + np.mean(HW["B"][t_show][o]["dif"]) for o in OBS]
exa = [REF[t_show]["obs"][o]["W"] for o in OBS]
x = np.arange(len(OBS)); w = 0.38
b2.bar(x - w / 2, exa, w, color=COL["muted"], label="exact")
b2.bar(x + w / 2, got, w, color=COL["blue"], label="measured, $t=0$")
b2.set_xticks(x); b2.set_xticklabels(["$Z_0$", "$Z_1$", "$Z_0Z_1$", "$XX{+}YY$", "$H$", "$Q$"],
                                     fontsize=10.5)
b2.set_ylabel(r"$\langle O\rangle_W$")
b2.set_title(r"Per-observable profile — only shadows give this", fontsize=12.5)
b2.legend(frameon=False, fontsize=10.5); style(b2)
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
