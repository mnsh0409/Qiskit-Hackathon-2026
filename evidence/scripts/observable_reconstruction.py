"""THREE-ARM PROTOCOL COMPARISON, with the analysis chain each arm actually deserves:

  ARM 1  GARBAGE (discard)   -- Hadamard test only. chi(t) -> windowed DFT -> energies.
                                No system register is kept, so NO observable is available.
  ARM 2  POST-SELECT all-Z   -- keep the all-Z shots of the shadow run. chi, chi_O -> matrix
                                pencil. Works for Z-DIAGONAL observables only.
  ARM 3  CLASSICAL SHADOW    -- full random-basis ensemble. chi, chi_O -> matrix pencil.

Target observables: Z_i, Z_i Z_j, H, and the hopping term X_iX_j + Y_iY_j.

WHAT IS ACTUALLY TRUE, checked before running rather than assumed:
  Z_0        1/1 Pauli terms Z-diagonal -> post-select CAN reconstruct it
  Z_0 Z_1    1/1                        -> post-select CAN reconstruct it
  H          5/9                        -> post-select sees only the diagonal part
  XX+YY      0/2                        -> post-select is completely blind

So "only the shadow can reconstruct these" is TRUE against the discard arm for all four,
and TRUE against post-selection for H and the hopping term -- but FALSE for Z_i and Z_iZ_j,
which a Z-only protocol handles fine (and, per R039, more cheaply). We report it that way.
For the non-diagonal observables the post-select failure is SYSTEMATIC, not statistical:
it converges to Tr[O_Zdiag U rho], a different quantity, so more shots do not help.
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions

import json
import numpy as np
from scipy.signal import find_peaks

ns = load_notebook_definitions()
HAM, CHARGE, PSI, N_SYS = ns["HAM"], ns["CHARGE"], ns["PSI"], ns["N_SYS"]
SPO, TS, SHOTS = ns["SparsePauliOp"], ns["TS"], 2000
E_EXACT, Q_EXACT = ns["E_EXACT"], ns["Q_EXACT_LABELS"]

OBS = {
    "Z_0":        SPO.from_sparse_list([("Z", [0], 1.0)], num_qubits=N_SYS),
    "Z_0Z_1":     SPO.from_sparse_list([("ZZ", [0, 1], 1.0)], num_qubits=N_SYS),
    "H":          HAM,
    "X0X1+Y0Y1":  SPO.from_sparse_list([("XX", [0, 1], 1.0), ("YY", [0, 1], 1.0)],
                                        num_qubits=N_SYS),
}



def exact_ratio(o, e0):
    """The label reconstruct() targets at the line E=e0.

    chi_O(t) = sum_k <psi|O|k><k|psi> e^{-iE_k t} and chi(t) = sum_k |<k|psi>|^2 e^{-iE_k t},
    so the per-mode ratio is <psi|O|k>/<psi|k> -- NOT <k|O|k>. The two coincide only when
    [O,H]=0 (e.g. O=Q or O=H). Using <k|O|k> as the reference for a non-commuting O is a
    reference bug, not an estimator failure; it cost one rerun to notice."""
    ev, evec = np.linalg.eigh(HAM.to_matrix())
    k = int(np.argmin(np.abs(ev - e0)))
    v = evec[:, k]
    num = PSI.conj() @ o.to_matrix() @ v
    den = PSI.conj() @ v
    return float(np.real(num / den)) if abs(den) > 1e-12 else float("nan")


def zdiag_part(o):
    terms = [(l, c) for l, c in o.to_list() if set(l) <= {"I", "Z"}]
    return SPO.from_list(terms) if terms else None


print(f"one shadow sweep: {len(TS)} times x 2 quadratures x {SHOTS} shots, "
      f"{len(OBS)} joint observables")
import os
_CACHE = "/home/martin/Documents/QiskitHackathon/2026/evidence/obsrec_sweep.npz"
SW = ns["run_time_sweep"](HAM, TS, SHOTS, ns["SEED"], joint_observables=OBS, verbose=False)
# cache the derived signals immediately -- the sweep costs ~2.5 min
np.savez(_CACHE, chi=SW.chi, **{f"chiO_{k}": SW.chi_obs[k] for k in OBS})
print("done (signals cached)\n")

# ---------------- ARM 1: discard the garbage -> chi only -> DFT ----------------
E_GRID = np.linspace(-3.2, 3.2, 3200)
F = ns["dft_spectrum"](TS, SW.chi, E_GRID)
mag = np.abs(F)
idx, _ = find_peaks(mag, height=0.05 * mag.max())
dft_E = E_GRID[idx]
hits1 = sum(1 for e0 in E_EXACT if len(dft_E) and min(abs(dft_E - e0)) < 0.35)
print("=" * 78)
print("ARM 1 -- GARBAGE DISCARDED: Hadamard test only, chi -> DFT")
print("=" * 78)
print(f"  energies: {hits1}/4 lines recovered at {np.round(sorted(dft_E),3).tolist()}")
print("  observables: NONE. The system register was not measured, so no O can be formed")
print("  at any shot count. This is a structural limit, not a precision limit.")

# ---------------- ARM 3: shadow + matrix pencil ----------------
print("\n" + "=" * 78)
print("ARM 3 -- CLASSICAL SHADOW: chi, chi_O -> matrix pencil")
print("=" * 78)
ROWS = []
shadow_labels = {}
for name, o in OBS.items():
    E, P, lab, rank = ns["reconstruct"](TS, SW.chi, SW.chi_obs[name])
    exact_lab = [exact_ratio(o, e0) for e0 in E_EXACT]
    got = [float(lab[int(np.argmin(np.abs(E - e0)))]) for e0 in E_EXACT]
    err = max(abs(g - x) for g, x in zip(got, exact_lab))
    shadow_labels[name] = (got, exact_lab, err)
    print(f"  {name:<11} per-line labels {np.round(got,3).tolist()}")
    print(f"  {'':<11} exact           {np.round(exact_lab,3).tolist()}   max err {err:.3f}")

# ---------------- ARM 2: post-select all-Z + matrix pencil ----------------
print("\n" + "=" * 78)
print("ARM 2 -- POST-SELECT all-Z: same shots, Z-only subset, matrix pencil")
print("=" * 78)
# rebuild chi and chi_O from the all-Z subset
chi_ps, chiO_ps = [], {k: [] for k in OBS}
for rec_re, rec_im in SW.records:
    q = []
    per_obs = {k: [] for k in OBS}
    for rec in (rec_re, rec_im):
        allz = np.all(rec.bases == 2, axis=1)
        a = rec.ancilla[allz]; s = rec.outcomes[allz]
        q.append(float(np.mean(a)))
        for name, o in OBS.items():
            zd = zdiag_part(o)
            if zd is None:
                per_obs[name].append(np.nan)      # structurally unmeasurable
                continue
            # evaluate the Z-diagonal part directly on each shot
            val = np.zeros(len(a))
            for lab, c in zd.to_list():
                term = np.ones(len(a))
                for j, ch in enumerate(lab[::-1]):
                    if ch == "Z":
                        term = term * s[:, j]
                val = val + float(np.real(c)) * term
            per_obs[name].append(float(np.mean(a * val)))
    chi_ps.append(complex(*q))
    for name in OBS:
        chiO_ps[name].append(complex(*per_obs[name]))
chi_ps = np.array(chi_ps)

for name, o in OBS.items():
    zd = zdiag_part(o)
    n_d = 0 if zd is None else len(zd)
    n_t = len(o)
    if zd is None:
        print(f"  {name:<11} 0/{n_t} terms diagonal -> IMPOSSIBLE (no unbiased estimator exists)")
        ROWS.append(dict(observable=name, arm="post-select", status="impossible",
                         n_diag=0, n_total=n_t))
        continue
    arr = np.array(chiO_ps[name])
    E, P, lab, rank = ns["reconstruct"](TS, chi_ps, arr)
    got = [float(lab[int(np.argmin(np.abs(E - e0)))]) for e0 in E_EXACT]
    # exact label for the FULL observable (what you wanted) and its Z-diagonal part
    ex_full = [exact_ratio(o, e0) for e0 in E_EXACT]
    ex_zd = [exact_ratio(zd, e0) for e0 in E_EXACT]
    bias = max(abs(f - z) for f, z in zip(ex_full, ex_zd))
    tag = "OK" if n_d == n_t else f"BIASED (systematic, max {bias:.3f})"
    print(f"  {name:<11} {n_d}/{n_t} terms diagonal -> {tag}")
    print(f"  {'':<11} recovered {np.round(got,3).tolist()}  vs wanted "
          f"{np.round(ex_full,3).tolist()}")
    ROWS.append(dict(observable=name, arm="post-select",
                     status="ok" if n_d == n_t else "biased",
                     n_diag=n_d, n_total=n_t, systematic_bias=float(bias),
                     recovered=got, wanted=ex_full))

print("\n" + "=" * 78)
print("CAPABILITY SUMMARY")
print("=" * 78)
print(f"{'observable':<12} {'discard':>10} {'post-select':>26} {'shadow':>10}")
print("-" * 78)
for name, o in OBS.items():
    zd = zdiag_part(o); n_d = 0 if zd is None else len(zd); n_t = len(o)
    ps = "YES" if n_d == n_t else ("BLIND" if n_d == 0 else f"biased ({n_d}/{n_t} terms)")
    print(f"{name:<12} {'--':>10} {ps:>26} {'YES':>10}")
print("\n  'Only the shadow can do it' is TRUE for H and X0X1+Y0Y1 against BOTH other arms,")
print("  and TRUE for Z_0 / Z_0Z_1 against the discard arm -- but those two are Z-diagonal,")
print("  so post-selection handles them (and R039 shows a dedicated Z sweep does it cheaper).")

with open("/home/martin/Documents/QiskitHackathon/2026/evidence/observable_reconstruction.json",
          "w") as fh:
    json.dump(dict(shots=SHOTS, dft_lines=hits1,
                   shadow={k: dict(got=v[0], exact=v[1], max_err=v[2])
                           for k, v in shadow_labels.items()},
                   postselect=ROWS), fh, indent=2)
print("\nwrote evidence/observable_reconstruction.json")
