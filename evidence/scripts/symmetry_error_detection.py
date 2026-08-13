"""Going-further robustness item 3: sector post-selection as ERROR DETECTION, on real
hardware shots.

THE IDEA (this is SQD's "configuration recovery" specialised to our conserved charge, and
unlike SKQD proper it does NOT need a large Hilbert space to be meaningful). Q = sum_j Z_j
commutes with H, and our input state populates only a subset of charge sectors. Therefore
ANY all-Z-basis shot landing in a FORBIDDEN sector is a detected error -- certified with no
reference state, no simulation, and no exact diagonalisation. It is a symmetry argument, so
it survives to any system size.

Populated vs forbidden sectors (computed, not assumed, in this script):
    frozen n=3 : populated {+1,+3}   forbidden {-3,-1}
    2site  n=2 : populated { 0,+2}   forbidden {-2}

WHY ONLY THE all-Z SHOTS. The charge Q is diagonal in the computational basis, so a shot's
charge is only defined when every qubit was measured in Z. In a random-basis shadow ensemble
that is 1 setting in 3^n -- the yield cost is real and is reported here, not hidden.

WHAT THIS IS NOT. Post-selecting the shadow record set and then re-running the shadow
estimators would BIAS them: the estimator's unbiasedness rests on the basis distribution
being uniform, and discarding a symmetry-violating subset of only the all-Z shots breaks
that (this is the same class of mistake as BUGLOG B04). So this script reports error
DETECTION RATES -- a diagnostic -- and deliberately does not feed post-selected data back
into <Q> or chi.
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions, get_model

import itertools
import json
import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService

ns = load_notebook_definitions()
ROWS = []


def sector_info(model):
    n, H, Q, prep, psi, label = get_model(ns, model)
    qd = np.real(np.diag(Q.to_matrix())).round().astype(int)
    populated = sorted({int(q) for q, a in zip(qd, np.abs(psi) ** 2) if a > 1e-12})
    # Q is conserved, so the reachable set is exactly the populated set at every time
    forbidden = sorted(set(qd.tolist()) - set(populated))
    return n, H, Q, prep, psi, qd, populated, forbidden


def detect(bases, outcomes, qd_allowed, n):
    """-> (n_allZ, n_violating). Charge is only defined on all-Z shots."""
    all_z = np.all(bases == 2, axis=1)
    if all_z.sum() == 0:
        return 0, 0
    outs = outcomes[all_z]                       # +-1 per qubit
    charge = outs.sum(axis=1)                    # Q = sum_j Z_j
    bad = ~np.isin(charge, qd_allowed)
    return int(all_z.sum()), int(bad.sum())


print("=" * 78)
print("(1) IDEAL SIMULATOR -- the detector must fire at ~0 (no errors to detect)")
print("=" * 78)
for model in ("2site", "frozen"):
    n, H, Q, prep, psi, qd, populated, forbidden = sector_info(model)
    print(f"\n{model} (n={n}): populated Q sectors {populated}, forbidden {forbidden}")
    bases_all = list(itertools.product(range(3), repeat=n))
    backend = AerSimulator()
    B, O = [], []
    for phi, sd in ((ns["PHI_RE"], 301), (ns["PHI_IM"], 302)):
        circs = [ns["build_shadow_hadamard_circuit"](H, 0.9, phi, basis=list(b), prep=prep,
                                                      method="exact") for b in bases_all]
        res = backend.run(transpile(circs, backend), shots=2000, memory=True,
                          seed_simulator=sd).result()
        for k, b in enumerate(bases_all):
            outc, _anc = ns["parse_memory"](res.get_memory(k), n)
            B.append(np.tile(b, (len(outc), 1))); O.append(outc)
    bases, outs = np.concatenate(B), np.concatenate(O)
    n_z, n_bad = detect(bases, outs, populated, n)
    rate = n_bad / n_z if n_z else float("nan")
    print(f"  total shots {len(bases):,} | all-Z shots {n_z:,} "
          f"({n_z/len(bases)*100:.1f}%, expect {100/3**n:.1f}%)")
    print(f"  symmetry-violating: {n_bad:,}  ->  DETECTED ERROR RATE {rate*100:.3f}%")
    ROWS.append(dict(source="ideal_sim", model=model, n=n, populated=populated,
                     forbidden=forbidden, total_shots=int(len(bases)), all_z_shots=n_z,
                     violating=n_bad, error_rate=float(rate)))

print("\n" + "=" * 78)
print("(2) REAL HARDWARE -- a genuine error rate, from symmetry alone")
print("=" * 78)
JOB_ID = "d9uk99k98n5s7392vhsg"          # our 2site balanced shadow ensemble (R023)
db = json.load(open("/home/martin/Documents/QiskitHackathon/2026/hardware_jobs.json"))
meta = db[JOB_ID]
n, H, Q, prep, psi, qd, populated, forbidden = sector_info(meta["model"])
res = QiskitRuntimeService().job(JOB_ID).result()
B, O = [], []
for idx, (pi, basis) in enumerate(meta["plan"]):
    outc, _anc = ns["parse_memory"](res[idx].data.c.get_bitstrings(), n)
    B.append(np.tile(basis, (len(outc), 1))); O.append(outc)
bases, outs = np.concatenate(B), np.concatenate(O)
n_z, n_bad = detect(bases, outs, populated, n)
rate = n_bad / n_z if n_z else float("nan")
print(f"\n{meta['model']} on {meta['backend']} (job {JOB_ID}), populated {populated}, "
      f"forbidden {forbidden}")
print(f"  total shots {len(bases):,} | all-Z shots {n_z:,} ({n_z/len(bases)*100:.1f}%)")
print(f"  symmetry-violating: {n_bad:,}  ->  DETECTED ERROR RATE {rate*100:.3f}%")
ROWS.append(dict(source="hardware", model=meta["model"], backend=meta["backend"],
                 job_id=JOB_ID, n=n, populated=populated, forbidden=forbidden,
                 total_shots=int(len(bases)), all_z_shots=n_z, violating=n_bad,
                 error_rate=float(rate)))

print("\n" + "=" * 78)
print("YIELD / ACCURACY TRADE-OFF (the honest cost of this diagnostic)")
print("=" * 78)
print(f"  Only 1 shot in 3^n carries a defined charge, so the diagnostic sees "
      f"{100/3**n:.1f}% of the data at n={n}.")
print("  Detection is FREE in circuits (it reuses shots already taken) but the statistical")
print("  precision of the rate is set by that reduced subset, and it can only ever detect")
print("  errors that move charge -- a phase error inside a sector is invisible to it.")

with open("/home/martin/Documents/QiskitHackathon/2026/evidence/symmetry_detection_result.json",
          "w") as fh:
    json.dump(ROWS, fh, indent=2)
print("\nwrote evidence/symmetry_detection_result.json")
