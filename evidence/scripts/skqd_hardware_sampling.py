"""THE SKQD LOCALISATION BOUNDARY ON REAL HARDWARE -- paper 2's missing leg.

R047/R057 measured the Delta/J boundary with sampling simulated from exact statevectors;
R050 the Hubbard analogue; only configuration recovery (R036/R037) ever touched a QPU.
This script samples configurations ON-DEVICE at one point on each side of the boundary
(Delta/J = 0.38, our benchmark's hopping-dominated ratio, and Delta/J = 5.0, deep in the
localised regime) at n=12 -- the size where R057's 20-seed bootstrap CIs live -- and runs
the identical top-M-by-frequency protocol on the returned counts.

CIRCUITS: Neel preparation (X on even sites), 2nd-order Suzuki-Trotter evolution (reps=2)
to each of the 10 protocol times, measure ALL qubits in Z. No ancilla, no interference --
the method's own noise-tolerance argument is that a corrupted sample is just a basis
state, and out-of-sector configurations (broken charge conservation) are discarded
exactly as SQD's configuration recovery discards them; the discarded fraction is itself a
device-error measure (R036 measured 1.65% on a 2-site circuit; these are ~150-gate
12-qubit circuits, so expect far more).

PRE-FLIGHT (classical, before any QPU time): the same protocol run on the TROTTERIZED
statevectors, so the hardware run differs from the reference only by device noise, not by
Trotterization. The pre-registered prediction is the ideal-Trotter dim_needed at each
ratio, plus the qualitative claim that the boundary ordering (localised needs far less
than delocalised) survives device noise.

Usage:
  python skqd_hardware_sampling.py --dry-run       # pre-flight only
  python skqd_hardware_sampling.py ibm_marrakesh   # submit
  python skqd_hardware_sampling.py --fetch         # fetch + analyse
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json
sys.path.insert(0, REPO)
from hardware_run import load_notebook_definitions

import numpy as np
from itertools import combinations
from qiskit import QuantumCircuit, transpile

ns = load_notebook_definitions()
SPO = ns["SparsePauliOp"]

N, K = 12, 6
J = 0.65
RATIOS = (0.25 / 0.65, 5.0)              # Delta/J: the benchmark's ratio, and localised
FIELDS = [0.40, -0.50, 0.15, 0.20, -0.30, 0.10, 0.25, -0.15,
          0.35, -0.20, 0.05, 0.30]       # first 12 of skqd_scaling.py's FIELDS
TIMES = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0)   # the R047 protocol grid
SHOTS = 3000                              # per time, matching the protocol
REPS = 2
M_GRID = (25, 50, 100, 150, 200, 300, 400, 600, 800)          # as R047/R057
JOB_PATH = os.path.join(REPO, "evidence/skqd_hw_job.json")


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
    """H restricted to the half-filled sector; identical construction to
    skqd_scaling.py sec. 3 (validated against the full matrix in R047)."""
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


NEEL = 0
for j in range(0, N, 2):
    NEEL |= (1 << j)


def circuit(ratio, t):
    qc = QuantumCircuit(N)
    for j in range(0, N, 2):
        qc.x(j)                                              # Neel reference
    qc.append(ns["PauliEvolutionGate"](full_ham(ratio), time=t,
              synthesis=ns["SuzukiTrotter"](order=2, reps=REPS)), range(N))
    qc.measure_all()
    return qc


def dim_needed(counts, Hc, e0):
    """Top-M-by-frequency, exactly R047's protocol. counts: array over sector index."""
    order = np.argsort(counts)[::-1]
    order = order[counts[order] > 0]
    for M in M_GRID:
        if M > len(order):
            return None, len(order)
        sub = np.sort(order[:M])
        if abs(float(np.linalg.eigvalsh(Hc[np.ix_(sub, sub)])[0]) - e0) / abs(e0) < 1e-2:
            return M, len(order)
    return None, len(order)


# ============================ FETCH MODE ============================
if "--fetch" in sys.argv:
    from qiskit_ibm_runtime import QiskitRuntimeService
    svc = QiskitRuntimeService()
    REC = json.load(open(JOB_PATH))
    results = {}
    for bname, rec in REC["jobs"].items():
        job = svc.job(rec["job_id"])
        st = str(job.status())
        print(f"job {rec['job_id']} on {bname}: {st}")
        if "DONE" not in st.upper():
            continue
        res = job.result()
        print("\n" + "=" * 78)
        print(f"{bname} -- the boundary, sampled on hardware (n={N}, sector {DIM})")
        print("=" * 78)
        out = {}
        for r_i, ratio in enumerate(rec["ratios"]):
            Hc = build_Hc(ratio)
            ev = np.linalg.eigvalsh(Hc); e0 = float(ev[0])
            counts = np.zeros(DIM)
            total = kept = 0
            for t_i in range(len(rec["times"])):
                idx = r_i * len(rec["times"]) + t_i
                d = res[idx].data
                arr = getattr(d, "meas", None) or getattr(d, "c", None)
                for b in arr.get_bitstrings():
                    total += 1
                    m = int(b[::-1], 2)   # bitstring is qubit-(N-1)..0; reverse to mask
                    if m in INDEX:
                        counts[INDEX[m]] += 1; kept += 1
            need, observed = dim_needed(counts, Hc, e0)
            frac_str = f"{need}/{DIM} = {need/DIM:.1%}" if need else \
                f"NEVER (all {observed} observed configs insufficient)"
            print(f"\n  Delta/J = {ratio:.2f}:")
            print(f"    shots kept in sector: {kept}/{total} = {kept/total:.1%} "
                  f"(discarded {1-kept/total:.1%} -- broken charge conservation)")
            print(f"    distinct in-sector configurations observed: {observed}/{DIM}")
            print(f"    dim needed for 1% ground energy: {frac_str}")
            print(f"    ideal-Trotter pre-registered prediction: "
                  f"{rec['prediction'][str(ratio)]}")
            out[str(ratio)] = dict(kept=kept, total=total, observed=int(observed),
                                   dim_needed=need,
                                   frac=(need / DIM) if need else None)
        results[bname] = out
    if results:
        with open(os.path.join(REPO, "evidence/skqd_hw_result.json"), "w") as fh:
            json.dump(results, fh, indent=2)
        print("\nwrote evidence/skqd_hw_result.json")
    sys.exit(0)

