import json

path = "/home/martin/Documents/QiskitHackathon/2026/shadow_hadamard_challenge_PARTICIPANT.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

TARGET_ID = "534b32e1"

new_source = '''def dft_spectrum(ts, y, e_grid):
    """Hann-windowed DFT, normalised so an isolated peak's height ~ its spectral weight."""
    w = np.hanning(len(ts))
    phases = np.exp(1j * np.outer(e_grid, ts))          # note the PLUS sign
    return (phases * (w * y)) @ np.ones(len(ts)) / np.sum(w)


from scipy.signal import find_peaks

E_GRID = np.linspace(-3.2, 3.2, 3200)
F_CHI = dft_spectrum(TS, CHI, E_GRID)
F_Q = dft_spectrum(TS, CHI_Q, E_GRID)


def dft_peak_labels(e_grid, f_chi, f_q, min_height_frac=0.05):
    """Data-only baseline: find local maxima of |chi~(E)|, read the ratio at each.

    NOTE the exact spectrum is used NOWHERE here -- peaks come from the measured data alone,
    which is the rule for every estimator in Part B.
    """
    mag = np.abs(f_chi)
    idx, _ = find_peaks(mag, height=min_height_frac * mag.max())
    return [(float(e_grid[j]), float(mag[j]), float(np.real(f_q[j] / f_chi[j]))) for j in idx]


DFT_PEAKS = dft_peak_labels(E_GRID, F_CHI, F_Q)
print(f"DFT peak-ratio baseline: {len(DFT_PEAKS)} local maxima found in the measured spectrum\\n")
print("     found E   peak height    q_ratio  |  nearest exact E   exact q")
dft_labels = {}
for e, h, ratio in DFT_PEAKS:
    k = int(np.argmin(np.abs(E_EXACT - e)))               # evaluation only, not estimation
    dft_labels[k] = ratio
    flag = "" if abs(ratio - Q_EXACT_LABELS[k]) < 0.35 else "   <-- wobbles"
    print(f"   {e:+8.3f}   {h:10.4f}   {ratio:+8.3f}  |  {E_EXACT[k]:+12.3f}   "
          f"{Q_EXACT_LABELS[k]:+6d}{flag}")

_e_dom = E_GRID[int(np.argmax(np.abs(F_CHI)))]
check("DFT sign convention: the dominant line comes out at POSITIVE E", _e_dom > 0,
      f"largest |chi~(E)| at E = {_e_dom:+.3f}; chi(t) = sum_k p_k e^(-iE_k t), so you must "
      f"correlate against e^(+iEt)")
check("the data-only peak finder actually found peaks", len(DFT_PEAKS) >= 2,
      f"{len(DFT_PEAKS)} local maxima")

print("\\nTwo separate weaknesses to notice:")
print("  * ENERGIES are poor: the DFT resolution is only 2*pi/T_max ~ 0.5, so peaks are pulled")
print("    toward their neighbours and weak lines can fail to produce a local maximum at all.")
print("  * The weakest LABEL (p ~ 0.05) is contaminated by its neighbours' leakage tails.")
print("Both are fixed by the pencil + shared-frequency least-squares route in the next sections.")'''

found = False
for cell in nb["cells"]:
    if cell.get("id") == TARGET_ID:
        assert cell["cell_type"] == "code"
        old_source = "".join(cell["source"])
        assert "raise NotImplementedError" in old_source, "unexpected cell content, aborting"
        cell["source"] = new_source.splitlines(keepends=True)
        found = True
        break

assert found, "target cell id not found"

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")

print("patched cell", TARGET_ID)
