"""TRACK B ON REAL HARDWARE -- feasibility sizing, done BEFORE any QPU time is spent.

Track B (anti-controlled Hadamard test) has never run on a QPU in this project: the
hardware rows so far are Part A (R008 frozen, R023 2-site, R026 4-site, R031 teammate)
plus Track E / SQD rows that REUSE R023's shots. On the frozen 3-site benchmark Track B is
hopeless on hardware -- R034 measured 344/588/1076 CX at reps 1/2/4, against R008's finding
that 435 CX already collapses the signal to 0.18-0.37 survival.

The 2-site side model is the opening: R023 got 15 CX / depth 64 for the ORDINARY controlled
evolution there and a clean result (chi survival 0.962, <Q> survival 0.957). Track B carries
BOTH evolutions, so the question this script answers with real transpiled numbers -- not
estimates -- is whether the doubled circuit still fits inside the coherence budget.

Nothing here submits. It prints gate counts and a falsifiable survival prediction.
"""
import os
# repo root derived from this file, so the script runs from any clone/checkout
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
sys.path.insert(0, REPO)
from hardware_run import load_notebook_definitions, get_model

import json
import numpy as np
from qiskit import transpile

ns = load_notebook_definitions()
QC, QR = ns["QuantumCircuit"], ns["QuantumRegister"]
CR = ns["ClassicalRegister"]
SV, OP = ns["Statevector"], ns["Operator"]
PHI_RE, PHI_IM = ns["PHI_RE"], ns["PHI_IM"]

N2, H2, Q2, PREP2, PSI2, LABEL2 = get_model(ns, "2site")
print(f"model: {LABEL2}  (n_sys={N2})")


def build_ab(t, phi, w_kind, reps_w=1, basis=None, measure=False):
    """W on the |0> ancilla branch, U=exact on the |1> branch.
    <Z_a>_phi = Re[e^{i phi} <psi| W^dag U |psi>]  (derivation in track_b_ab_tester.py)."""
    sys_reg, anc = QR(N2, "sys"), QR(1, "anc")
    qc = QC(sys_reg, anc)
    qc.compose(PREP2, qubits=sys_reg, inplace=True)
    qc.h(anc[0])
    qc.x(anc[0])                                              # anti-control W
    if w_kind == "trotter":
        qc.append(ns["build_controlled_evolution"](H2, t, "trotter", reps_w),
                  [anc[0], *sys_reg])
    elif w_kind == "identity":
        pass                                                  # W = I -> ordinary test
    else:
        raise ValueError(w_kind)
    qc.x(anc[0])
    qc.append(ns["build_controlled_evolution"](H2, t, "exact"), [anc[0], *sys_reg])
    if phi != 0.0:
        qc.p(phi, anc[0])
    qc.h(anc[0])
    if basis is not None:                                     # shadow rotations
        for j, b in enumerate(basis):
            if b == 0:
                qc.h(sys_reg[j])
            elif b == 1:
                qc.sdg(sys_reg[j]); qc.h(sys_reg[j])
    if measure:
        creg = CR(N2 + 1, "c")
        qc.add_register(creg)
        qc.measure(sys_reg, creg[:N2]); qc.measure(anc[0], creg[N2])
    return qc


# ---------------- 1. identity check on the 2-site model, before anything else -------------
print("\n" + "=" * 74)
print("1. STATEVECTOR IDENTITY  chi_AB(t) = <psi| W(t)^dag U(t) |psi>   (2-site model)")
print("=" * 74)
worst = 0.0
for t in (0.0, 0.9, 1.8, 2.7):
    for reps in (1, 2):
        dim = 2 ** N2
        # The gate is appended as [anc, *sys], so within the GATE's own operator the control
        # is qubit 0 -- the LEAST significant bit in Qiskit's ordering. The |1>-control block
        # is therefore the odd-index sublattice [1::2, 1::2], NOT the upper half. (Taking the
        # upper half is the endianness trap CONVENTIONS warns about; it passes at t=0, where
        # both branches are the identity, and fails everywhere else.)
        Umat = OP(ns["build_controlled_evolution"](H2, t, "exact")).data[1::2, 1::2]
        W = OP(ns["build_controlled_evolution"](H2, t, "trotter", reps)).data[1::2, 1::2]
        want = complex(PSI2.conj() @ (W.conj().T @ Umat) @ PSI2)
        got = []
        for phi in (PHI_RE, PHI_IM):
            qc = build_ab(t, phi, "trotter", reps)
            psi_out = SV(qc).data
            # <Z_a>: ancilla is the HIGHEST qubit index -> first half |0>, second half |1>
            p = np.abs(psi_out) ** 2
            got.append(float(p[:dim].sum() - p[dim:].sum()))
        dev = abs(complex(got[0], got[1]) - want)
        worst = max(worst, dev)
        print(f"   t={t:4.1f} reps={reps}  measured {complex(got[0],got[1]):+.6f}   "
              f"exact {want:+.6f}   dev {dev:.2e}")
