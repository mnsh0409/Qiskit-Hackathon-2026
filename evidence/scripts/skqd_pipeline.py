"""SKQD-style sample-based diagonalisation on REAL HARDWARE shots, with symmetry-based
configuration recovery.

READ THIS BEFORE READING THE NUMBERS -- what this does and does not show.

SKQD (Sample-based Krylov Quantum Diagonalization) samples computational-basis
configurations from time-evolved states, unions them into a subspace, and diagonalises H
there classically. Its VALUE PROPOSITION is spanning a subspace too large to enumerate.

**That value proposition cannot be tested at our size, and we do not claim to test it.**
Our reachable space is 3-dimensional (2site) / 4-dimensional (frozen). Sampling finds every
configuration, so the subspace is complete and the diagonalisation is exact BY CONSTRUCTION,
for reasons having nothing to do with SKQD working. Reporting that as an SKQD success would
be meaningless.

What IS genuinely testable here, and is the point of this script:
  1. The DATA PATH: our shadow-Hadamard records really do feed an SKQD pipeline. The all-Z
     subset of a random-basis shadow ensemble is exactly a set of computational-basis
     configurations sampled from rho^(I)(t), which contains the time-evolved state.
  2. CONFIGURATION RECOVERY on real noisy data: hardware shots contain symmetry-violating
     configurations (R036 measured 1.650% of them). Does dropping them change the recovered
     spectrum? That is a real question about noisy-data handling, answerable at n=2.

So: pipeline demonstrated end to end on real hardware; method's scaling advantage NOT
demonstrated and explicitly out of reach at this benchmark size.
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


def model_info(model):
    n, H, Q, prep, psi, label = get_model(ns, model)
    qd = np.real(np.diag(Q.to_matrix())).round().astype(int)
    populated = sorted({int(q) for q, a in zip(qd, np.abs(psi) ** 2) if a > 1e-12})
    return n, H, Q, psi, prep, qd, populated


def configs_from_shots(bases, outcomes, n):
    """All-Z shots -> computational-basis indices. outcome +1 -> bit 0, -1 -> bit 1.
    Bit j of the index is system qubit j (little-endian, matching CONVENTIONS §1)."""
    all_z = np.all(bases == 2, axis=1)
    outs = outcomes[all_z]
    bits = (outs < 0).astype(int)                      # -1 -> 1
    idx = np.zeros(len(bits), dtype=int)
    for j in range(n):
        idx |= bits[:, j] << j
    return idx


def skqd_diagonalise(H, config_indices):
    """Project H onto span{|c> : c in configs} and diagonalise. Classical post-processing."""
    cfgs = sorted(set(int(c) for c in config_indices))
    Hm = H.to_matrix()
    sub = Hm[np.ix_(cfgs, cfgs)]
    evals = np.linalg.eigvalsh(sub)
    return cfgs, evals


def exact_populated_levels(H, Q, psi):
    """Exact eigenvalues carrying nonzero weight in psi -- the evaluation-side truth."""
    Hm, Qm = H.to_matrix(), np.real(np.diag(Q.to_matrix()))
    out = []
    for q in sorted(set(Qm.round().astype(int).tolist())):
        idx = np.where(Qm.round().astype(int) == q)[0]
        ev, evec = np.linalg.eigh(Hm[np.ix_(idx, idx)])
        amps = evec.conj().T @ psi[idx]
        for e, a in zip(ev, np.abs(amps) ** 2):
            if a > 1e-10:
                out.append(float(e))
    return sorted(out)


def report(tag, H, Q, psi, qd, populated, bases, outcomes, n):
    idx = configs_from_shots(bases, outcomes, n)
    charge = np.array([qd[c] for c in idx])
    good = np.isin(charge, populated)
    n_all, n_bad = len(idx), int((~good).sum())

    cfg_raw, ev_raw = skqd_diagonalise(H, idx)
    cfg_rec, ev_rec = skqd_diagonalise(H, idx[good])
    truth = exact_populated_levels(H, Q, psi)

    print(f"\n--- {tag} ---")
    print(f"  all-Z shots {n_all:,}; symmetry-violating {n_bad:,} ({n_bad/n_all*100:.3f}%)")
    print(f"  RAW      subspace dim {len(cfg_raw)} (configs {cfg_raw})")
    print(f"           eigenvalues {np.round(ev_raw, 4).tolist()}")
    print(f"  RECOVERED subspace dim {len(cfg_rec)} (configs {cfg_rec})")
    print(f"           eigenvalues {np.round(ev_rec, 4).tolist()}")
    print(f"  exact POPULATED levels {np.round(truth, 4).tolist()}")

    def match_err(ev):
        return max(min(abs(e - t) for e in ev) for t in truth) if len(ev) else float("nan")
    print(f"  worst |dE| to a populated level: raw {match_err(ev_raw):.2e}, "
          f"recovered {match_err(ev_rec):.2e}")
    spurious_raw = len(ev_raw) - len(truth)
    spurious_rec = len(ev_rec) - len(truth)
    print(f"  SPURIOUS eigenvalues (unpopulated sectors leaking in): "
          f"raw {spurious_raw}, recovered {spurious_rec}")
    ROWS.append(dict(tag=tag, all_z_shots=n_all, violating=n_bad,
                     dim_raw=len(cfg_raw), dim_recovered=len(cfg_rec),
                     ev_raw=[float(x) for x in ev_raw],
                     ev_recovered=[float(x) for x in ev_rec],
                     exact_populated=truth,
                     worst_dE_raw=float(match_err(ev_raw)),
                     worst_dE_recovered=float(match_err(ev_rec)),
                     spurious_raw=int(spurious_raw), spurious_recovered=int(spurious_rec)))


print("=" * 78)
print("(1) IDEAL SIMULATOR control -- no errors, so recovery should change nothing")
print("=" * 78)
for model in ("2site", "frozen"):
    n, H, Q, psi, prep, qd, populated = model_info(model)
    bases_all = list(itertools.product(range(3), repeat=n))
    backend = AerSimulator()
    B, O = [], []
    for phi, sd in ((ns["PHI_RE"], 401), (ns["PHI_IM"], 402)):
        circs = [ns["build_shadow_hadamard_circuit"](H, 0.9, phi, basis=list(b), prep=prep,
                                                      method="exact") for b in bases_all]
        res = backend.run(transpile(circs, backend), shots=2000, memory=True,
                          seed_simulator=sd).result()
        for k, b in enumerate(bases_all):
            outc, _a = ns["parse_memory"](res.get_memory(k), n)
            B.append(np.tile(b, (len(outc), 1))); O.append(outc)
    report(f"ideal sim, {model}", H, Q, psi, qd, populated,
           np.concatenate(B), np.concatenate(O), n)

print("\n" + "=" * 78)
print("(2) REAL HARDWARE -- does configuration recovery clean the spectrum?")
print("=" * 78)
JOB = "d9uk99k98n5s7392vhsg"
db = json.load(open("/home/martin/Documents/QiskitHackathon/2026/hardware_jobs.json"))
meta = db[JOB]
n, H, Q, psi, prep, qd, populated = model_info(meta["model"])
res = QiskitRuntimeService().job(JOB).result()
B, O = [], []
for i, (pi, basis) in enumerate(meta["plan"]):
    outc, _a = ns["parse_memory"](res[i].data.c.get_bitstrings(), n)
    B.append(np.tile(basis, (len(outc), 1))); O.append(outc)
report(f"REAL HARDWARE {meta['backend']}, {meta['model']} (job {JOB})",
       H, Q, psi, qd, populated, np.concatenate(B), np.concatenate(O), n)

print("\n" + "=" * 78)
print("HONEST SCOPE")
print("=" * 78)
print("  The subspace is COMPLETE at this size, so exactness here is guaranteed by")
print("  dimension counting, not by SKQD working. What this demonstrates is (a) the data")
print("  path -- shadow records really do feed an SKQD pipeline -- and (b) configuration")
print("  recovery on genuinely noisy hardware shots. The scaling advantage that motivates")
print("  SKQD is OUT OF REACH at n=2-3 and is not claimed.")

with open("/home/martin/Documents/QiskitHackathon/2026/evidence/skqd_result.json", "w") as fh:
    json.dump(ROWS, fh, indent=2)
print("\nwrote evidence/skqd_result.json")
