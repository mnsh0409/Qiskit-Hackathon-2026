"""FOLLOW-UP TO R044 (p.20/21): does the Track B hardware picture hold over a LONGER time
window, or was t <= 2.7 too short to see anything change?

R044 measured chi_AB(t), the per-observable W/U profile, and the free error bar
<Q>_W - <Q>_U at t = 0.0, 0.9, 1.8, 2.7 on ibm_marrakesh + ibm_kingston. That is one Trotter
period and a bit; whether the echo's lead over our arm grows, shrinks, or holds, and
whether the conserved-charge error bar stays flat as the circuit gets no deeper (arm cost is
t-independent here -- only the ROTATION ANGLE changes with t, not the gate count) were never
measured past t=2.7.

Deliberately a SEPARATE script and SEPARATE evidence files (track_b_hw_jobs_ext.json,
track_b_hw_result_ext.json), not a parameterised rerun of track_b_hardware_submit.py:
that script's downstream chart generator (make_trackb_charts.py) reads
evidence/track_b_hw_result.json as a single-job LIST and evidence/track_b_hw_jobs.json's
TOP-LEVEL exact_reference as one global TIMES -- both assumptions that a second job with a
different TIMES tuple would break. Keeping this fully separate means R044's existing
evidence and p.20/21 figures are untouched no matter what this run finds.

Circuits, model, arms (A/B/C/D) and the pre-flight identity check are identical to
track_b_hardware_submit.py -- only TIMES is extended, from (0.0, 0.9, 1.8, 2.7) to
(0.0, 0.9, 1.8, 2.7, 3.6, 4.5, 5.4), i.e. 3 more points at the same 0.9 step, taking the
window from ~1 Trotter period to ~2.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json
sys.path.insert(0, REPO)
from hardware_run import load_notebook_definitions, get_model

import numpy as np
import itertools
from qiskit import transpile

ns = load_notebook_definitions()
QC, QR, CR = ns["QuantumCircuit"], ns["QuantumRegister"], ns["ClassicalRegister"]
SV, OP, SPO = ns["Statevector"], ns["Operator"], ns["SparsePauliOp"]
PHI_RE, PHI_IM = ns["PHI_RE"], ns["PHI_IM"]

N2, H2, Q2, PREP2, PSI2, LABEL2 = get_model(ns, "2site")
TIMES = (0.0, 0.9, 1.8, 2.7, 3.6, 4.5, 5.4)          # R044's 4 points + 3 more, same step
REPS_W = 1
SHOTS = 1000                                          # identical to R044, for a fair compare
BASES = list(itertools.product(range(3), repeat=N2))

OBS = {
    "Z_0":       SPO.from_sparse_list([("Z", [0], 1.0)], num_qubits=N2),
    "Z_1":       SPO.from_sparse_list([("Z", [1], 1.0)], num_qubits=N2),
    "Z_0Z_1":    SPO.from_sparse_list([("ZZ", [0, 1], 1.0)], num_qubits=N2),
    "X0X1+Y0Y1": SPO.from_sparse_list([("XX", [0, 1], 1.0), ("YY", [0, 1], 1.0)],
                                      num_qubits=N2),
    "H":         H2,
    "Q":         Q2,
}


def build(t, phi, basis, final_hadamard):
    sys_reg, anc = QR(N2, "sys"), QR(1, "anc")
    qc = QC(sys_reg, anc)
    qc.compose(PREP2, qubits=sys_reg, inplace=True)
    qc.h(anc[0])
    qc.x(anc[0])                                                    # anti-control W
    qc.append(ns["build_controlled_evolution"](H2, t, "trotter", REPS_W), [anc[0], *sys_reg])
    qc.x(anc[0])
    qc.append(ns["build_controlled_evolution"](H2, t, "exact"), [anc[0], *sys_reg])
    if phi != 0.0:
        qc.p(phi, anc[0])
    if final_hadamard:
        qc.h(anc[0])
    for j, b in enumerate(basis):                                   # shadow rotations
        if b == 0:
            qc.h(sys_reg[j])
        elif b == 1:
            qc.sdg(sys_reg[j]); qc.h(sys_reg[j])
    creg = CR(N2 + 1, "c")
    qc.add_register(creg)
    qc.measure(sys_reg, creg[:N2]); qc.measure(anc[0], creg[N2])
    return qc


def blocks(t):
    """W(t) and U(t) as system-register matrices. Same convention as track_b_hardware_submit.py:
    the |1>-control block is the odd sublattice [1::2, 1::2] (ancilla is the LEAST significant
    bit of the appended [anc, *sys] register), not the upper half -- the bug R042 caught."""
    U = OP(ns["build_controlled_evolution"](H2, t, "exact")).data[1::2, 1::2]
    W = OP(ns["build_controlled_evolution"](H2, t, "trotter", REPS_W)).data[1::2, 1::2]
    return W, U


# ============================ PRE-FLIGHT: validate arm B ============================
print("=" * 76)
print("PRE-FLIGHT -- arm B identity on the statevector, before any QPU time")
print("=" * 76)
worst = 0.0
for t in TIMES:
    W, U = blocks(t)
    rho_w = np.outer(W @ PSI2, (W @ PSI2).conj())
    rho_u = np.outer(U @ PSI2, (U @ PSI2).conj())
    for name, o in OBS.items():
        om = o.to_matrix()
        want_sum = float(np.real(np.trace(om @ (rho_w + rho_u)) / 2))
        want_dif = float(np.real(np.trace(om @ (rho_w - rho_u)) / 2))
        qc = build(t, 0.0, (2,) * N2, final_hadamard=False)
        qc.remove_final_measurements(inplace=True)
        full = SV(qc).data
        dim = 2 ** N2
        amp0, amp1 = full[:dim], full[dim:]
        got_sum = float(np.real(amp0.conj() @ om @ amp0 + amp1.conj() @ om @ amp1))
        got_dif = float(np.real(amp0.conj() @ om @ amp0 - amp1.conj() @ om @ amp1))
        worst = max(worst, abs(got_sum - want_sum), abs(got_dif - want_dif))
print(f"  worst deviation over {len(TIMES)} times x {len(OBS)} observables: {worst:.3e}")
assert worst < 1e-10, "arm B identity failed -- do not spend QPU time"
print("  ARM B IDENTITY CONFIRMED over the extended time window\n")

REF = {}
for t in TIMES:
    W, U = blocks(t)
    REF[str(t)] = {
        "chi_AB": [float(np.real(PSI2.conj() @ (W.conj().T @ U) @ PSI2)),
                   float(np.imag(PSI2.conj() @ (W.conj().T @ U) @ PSI2))],
        "echo_p0": float(abs(PSI2.conj() @ (W.conj().T @ U) @ PSI2) ** 2),
        "hst_p0": float(abs(np.trace(W.conj().T @ U) / (2 ** N2)) ** 2),
        "obs": {k: {"W": float(np.real((W @ PSI2).conj() @ o.to_matrix() @ (W @ PSI2))),
                    "U": float(np.real((U @ PSI2).conj() @ o.to_matrix() @ (U @ PSI2)))}
                for k, o in OBS.items()}}


def build_echo(t):
    from qiskit.circuit.library import PauliEvolutionGate
    from qiskit.synthesis import SuzukiTrotter
    W_, U_ = blocks(t)
    trot = QC(N2)
    trot.append(PauliEvolutionGate(H2, time=t, synthesis=SuzukiTrotter(order=2, reps=REPS_W)),
                range(N2))
    qc = QC(N2)
    qc.compose(PREP2, inplace=True)
    qc.unitary(U_, range(N2))
    qc.compose(trot.inverse(), inplace=True)
    qc.compose(PREP2.inverse(), inplace=True)
    qc.measure_all()
    return qc


def build_hst(t):
    W_, U_ = blocks(t)
    qc = QC(2 * N2)
    for j in range(N2):
        qc.h(j); qc.cx(j, N2 + j)
    qc.unitary(U_, range(N2))
    qc.unitary(W_.conj(), range(N2, 2 * N2))
    for j in range(N2):
        qc.cx(j, N2 + j); qc.h(j)
    qc.measure_all()
    return qc


circuits, meta = [], []
for t in TIMES:
    for basis in BASES:
        for phi, tag in ((PHI_RE, "re"), (PHI_IM, "im")):
            circuits.append(build(t, phi, basis, True))
            meta.append(dict(arm="A", t=t, basis=list(basis), phi=tag))
        circuits.append(build(t, 0.0, basis, False))
        meta.append(dict(arm="B", t=t, basis=list(basis), phi="re"))
for t in TIMES:
    circuits.append(build_echo(t)); meta.append(dict(arm="C_echo", t=t))
    circuits.append(build_hst(t));  meta.append(dict(arm="D_hst", t=t))
print(f"job: {len(circuits)} circuits x {SHOTS} shots = {len(circuits)*SHOTS:,} shots "
      f"({len(TIMES)} times, vs R044's 4)")
for a in ("A", "B", "C_echo", "D_hst"):
    print(f"     arm {a:<7} {sum(m['arm']==a for m in meta):>3} circuits")
print()

if "--dry-run" in sys.argv:
    print("dry run -- nothing submitted"); sys.exit(0)

from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2


def two_qubit_ops(backend):
    names = set()
    try:
        for name, inst in backend.target.items():
            if inst and any(k is not None and len(k) == 2 for k in inst):
                names.add(name)
    except Exception:
        pass
    names -= {"measure", "delay", "reset", "barrier"}
    if not names:
        names = {g for g in ("cz", "ecr", "cx") if g in backend.operation_names}
    assert names, (f"could not identify a 2-qubit basis gate on {backend.name}; "
                   f"operations = {sorted(backend.operation_names)}")
    return sorted(names)


svc = QiskitRuntimeService()
targets = [a for a in sys.argv[1:] if a.startswith("ibm_")]
assert targets, "give at least one backend, e.g. ibm_marrakesh"

# Own dedicated file, written fresh: no merge needed because nothing else writes here and
# R044's evidence/track_b_hw_jobs.json is never opened, let alone touched, by this script.
out = {"model": "2site", "reps_w": REPS_W, "times": list(TIMES), "shots": SHOTS,
       "bases": [list(b) for b in BASES], "meta": meta, "exact_reference": REF, "jobs": {}}
for name in targets:
    backend = svc.backend(name)
    tqcs = transpile(circuits, backend, optimization_level=3, seed_transpiler=2026)
    twoq = two_qubit_ops(backend)
    n2q = [sum(v for k, v in c.count_ops().items() if k in twoq) for c in tqcs]
    sampler = SamplerV2(mode=backend)
    job = sampler.run(tqcs, shots=SHOTS)
    out["jobs"][name] = dict(job_id=job.job_id(), max_2q=int(max(n2q)),
                             median_2q=int(np.median(n2q)), max_depth=int(max(c.depth() for c in tqcs)))
    print(f"  {name}: job {job.job_id()}  median 2q {int(np.median(n2q))}  "
          f"max depth {max(c.depth() for c in tqcs)}")

with open(os.path.join(REPO, "evidence/track_b_hw_jobs_ext.json"), "w") as fh:
    json.dump(out, fh, indent=2)
print("\nwrote evidence/track_b_hw_jobs_ext.json  "
      "(fetch with track_b_hardware_time_extend_fetch.py)")