# ============================ PRE-FLIGHT ============================
print("=" * 78)
print(f"PRE-FLIGHT -- the protocol on TROTTERIZED statevectors (reps={REPS}), so the")
print("hardware run differs from this reference by device noise only")
print("=" * 78)
RNG = np.random.default_rng(2026)
from qiskit.quantum_info import Statevector
PRED = {}
for ratio in RATIOS:
    Hc = build_Hc(ratio)
    ev = np.linalg.eigvalsh(Hc); e0 = float(ev[0])
    counts = np.zeros(DIM)
    oos = 0
    for t in TIMES:
        qc = circuit(ratio, t); qc.remove_final_measurements(inplace=True)
        # transpile to basis gates FIRST: Statevector on an un-synthesised
        # PauliEvolutionGate evaluates the EXACT evolution, not the Trotter product
        # (BUGLOG B07's hazard), and is also far slower at n=12
        qc = transpile(qc, basis_gates=["rz", "sx", "x", "cx"],
                       optimization_level=1, seed_transpiler=0)
        p = np.abs(np.asarray(Statevector(qc).data)) ** 2
        p /= p.sum()
        draw = RNG.choice(2 ** N, size=SHOTS, p=p)
        for m in draw:
            if m in INDEX:
                counts[INDEX[m]] += 1
            else:
                oos += 1                  # Trotter conserves Q exactly -> expect 0
    need, observed = dim_needed(counts, Hc, e0)
    frac_str = f"{need}/{DIM} = {need/DIM:.1%}" if need else \
        f"NEVER (all {observed} observed insufficient)"
    PRED[str(ratio)] = frac_str
    print(f"  Delta/J {ratio:.2f}: out-of-sector draws {oos} (want 0); "
          f"observed {observed}/{DIM}; dim needed: {frac_str}")
assert PRED[str(RATIOS[1])] != PRED[str(RATIOS[0])], "boundary invisible ideally -- stop"
print("  PRE-FLIGHT PASSED: boundary ordering present in the ideal-Trotter reference\n")

if "--dry-run" in sys.argv and not [a for a in sys.argv if a.startswith("ibm_")]:
    print("dry run: statevector only, no backend contacted"); sys.exit(0)

# ============================ TRANSPILE + SUBMIT ============================
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
svc = QiskitRuntimeService()
targets = [a for a in sys.argv[1:] if a.startswith("ibm_")]
assert targets, "give a backend, e.g. ibm_marrakesh"
backend = svc.backend(targets[0])
TWOQ = sorted({nme for nme, inst in backend.target.items()
               if inst and any(k is not None and len(k) == 2 for k in inst)}
              - {"measure", "delay", "reset", "barrier"})

circuits, meta = [], []
for ratio in RATIOS:
    for t in TIMES:
        tq = transpile(circuit(ratio, t), backend, optimization_level=1,
                       seed_transpiler=2026)
        n2 = sum(v for k, v in tq.count_ops().items() if k in TWOQ)
        circuits.append(tq); meta.append(dict(ratio=ratio, t=t, two_q=int(n2)))
med = int(np.median([m["two_q"] for m in meta]))
print(f"transpiled {len(circuits)} circuits on {backend.name}: median {med} 2q gates, "
      f"max depth {max(c.depth() for c in circuits)}")

if "--dry-run" in sys.argv:
    print("dry run -- nothing submitted"); sys.exit(0)

sampler = SamplerV2(mode=backend)
job = sampler.run(circuits, shots=SHOTS)
out = json.load(open(JOB_PATH)) if os.path.exists(JOB_PATH) else {"jobs": {}}
out.setdefault("jobs", {})[backend.name] = dict(
    job_id=job.job_id(), n=N, ratios=list(RATIOS), times=list(TIMES), shots=SHOTS,
    reps=REPS, meta=meta, prediction=PRED)
with open(JOB_PATH, "w") as fh:
    json.dump(out, fh, indent=2)
print(f"\nsubmitted {len(circuits)} circuits x {SHOTS} shots to {backend.name}")
print(f"job {job.job_id()}  ->  evidence/skqd_hw_job.json  (fetch with --fetch)")
