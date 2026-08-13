"""Generate the two deck charts we have data for but no figure of:
  deck/fig_hardware_grid.png  -- the complete depth x device hardware grid (R008/R018)
  deck/fig_ablation.png       -- protocol x estimator ablation + QPE (R011/R012/R021/R030)
Numbers are hard-coded FROM the RESULTS rows cited above so the chart cannot drift from
the audited values; each is labelled with its row.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COL = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "violet": "#4a3aa7",
       "ink": "#0b0b0b", "muted": "#898781", "grid": "#e1e0d9"}
BG = "#fcfcfb"
plt.rcParams.update({"figure.facecolor": BG, "savefig.facecolor": BG, "font.size": 13})


def style(ax):
    ax.set_facecolor(BG)
    ax.grid(True, axis="y", color=COL["grid"], lw=0.9)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(COL["muted"])
    ax.tick_params(colors=COL["muted"], labelsize=12)
    ax.yaxis.label.set_color(COL["ink"]); ax.title.set_color(COL["ink"])


# ---------------- chart 1: hardware depth x device grid (R008, R018) ----------------
fig, ax = plt.subplots(figsize=(7.6, 4.3))
labels = ["Trotter\n435 2q gates", "exact\n101 2q gates"]
marrakesh = [0.179, 0.822]
kingston = [0.368, 0.878]
x = np.arange(2); w = 0.36
b1 = ax.bar(x - w/2, marrakesh, w, label="ibm_marrakesh (2q err 3.2e-3)", color=COL["orange"])
b2 = ax.bar(x + w/2, kingston, w, label="ibm_kingston (2q err 2.0e-3)", color=COL["blue"])
for bars in (b1, b2):
    for b in bars:
        ax.annotate(f"{b.get_height():.3f}", (b.get_x() + b.get_width()/2, b.get_height()),
                    ha="center", va="bottom", fontsize=12, color=COL["ink"], weight="bold")
ax.axhline(1.0, color=COL["muted"], ls=":", lw=1.3)
ax.text(1.45, 1.01, "noiseless", color=COL["muted"], fontsize=11, ha="right")
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylabel("signal survival  $|\\chi_{hw}|/|\\chi_{exact}|$")
ax.set_ylim(0, 1.12)
ax.set_title("Circuit depth dominates device quality", fontsize=14, pad=12)
ax.legend(frameon=False, fontsize=11, loc="upper left")
ax.annotate("", xy=(1 - w/2, 0.80), xytext=(0 - w/2, 0.20),
            arrowprops=dict(arrowstyle="->", color=COL["ink"], lw=2))
ax.text(0.5, 0.54, "4.6$\\times$ from depth", fontsize=12.5, color=COL["ink"],
        weight="bold", ha="center", rotation=27)
style(ax); fig.tight_layout()
fig.savefig("/home/martin/Documents/QiskitHackathon/2026/deck/fig_hardware_grid.png",
            dpi=200, bbox_inches="tight")
print("wrote deck/fig_hardware_grid.png")

# ---------------- chart 2: ablation -- what each choice buys ----------------
fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.4, 4.3))

methods = ["standard\n+ DFT", "shadow\n+ DFT", "QPE", "standard\n+ pencil", "shadow\n+ pencil"]
lines = [3, 3, 4, 4, 4]
dE = [0.1387, 0.1307, 0.0794, 0.0126, 0.0325]
labels_ok = [False, False, False, False, True]
colors = [COL["muted"] if not ok else COL["aqua"] for ok in labels_ok]

axL.bar(range(5), lines, color=colors)
axL.set_xticks(range(5)); axL.set_xticklabels(methods, fontsize=10.5)
axL.set_ylabel("energy levels recovered (of 4)"); axL.set_ylim(0, 4.6)
axL.set_title("Estimator choice buys resolution", fontsize=13, pad=10)
for i, v in enumerate(lines):
    axL.annotate(f"{v}/4", (i, v), ha="center", va="bottom", fontsize=12, weight="bold",
                 color=COL["ink"])
style(axL)

axR.bar(range(5), dE, color=colors)
axR.set_xticks(range(5)); axR.set_xticklabels(methods, fontsize=10.5)
axR.set_ylabel("max $|\\Delta E|$ on recovered lines"); axR.set_yscale("log")
axR.set_title("Green = symmetry labels available", fontsize=13, pad=10)
for i, v in enumerate(dE):
    axR.annotate(f"{v:.4f}", (i, v), ha="center", va="bottom", fontsize=11, color=COL["ink"])
style(axR)
axR.grid(True, axis="y", which="both", color=COL["grid"], lw=0.9)

fig.suptitle("Only the shadow protocol yields symmetry labels — at any shot count",
             fontsize=14, color=COL["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig("/home/martin/Documents/QiskitHackathon/2026/deck/fig_ablation.png",
            dpi=200, bbox_inches="tight")
print("wrote deck/fig_ablation.png")

# ---------------- chart 3: direct-Z vs shadow (R039) ----------------
import json as _json
d = _json.load(open("/home/martin/Documents/QiskitHackathon/2026/evidence/direct_z_ablation.json"))
fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.4, 4.2))

axL.bar([0, 1], [d["sem_q_direct"], d["sem_q_shadow"]], color=[COL["aqua"], COL["blue"]], width=0.55)
axL.set_xticks([0, 1]); axL.set_xticklabels(["direct Z\n(1 circuit/setting)", "shadow\n(up to 27)"])
axL.set_ylabel("mean sem on $\\chi_Q$")
axL.set_title("Symmetry channel: direct Z is CHEAPER", fontsize=13, pad=10)
for i, v in enumerate([d["sem_q_direct"], d["sem_q_shadow"]]):
    axL.annotate(f"{v:.4f}", (i, v), ha="center", va="bottom", fontsize=12.5, weight="bold",
                 color=COL["ink"])
axL.annotate(f"{d['shadow_premium']:.2f}$\\times$ premium", (0.5, d["sem_q_shadow"]*0.55),
             ha="center", fontsize=12, color=COL["ink"], weight="bold")
axL.set_ylim(0, d["sem_q_shadow"]*1.35); style(axL)

ts = [r["t"] for r in d["H_drift"]]
axR.axhline(d["H_drift"][0]["H_exact"], color=COL["aqua"], lw=2.4, label="$\\langle H\\rangle$ exact (conserved)")
axR.plot(ts, [r["H_zdiag"] for r in d["H_drift"]], "o-", color=COL["orange"], lw=2, ms=6,
         label="$\\langle H\\rangle$ a Z-only experiment sees")
axR.fill_between(ts, [r["H_exact"] for r in d["H_drift"]], [r["H_zdiag"] for r in d["H_drift"]],
                 color=COL["orange"], alpha=0.15)
axR.set_xlabel("t"); axR.set_ylabel("$\\langle H\\rangle$")
axR.set_title("...but it cannot see 4 of 9 terms of $H$", fontsize=13, pad=10)
axR.legend(frameon=False, fontsize=10.5, loc="upper right")
axR.annotate(f"drifts by up to {d['max_gap']:.3f}\non a CONSERVED quantity",
             (4.2, 0.13), fontsize=11, color=COL["ink"], ha="center")
style(axR)
fig.suptitle("Why classical shadows: not better symmetry resolution — everything else",
             fontsize=14, color=COL["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig("/home/martin/Documents/QiskitHackathon/2026/deck/fig_direct_z.png",
            dpi=200, bbox_inches="tight")
print("wrote deck/fig_direct_z.png")

# ---------------- chart 4: the protocol escalation ladder (R040) ----------------
e = _json.load(open("/home/martin/Documents/QiskitHackathon/2026/evidence/protocol_escalation.json"))
fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.0, 4.4),
                               gridspec_kw={"width_ratios": [1.05, 1.0]})

rungs = ["discard\ngarbage", "post-select\nall-Z", "dedicated\nall-Z", "random\nshadow"]
sems  = [np.nan, e["sem_postselect"], e["sem_dedicated"], e["sem_shadow"]]
cols  = [COL["muted"], COL["orange"], COL["aqua"], COL["blue"]]
bars = axL.bar(range(4), [0 if np.isnan(v) else v for v in sems], color=cols, width=0.6)
axL.set_xticks(range(4)); axL.set_xticklabels(rungs, fontsize=10.5)
axL.set_ylabel("sem on $\\chi_Q$   (lower is better)")
axL.set_title("Precision on the symmetry channel", fontsize=13, pad=10)
axL.text(0, 0.012, "IMPOSSIBLE", ha="center", fontsize=11, color=COL["muted"],
         weight="bold", rotation=90, va="bottom")
for i, v in enumerate(sems):
    if not np.isnan(v):
        axL.annotate(f"{v:.4f}", (i, v), ha="center", va="bottom", fontsize=12,
                     weight="bold", color=COL["ink"])
axL.annotate("", xy=(3, e["sem_shadow"]+0.03), xytext=(1, e["sem_postselect"]+0.03),
             arrowprops=dict(arrowstyle="->", color=COL["ink"], lw=2))
axL.text(2, e["sem_postselect"]+0.055, f"inversion beats naive\npost-selection {e['shadow_beats_postselect']:.2f}$\\times$",
         ha="center", fontsize=11, weight="bold", color=COL["ink"])
axL.set_ylim(0, e["sem_postselect"]*1.45); style(axL)

axR.axis("off")
rows = [("discard garbage",  "yes", "--",  "--"),
        ("post-select all-Z","yes", "yes", "5/9"),
        ("dedicated all-Z",  "yes", "yes", "5/9"),
        ("random shadow",    "yes", "yes", "9/9")]
axR.text(0.5, 0.95, "What each can measure AT ALL", ha="center", fontsize=13,
         color=COL["ink"], transform=axR.transAxes)
hdr = ["protocol", "$\\chi(t)$", "$Q$", "$H$ terms"]
xs = [0.02, 0.46, 0.62, 0.80]
for x, h in zip(xs, hdr):
    axR.text(x, 0.80, h, fontsize=11.5, color=COL["muted"], transform=axR.transAxes)
for r, row in enumerate(rows):
    y = 0.68 - r*0.125
    c = COL["blue"] if r == 3 else COL["ink"]
    for x, cell in zip(xs, row):
        w = "bold" if (r == 3 or cell == "9/9") else "normal"
        axR.text(x, y, cell, fontsize=11.5, color=c, weight=w, transform=axR.transAxes)
axR.text(0.02, 0.02,
         "Z-only protocols are blind to the 4 hopping terms (0.65 each):\n"
         "$\\langle H\\rangle$ is conserved, yet what they report drifts by 0.147\n"
         "— with no second channel to notice.",
         fontsize=10, color=COL["orange"], transform=axR.transAxes, va="bottom")

fig.suptitle("Four ways to treat the garbage register — each rung buys something",
             fontsize=14.5, color=COL["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.92))
fig.savefig("/home/martin/Documents/QiskitHackathon/2026/deck/fig_escalation.png",
            dpi=200, bbox_inches="tight")
print("wrote deck/fig_escalation.png")

# ---------------- chart 5: the benchmark model itself ----------------
# CONVENTIONS section 2, frozen. Open 3-site chain: bonds (0,1) and (1,2) ONLY.
from matplotlib.patches import Ellipse, FancyArrowPatch, Arc

XLO, XHI, YLO, YHI = -0.85, 2.90, -2.10, 1.80
FIGW, FIGH = 11.0, 5.6
fig, ax = plt.subplots(figsize=(FIGW, FIGH))
ax.set_xlim(XLO, XHI); ax.set_ylim(YLO, YHI); ax.axis("off")
ax.set_facecolor(BG)

# axes are deliberately not equal-aspect (equal aspect wastes slide width), so the sites
# are ellipses pre-corrected by the data->inches ratio, which renders them round
ASP = (FIGW / (XHI - XLO)) / (FIGH / (YHI - YLO))

SITES = [0.0, 1.0, 2.0]
FIELDS = [0.40, -0.50, 0.15]            # h_0, h_1, h_2
R = 0.155

# --- the two nearest-neighbour bonds ---
for x0, x1 in zip(SITES[:-1], SITES[1:]):
    ax.plot([x0 + R, x1 - R], [0, 0], color=COL["ink"], lw=3.5, zorder=2,
            solid_capstyle="round")
    xm = 0.5 * (x0 + x1)
    ax.text(xm, 0.42, r"$0.65\,(X_iX_j\!+\!Y_iY_j)$", ha="center", fontsize=12.5,
            color=COL["blue"], zorder=3)
    ax.text(xm, 0.21, r"$+\ 0.25\,Z_iZ_j$", ha="center", fontsize=12.5,
            color=COL["aqua"], zorder=3)

# --- the bond that is NOT there: q0-q2, drawn dashed and struck out ---
ax.add_patch(Arc((1.0, 0.0), 2.12, 2.05, theta1=25, theta2=155, lw=1.8,
                 color=COL["muted"], ls=(0, (5, 4)), zorder=1))
for dx, dy in ((-1, -1), (-1, 1)):
    ax.plot([1 - 0.07 * dx, 1 + 0.07 * dx], [1.025 - 0.09 * dy, 1.025 + 0.09 * dy],
            color=COL["orange"], lw=3.2, zorder=4)
ax.text(1.17, 1.025, "no $q_0$\u2013$q_2$ term:\nonly nearest neighbours interact",
        ha="left", va="center", fontsize=12.5, color=COL["orange"], zorder=4,
        bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none"))

# --- the three spin-1/2 sites ---
for i, (x, h) in enumerate(zip(SITES, FIELDS)):
    ax.add_patch(Ellipse((x, 0), 2 * R, 2 * R * ASP, facecolor="white",
                         edgecolor=COL["ink"], lw=2.4, zorder=5))
    ax.add_patch(FancyArrowPatch((x, -0.17), (x, 0.18), arrowstyle="-|>",
                                 mutation_scale=16, color=COL["violet"], lw=2.6, zorder=6))
    ax.text(x, -0.50, rf"$q_{i}$", ha="center", va="top", fontsize=15, color=COL["ink"])
    # local Z field; the arrow direction carries the sign
    y0, y1 = (-1.06, -0.78) if h > 0 else (-0.78, -1.06)
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=14,
                                 color=COL["orange"], lw=2.2, zorder=6))
    ax.text(x, -1.24, rf"$h_{i}={h:+.2f}$", ha="center", va="top", fontsize=12.5,
            color=COL["orange"])

ax.text(XLO + 0.05, 1.75, "3 spin-$\\frac{1}{2}$ particles, open chain",
        fontsize=15, color=COL["ink"], weight="bold", ha="left", va="top")
ax.text(XHI - 0.05, 1.75, "conserved:  $Q=\\sum_j Z_j$,   $[H,Q]=0$",
        fontsize=12.5, color=COL["aqua"], ha="right", va="top")
ax.text(XHI - 0.05, 1.47, "$\\Rightarrow$ the spectrum splits into charge sectors",
        fontsize=11, color=COL["muted"], ha="right", va="top")
ax.text(1.0, -1.52, "the three local fields are unequal, so no two levels coincide",
        fontsize=11.5, color=COL["orange"], ha="center", va="top")
ax.text(1.0, -2.08,
        r"$H=\sum_{i=0}^{1}\left[\,0.65\,(X_iX_{i+1}+Y_iY_{i+1})+0.25\,Z_iZ_{i+1}\right]"
        r"\;+\;0.40\,Z_0-0.50\,Z_1+0.15\,Z_2$",
        fontsize=13.5, color=COL["ink"], ha="center", va="bottom")

fig.savefig("/home/martin/Documents/QiskitHackathon/2026/deck/fig_model.png",
            dpi=200, bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_model.png")

# ---------------- chart 6: what a classical shadow actually is ----------------
# Pedagogical, not data: a worked single-record illustration of the HKP estimator.
# The contribution values are computed from the estimator definition below, not measured.
from matplotlib.patches import Rectangle, Wedge

XLO, XHI, YLO, YHI = 0.0, 10.6, 0.0, 5.05
FW, FH = 12.6, 5.5
fig, ax = plt.subplots(figsize=(FW, FH))
ax.set_xlim(XLO, XHI); ax.set_ylim(YLO, YHI); ax.axis("off"); ax.set_facecolor(BG)

PAULI_COL = {"X": COL["orange"], "Y": COL["violet"], "Z": COL["blue"]}
DIV = 4.95

# ============================ LEFT: one shot ============================
ax.text(0.05, 4.95, "1.  Each shot draws its own random basis",
        fontsize=14, weight="bold", color=COL["ink"], va="top")

DRAWN, OUTC = ["Z", "Z", "X"], [+1, -1, +1]
for j, (y, b, s) in enumerate(zip([4.10, 3.50, 2.90], DRAWN, OUTC)):
    ax.plot([0.62, 3.42], [y, y], color=COL["ink"], lw=1.5, zorder=1)
    ax.text(0.42, y, rf"$q_{j}$", fontsize=12.5, ha="right", va="center", color=COL["ink"])
    ax.add_patch(Rectangle((1.52, y - 0.21), 0.66, 0.42, facecolor="white",
                           edgecolor=PAULI_COL[b], lw=2.2, zorder=2))
    ax.text(1.85, y, rf"$V_{{{b}}}$", fontsize=12.5, ha="center", va="center",
            color=PAULI_COL[b], zorder=3)
    ax.add_patch(Rectangle((2.92, y - 0.21), 0.5, 0.42, facecolor="white",
                           edgecolor=COL["ink"], lw=1.6, zorder=2))
    ax.add_patch(Wedge((3.17, y - 0.10), 0.15, 20, 160, width=0.035,
                       facecolor=COL["ink"], zorder=3))
    ax.plot([3.17, 3.26], [y - 0.10, y + 0.09], color=COL["ink"], lw=1.3, zorder=3)
    ax.text(3.58, y, rf"$s_{j}={s:+d}$", fontsize=12, ha="left", va="center",
            color=COL["ink"])

ax.text(1.85, 4.50, "drawn u.a.r.", fontsize=10.5, ha="center", color=COL["muted"])
ax.text(0.05, 2.44, r"$b_j \sim \mathrm{Unif}\{X,Y,Z\}$, independently on every"
                    "\n" r"qubit and every shot", fontsize=11.5, color=COL["muted"], va="top")
ax.text(0.05, 1.62, "All that is stored per shot:  "
                    r"$(\,b_0b_1b_2,\;\ s_0s_1s_2\,)$", fontsize=11.5,
        color=COL["ink"], va="top")
ax.text(0.05, 1.14,
        r"$\hat\rho=\bigotimes_j\left(3\,V_{b_j}^{\dagger}|s_j\rangle\langle s_j|V_{b_j}"
        r"-\mathbb{1}\right)$,    $\mathbb{E}[\hat\rho]=\rho$",
        fontsize=12.5, color=COL["ink"], va="top")
ax.text(0.05, 0.50, "one unbiased snapshot — meaningless alone,\n"
                    "exact in expectation once averaged",
        fontsize=10.5, color=COL["muted"], va="top")

ax.plot([DIV, DIV], [0.15, 4.88], color=COL["grid"], lw=1.6)

# ============================ RIGHT: the estimator ============================
ax.text(5.15, 4.95, "2.  One record, every Pauli at once",
        fontsize=14, weight="bold", color=COL["ink"], va="top")
ax.text(5.15, 4.50,
        r"$\hat P = 3^{\,w(P)}\!\!\prod_{j\in\mathrm{supp}(P)}\!\! s_j\;"
        r"\mathbf{1}\!\left[b_j=P_j\right]$", fontsize=14, color=COL["ink"], va="top")

SHOTS = [(("Z", "Z", "X"), (+1, -1, +1)),
         (("X", "X", "Z"), (+1, +1, -1)),
         (("Z", "Y", "Y"), (-1, +1, +1)),
         (("Z", "Z", "Z"), (+1, +1, +1)),
         (("Y", "X", "Z"), (-1, -1, +1))]
CX = [5.22, 6.00, 7.20, 8.45, 9.60]
YT = 3.55
for cx, h, dx in zip(CX, ["shot", "basis $b$", "outcome $s$",
                          r"$\widehat{Z_0Z_1}$", r"$\widehat{X_0X_1}$"],
                     [0.0, 0.24, 0.24, 0.24, 0.24]):
    ax.text(cx + dx, YT, h, fontsize=11.5, weight="bold", color=COL["ink"],
            va="center", ha="center" if dx else "left")
ax.plot([5.10, 10.40], [YT - 0.25, YT - 0.25], color=COL["muted"], lw=1.2)


def contrib(b, s, target):
    """P-hat for this shot: zero unless the drawn basis matches P on every qubit in supp(P)."""
    if any(b[j] != p for j, p in target.items()):
        return None
    v = 3 ** len(target)
    for j in target:
        v *= s[j]
    return v


for i, (b, s) in enumerate(SHOTS):
    y = YT - 0.58 - 0.44 * i
    ax.text(CX[0], y, f"{i+1}", fontsize=11.5, color=COL["muted"], va="center")
    for k, ch in enumerate(b):
        ax.text(CX[1] + 0.24 * k, y, ch, fontsize=12.5, color=PAULI_COL[ch],
                va="center", ha="center", weight="bold")
    for k, sv in enumerate(s):
        ax.text(CX[2] + 0.24 * k, y, "$+$" if sv > 0 else "$-$", fontsize=13,
                color=COL["ink"], va="center", ha="center")
    for cx, tgt in ((CX[3], {0: "Z", 1: "Z"}), (CX[4], {0: "X", 1: "X"})):
        v = contrib(b, s, tgt)
        ax.text(cx + 0.24, y, "0" if v is None else f"${v:+d}$",
                fontsize=12.5, ha="center", va="center",
                color=COL["muted"] if v is None else COL["aqua"],
                weight="normal" if v is None else "bold")

ax.text(5.15, 1.02, r"$w=2$: a shot lands with probability $3^{-2}$ and the $3^{2}$"
                    "\n" r"weight cancels it exactly, so $\mathbb{E}[\hat P]=\mathrm{Tr}[P\rho]$",
        fontsize=11, color=COL["muted"], va="top")
ax.text(5.15, 0.46, r"$q_2$'s basis never enters $\widehat{Z_0Z_1}$: only $\mathrm{supp}(P)$"
                    " must match" "\n" r"$\Rightarrow$ $3^{-w}$, not $3^{-n}$. "
                    r"The price is $\mathbb{E}[\hat P^{2}]=3^{\,w}$.",
        fontsize=11, color=COL["orange"], va="top")

fig.savefig("/home/martin/Documents/QiskitHackathon/2026/deck/fig_shadow.png",
            dpi=200, bbox_inches="tight", facecolor=BG)
print("wrote deck/fig_shadow.png")
