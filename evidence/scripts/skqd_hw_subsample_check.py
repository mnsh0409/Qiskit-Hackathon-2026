"""Control for R062: is the hardware degradation of the SKQD boundary due to NOISE
(corrupted in-sector samples polluting the frequency ranking) or just SAMPLE SIZE (the
device kept only ~4.2k in-sector shots vs the reference's 30k)?

Rerun the ideal-Trotter reference protocol with the sample budget SUBSAMPLED to exactly
the hardware's kept-in-sector count, across 20 seeds. If the subsampled ideal reference
still converges at the small-M end (localised) / at ~65% (delocalised), the hardware
degradation is attributable to noise, not to counting statistics.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json
sys.path.insert(0, REPO)
from hardware_run import load_notebook_definitions

import numpy as np
from itertools import combinations
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector

ns = load_notebook_definitions()
SPO = ns["SparsePauliOp"]

N, K = 12, 6
J = 0.65
FIELDS = [0.40, -0.50, 0.15, 0.20, -0.30, 0.10, 0.25, -0.15,
          0.35, -0.20, 0.05, 0.30]
TIMES = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0)
REPS = 2
M_GRID = (25, 50, 100, 150, 200, 300, 400, 600, 800)

HW = json.load(open(os.path.join(REPO, "evidence/skqd_hw_result.json")))["ibm_marrakesh"]


def sector(n, k):
    out = []
    for pos in combinations(range(n), k):
        m = 0
        for p in pos:
            m |= (1 << p)
        out.append(m)
    out.sort()
    return out, {m: i for i, m in enumerate(out)}


BASIS, INDEX = sector(N, K)
DIM = len(BASIS)


def build_Hc(ratio):
    dlt = ratio * J
    Hc = np.zeros((DIM, DIM))
    for a, m in enumerate(BASIS):
        z = [1 - 2 * ((m >> j) & 1) for j in range(N)]
        Hc[a, a] = (sum(dlt * z[i] * z[i + 1] for i in range(N - 1))
                    + sum(FIELDS[i] * z[i] for i in range(N)))
        for i in range(N - 1):
            if ((m >> i) & 1) != ((m >> (i + 1)) & 1):
                Hc[INDEX[m ^ (1 << i) ^ (1 << (i + 1))], a] += 2 * J
    return Hc


def full_ham(ratio):
    dlt = ratio * J
    t = []
    for i in range(N - 1):
        t += [("XX", [i, i + 1], J), ("YY", [i, i + 1], J), ("ZZ", [i, i + 1], dlt)]
    t += [("Z", [i], FIELDS[i]) for i in range(N)]
    return SPO.from_sparse_list(t, num_qubits=N).simplify()


def dim_needed(counts, Hc, e0):
    order = np.argsort(counts)[::-1]
    order = order[counts[order] > 0]
    for M in M_GRID:
        if M > len(order):
            return None
        sub = np.sort(order[:M])
        if abs(float(np.linalg.eigvalsh(Hc[np.ix_(sub, sub)])[0]) - e0) / abs(e0) < 1e-2:
            return M
    return None


print(f"{'Delta/J':>8}{'hw kept':>9}{'hw dim':>8} | subsampled ideal-Trotter dim needed "
      f"(20 seeds)")
print("-" * 78)
for ratio_key, ratio in (("0.3846153846153846", 0.25 / 0.65), ("5.0", 5.0)):
    kept = HW[ratio_key]["kept"]
    hw_dim = HW[ratio_key]["dim_needed"]
    Hc = build_Hc(ratio)
    ev = np.linalg.eigvalsh(Hc); e0 = float(ev[0])
    # per-time trotterised distributions, computed once
    dists = []
    for t in TIMES:
        qc = QuantumCircuit(N)
        for j in range(0, N, 2):
            qc.x(j)
        qc.append(ns["PauliEvolutionGate"](full_ham(ratio), time=t,
                  synthesis=ns["SuzukiTrotter"](order=2, reps=REPS)), range(N))
        qc = transpile(qc, basis_gates=["rz", "sx", "x", "cx"],
                       optimization_level=1, seed_transpiler=0)
        p = np.abs(np.asarray(Statevector(qc).data)) ** 2
        dists.append(p / p.sum())
    per_time = kept // len(TIMES)
    needs = []
    for seed in range(20):
        rng = np.random.default_rng(3000 + seed)
        counts = np.zeros(DIM)
        for p in dists:
            for m in rng.choice(2 ** N, size=per_time, p=p):
                if m in INDEX:
                    counts[INDEX[m]] += 1
        needs.append(dim_needed(counts, Hc, e0))
    ok = [x for x in needs if x is not None]
    desc = (f"mean {np.mean(ok):.0f}, range [{min(ok)}, {max(ok)}], "
            f"{len(ok)}/20 converged") if ok else "NEVER in all 20 seeds"
    print(f"{ratio:>8.2f}{kept:>9}{str(hw_dim):>8} | {desc}")

print("\nIf the subsampled ideal needs far less than the hardware did, the hardware "
      "degradation is noise, not sample size.")
