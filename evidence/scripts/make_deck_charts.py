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
