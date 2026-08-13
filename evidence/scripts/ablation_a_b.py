"""Ablation A: protocol x estimator grid, with the standard-vs-shadow equivalence
demonstrated numerically rather than asserted, plus honest cost accounting.
Ablation B: resolution failure boundary (T_max sweep) -- pure post-processing.

Drives the graded notebook code via nbclient; estimator definitions are lifted
programmatically out of their cells, never hand-copied.
"""
import json
import nbformat
from nbclient import NotebookClient

REPO = "/home/martin/Documents/QiskitHackathon/2026"
NB = f"{REPO}/shadow_hadamard_challenge_PARTICIPANT.ipynb"
OUT = "/tmp/qh26_scratch"

src = json.load(open(NB, encoding="utf-8"))
cells = src["cells"]

nb = nbformat.v4.new_notebook()
nb.metadata = src.get("metadata", {})

# cells 0..48 -> definitions + the main 256,000-shot sweep (gives CHI, CHI_Q, SWEEP)
for c in cells[:49]:
    if c["cell_type"] == "code":
        nb.cells.append(nbformat.v4.new_code_cell(source="".join(c["source"])))


def defs_of(cell_id, driver_marker):
    body = next("".join(c["source"]) for c in cells if c.get("id") == cell_id)
    assert driver_marker in body, f"marker missing in {cell_id} -- notebook changed?"
    return body.split(driver_marker)[0]


nb.cells.append(nbformat.v4.new_code_cell(
    source=defs_of("534b32e1", "DFT_PEAKS = dft_peak_labels(")))       # dft_spectrum, dft_peak_labels
nb.cells.append(nbformat.v4.new_code_cell(
    source=defs_of("8c988cf4", "E_HAT, P_HAT, Q_HAT_LABEL, RANK = reconstruct(")))  # pencil, reconstruct