print(f"\n   worst deviation {worst:.3e}  ->  "
      f"{'IDENTITY CONFIRMED' if worst < 1e-10 else 'FAILED -- do not submit'}")
assert worst < 1e-10, "Track B identity does not hold on the 2-site model; stop."

# ---------------- 2. transpiled cost against the real backend ----------------
print("\n" + "=" * 74)
print("2. TRANSPILED COST ON REAL HARDWARE")
print("=" * 74)
from qiskit_ibm_runtime import QiskitRuntimeService


def two_qubit_ops(backend):
    """Names of the backend's 2-qubit basis gates, read from its target rather than guessed.

    Hardcoding ("cz","ecr","cx") silently returns an EMPTY list on any device with a
    different 2q basis -- and then every gate count reads 0 and every survival reads 1.000,
    which is exactly the failure you cannot catch on a machine you have no access to.
    So: derive it, and refuse to continue if nothing is found."""
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
svc = QiskitRuntimeService()          # saved account, same path hardware_run.py uses
backend = svc.backend(sys.argv[1] if len(sys.argv) > 1 else "ibm_kingston")
props = backend.properties()
TWOQ = two_qubit_ops(backend)
print(f"backend {backend.name}, {backend.num_qubits} qubits, 2q basis {TWOQ}\n")


def survival(tqc):
    """Product of (1 - error) over the 2q gates the transpiled circuit ACTUALLY uses, with
    each edge's own calibrated error. Averaging over arbitrary coupling-map edges instead
    gives ~5e-2 here, which would contradict R023's measured 0.962 survival at 15 gates."""
    p, n, errs = 1.0, 0, []
    for inst in tqc.data:
        if inst.operation.name in TWOQ:
            q = [tqc.find_bit(b).index for b in inst.qubits]
            e = props.gate_error(inst.operation.name, q)
            p *= (1 - e); n += 1; errs.append(e)
    return p, n, (float(np.median(errs)) if errs else 0.0)


rows = []
for label, kind, reps in (("ordinary test (R023 baseline)", "identity", 0),
                          ("A/B  W=Trotter reps=1", "trotter", 1),
                          ("A/B  W=Trotter reps=2", "trotter", 2)):
    qc = build_ab(0.9, PHI_RE, kind, reps, basis=[2] * N2, measure=True)
    tqc = transpile(qc, backend, optimization_level=3, seed_transpiler=2026)
    surv, n2q, med = survival(tqc)
    rows.append(dict(label=label, depth=tqc.depth(), two_q=n2q,
                     median_edge_error=med, predicted_survival=surv))
    print(f"  {label:<30} depth {tqc.depth():>4}   2q gates {n2q:>4}   "
          f"median edge err {med:.2e}   predicted survival {surv:.3f}")

print(f"\n  sanity: R023 measured chi survival 0.962 on this backend at 15 two-qubit gates;")
print(f"  the baseline row above should land near that, or the model is wrong.")

# gate error alone ignores T1/T2, and R008 found DEPTH dominates device quality, so the
# numbers above are an upper bound. Put a duration-vs-coherence figure next to them.
print("\n  Decoherence check (gate error alone is an upper bound on survival):")
t1s = []
for q in range(backend.num_qubits):
    try:                                   # some qubits have no calibrated T1
        v = props.t1(q)
        if v:
            t1s.append(v)
    except Exception:
        pass
med_t1 = float(np.median(t1s))
for r, (label, kind, reps) in zip(rows, (("ordinary test (R023 baseline)", "identity", 0),
                                         ("A/B  W=Trotter reps=1", "trotter", 1),
                                         ("A/B  W=Trotter reps=2", "trotter", 2))):
    qc = build_ab(0.9, PHI_RE, kind, reps, basis=[2] * N2, measure=True)
    tqc = transpile(qc, backend, optimization_level=3, seed_transpiler=2026,
                    scheduling_method="alap")
    dur = tqc.duration * backend.dt if tqc.duration else float("nan")
    r["duration_s"] = float(dur); r["median_T1_s"] = med_t1
    r["duration_over_T1"] = float(dur / med_t1)
    print(f"  {label:<30} duration {dur*1e6:7.1f} us   median T1 {med_t1*1e6:6.1f} us   "
          f"t/T1 = {dur/med_t1:.3f}")
print("\n  Prediction recorded BEFORE submission, and deliberately stated as a RANGE:")
print("  gate-error-only survival is the optimistic end; multiply by roughly exp(-t/T1)")
print("  per active qubit for the pessimistic end. R023's baseline came in at 0.962")
print("  against a 0.984 gate-error prediction, i.e. the model ran ~2% optimistic there.")
with open(os.path.join(REPO, "evidence/track_b_hw_sizing.json"),
          "w") as fh:
    json.dump(dict(backend=backend.name, two_q_basis=TWOQ,
                   identity_worst_dev=worst, rows=rows), fh, indent=2)
print("\nwrote evidence/track_b_hw_sizing.json")