ablation = r'''
import json as _json
RES = {}

# ======================================================================== ABLATION A
# The standard Hadamard test measures ONLY the ancilla. The shadow variant adds basis
# rotations + system measurement. Checkpoint 3b/3c prove the ancilla marginal is untouched,
# so chi(t) should be the SAME random variable. Demonstrate it rather than assert it.

def run_standard_hadamard(ham, t, phi, n_shots, seed, backend=None):
    """Textbook Hadamard test: ancilla only, no shadow rotations, system discarded."""
    backend = backend if backend is not None else AerSimulator()
    qc = build_shadow_hadamard_circuit(ham, t, phi, basis=None, measure=True)
    tqc = transpile(qc, backend)
    mem = backend.run(tqc, shots=n_shots, memory=True,
                      seed_simulator=seed).result().get_memory(0)
    _outc, anc = parse_memory(mem, ham.num_qubits)
    return anc            # the system columns exist but are DISCARDED -- that is the ablation

print("ABLATION A -- standard vs shadow Hadamard, identical budget\n")
chi_std, sem_std = [], []
for i, t in enumerate(TS):
    a_re = run_standard_hadamard(HAM, t, PHI_RE, SHOTS, sub_seed("std-re", i))
    a_im = run_standard_hadamard(HAM, t, PHI_IM, SHOTS, sub_seed("std-im", i))
    chi_std.append(np.mean(a_re) + 1j * np.mean(a_im))
    sem_std.append((np.std(a_re, ddof=1) / np.sqrt(len(a_re)),
                    np.std(a_im, ddof=1) / np.sqrt(len(a_im))))
chi_std = np.array(chi_std); sem_std = np.array(sem_std)

CHI_REF_A = exact_chi(HAM, PSI, TS)
err_std = np.abs(chi_std - CHI_REF_A)
err_shd = np.abs(CHI - CHI_REF_A)
sem_std_c = np.hypot(sem_std[:, 0], sem_std[:, 1])
sem_shd_c = np.hypot(SWEEP.chi_sem[:, 0], SWEEP.chi_sem[:, 1])

# are the two chi estimates consistent? difference vs combined shot noise
z = np.abs(chi_std - CHI) / np.hypot(sem_std_c, sem_shd_c)
print(f"  chi rms error   standard {np.sqrt(np.mean(err_std**2)):.4f}   "
      f"shadow {np.sqrt(np.mean(err_shd**2)):.4f}")
print(f"  mean sem        standard {np.mean(sem_std_c):.4f}   shadow {np.mean(sem_shd_c):.4f}")
print(f"  |chi_std - chi_shadow| / combined sem : max {np.max(z):.2f}, mean {np.mean(z):.2f}")
print(f"  => {'CONSISTENT' if np.max(z) < 5 else 'INCONSISTENT'} "
      f"(same random variable, as Checkpoint 3b/3c predict)\n")
RES["equivalence"] = dict(rms_standard=float(np.sqrt(np.mean(err_std**2))),
                          rms_shadow=float(np.sqrt(np.mean(err_shd**2))),
                          mean_sem_standard=float(np.mean(sem_std_c)),
                          mean_sem_shadow=float(np.mean(sem_shd_c)),
                          max_z=float(np.max(z)), mean_z=float(np.mean(z)))

# ---- the 2x2 grid: protocol (rows) x estimator (columns) ----
def dft_energies(ts, chi_series):
    eg = np.linspace(-3.2, 3.2, 3200)
    f = dft_spectrum(ts, chi_series, eg)
    mag = np.abs(f)
    idx, _ = find_peaks(mag, height=0.05 * mag.max())
    return eg[idx]

def pencil_energies(ts, chi_series):
    e, r = matrix_pencil(chi_series, ts[1] - ts[0])
    a = amplitudes_at(e, ts, chi_series)
    keep = np.abs(a) > 0.02
    return np.sort(e[keep])

def grade(found):
    hits = [min(abs(found - e0)) if len(found) else 9.9 for e0 in E_EXACT]
    return sum(1 for h in hits if h < 0.35), max(h for h in hits if h < 0.35) if any(h < 0.35 for h in hits) else float('nan')

print("ABLATION A -- 2x2 grid  (lines recovered of 4 | max |dE| on recovered | labels)\n")
GRID = {}
for prot, series in (("standard", chi_std), ("shadow", CHI)):
    for est, fn in (("DFT", dft_energies), ("pencil", pencil_energies)):
        found = fn(TS, series)
        n_hit, max_de = grade(found)
        labels = "IMPOSSIBLE (no chi_Q)" if prot == "standard" else "available"
        GRID[f"{prot}+{est}"] = dict(n_lines=int(n_hit), max_dE=float(max_de),
                                     labels=labels)
        print(f"  {prot:>8} + {est:<7}: {n_hit}/4 lines   max|dE| {max_de:.4f}   labels: {labels}")

# labels, where they exist
_e, _p, _q, _r = reconstruct(TS, CHI, CHI_Q)
lab_ok = sum(1 for e0, q0 in zip(E_EXACT, Q_EXACT_LABELS)
             if abs(_e[int(np.argmin(np.abs(_e - e0)))] - e0) < 0.35
             and int(np.rint(_q[int(np.argmin(np.abs(_e - e0)))])) == q0)
print(f"\n  shadow+pencil labels correct: {lab_ok}/4")
RES["grid"] = GRID
RES["shadow_pencil_labels_correct"] = int(lab_ok)

# ---- cost accounting: what would the conventional route cost for the same labels? ----
print("\nABLATION A -- cost of obtaining the SAME joint observables conventionally\n")
terms = {name: len(list(pauli_terms(obs))) for name, obs in
         (("Q", CHARGE), ("H", HAM), ("Z0", Z0_OBS))}
tot = sum(terms.values())
print(f"  dedicated modified Hadamard tests needed: " +
      ", ".join(f"{k} = {v}" for k, v in terms.items()) + f"  -> {tot} extra experiments")
print(f"  shadow route: 0 extra circuits (same {SWEEP.total_circuits:,} circuits, "
      f"{SWEEP.total_shots:,} shots)")
print(f"  price paid instead: the 3^w shadow variance premium, measured below.")

# empirical variance premium for chi_Q, and what a dedicated experiment would achieve
sem_q_meas = float(np.mean(np.hypot(SWEEP.chi_obs_sem["Q"][:, 0], SWEEP.chi_obs_sem["Q"][:, 1])))
# dedicated: each Pauli of Q measured directly, outcome +-1 => var<=1; split shots over 3 terms
sem_q_dedicated = float(np.sqrt(terms["Q"] * terms["Q"] / SHOTS) * np.sqrt(2))  # both quadratures
print(f"\n  chi_Q sem, shadow (measured)          : {sem_q_meas:.4f}")
print(f"  chi_Q sem, dedicated tests (predicted) : {sem_q_dedicated:.4f}  "
      f"({terms['Q']} terms sharing {SHOTS} shots/quadrature)")
print(f"  shadow variance cost factor           : {sem_q_meas/sem_q_dedicated:.2f}x")
print(f"  ...while ALSO delivering H and Z0 from the same shots, which would have cost")
print(f"     {terms['H']} + {terms['Z0']} = {terms['H']+terms['Z0']} further experiments.")
RES["cost"] = dict(terms=terms, total_extra_experiments=tot,
                   sem_q_shadow=sem_q_meas, sem_q_dedicated=sem_q_dedicated,
                   variance_cost_factor=float(sem_q_meas / sem_q_dedicated))

# ======================================================================== ABLATION B
# Resolution failure boundary: truncate the SAME series to shorter T_max and find where
# each estimator stops resolving the hard pair (E=-0.481 vs +0.550, spacing 1.031).
print("\n\nABLATION B -- resolution failure boundary (truncating T_max)\n")
HARD = [-0.4810, 0.5500]
print(f"{'M':>4} {'T_max':>7} {'2pi/T':>7} | {'DFT lines':>10} {'DFT pair':>9} | "
      f"{'pencil lines':>13} {'pencil pair':>12} {'labels':>7}")
print("-" * 88)
BOUND = []
for M in range(8, len(TS) + 1, 4):
    ts_m, chi_m, chiq_m = TS[:M], CHI[:M], CHI_Q[:M]
    tmax = ts_m[-1]
    d_e = dft_energies(ts_m, chi_m)
    d_pair = all(len(d_e) and min(abs(d_e - h)) < 0.35 for h in HARD)
    d_n, _ = grade(d_e)
    try:
        p_e, p_p, p_q, _ = reconstruct(ts_m, chi_m, chiq_m)
        p_pair = all(len(p_e) and min(abs(p_e - h)) < 0.35 for h in HARD)
        p_n, _ = grade(p_e)
        p_lab = sum(1 for e0, q0 in zip(E_EXACT, Q_EXACT_LABELS)
                    if abs(p_e[int(np.argmin(np.abs(p_e - e0)))] - e0) < 0.35
                    and int(np.rint(p_q[int(np.argmin(np.abs(p_e - e0)))])) == q0)
    except Exception:
        p_pair, p_n, p_lab = False, 0, 0
    BOUND.append(dict(M=int(M), T_max=float(tmax), dft_lines=int(d_n), dft_pair=bool(d_pair),
                      pencil_lines=int(p_n), pencil_pair=bool(p_pair), pencil_labels=int(p_lab)))
    print(f"{M:>4} {tmax:>7.1f} {2*np.pi/tmax:>7.3f} | {d_n:>7}/4 {str(d_pair):>9} | "
          f"{p_n:>10}/4 {str(p_pair):>12} {p_lab:>5}/4")

_dft_ok = [b["T_max"] for b in BOUND if b["dft_pair"]]
_pen_ok = [b["T_max"] for b in BOUND if b["pencil_pair"]]
print(f"\n  DFT resolves the 1.031-spaced pair from T_max >= "
      f"{min(_dft_ok) if _dft_ok else float('inf')}")
print(f"  pencil resolves it from T_max >= {min(_pen_ok) if _pen_ok else float('inf')}")
RES["boundary"] = BOUND

with open("''' + OUT + r'''/ablation_results.json", "w") as fh:
    _json.dump(RES, fh, indent=2, default=str)
print("\nwrote ablation_results.json")
'''

nb.cells.append(nbformat.v4.new_code_cell(source=ablation))
NotebookClient(nb, timeout=7200, kernel_name="qh26-t5",
               resources={"metadata": {"path": REPO}}).execute()
nbformat.write(nb, f"{OUT}/executed_ablation_ab.ipynb")
print("DONE")
