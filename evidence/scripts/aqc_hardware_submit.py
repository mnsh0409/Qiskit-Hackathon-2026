"""AQC ON A QPU: run the circuit that should not fit, next to the one that should not work.

R046/R052 are compilation claims -- gate counts. This turns one into a measurement. At n=6
system qubits the three ways to build a Hadamard test's controlled evolution are, routed onto
the real device:

  A  exact controlled block   ~8850 two-qubit gates   predicted survival ~4e-6  (dead)
  B  controlled Trotter r=2   ~2500                   predicted survival ~0.03  (mostly dead)
  C  controlled AQC + P(-th)  ~576                    predicted survival ~0.45  (usable)

If the compilation claim means anything, C returns a recognisable chi(t) and A returns noise.
That is the whole experiment.

THE PHASE CORRECTION IS NOT OPTIONAL. AQC-Tensor optimises state fidelity, which is blind to
global phase, and a Hadamard test measures exactly that phase (R046). Every AQC arm here
carries its P(-theta) on the ancilla, with theta computed at compile time. Submitting without
it would return a chi wrong by ~3 radians and the run would be worthless.

Nothing is submitted until the statevector identity passes for all three arms.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json
sys.path.insert(0, REPO)
from hardware_run import load_notebook_definitions

import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit.quantum_info import Operator, Statevector
from qiskit_addon_aqc_tensor.ansatz_generation import generate_ansatz_from_circuit
from qiskit_addon_aqc_tensor.objective import OneMinusFidelity
from qiskit_addon_aqc_tensor.simulation import tensornetwork_from_circuit
from qiskit_addon_aqc_tensor.simulation.quimb import QuimbSimulator
import quimb.tensor

ns = load_notebook_definitions()
SPO = ns["SparsePauliOp"]
PHI_RE, PHI_IM = ns["PHI_RE"], ns["PHI_IM"]
sim = QuimbSimulator(quimb.tensor.CircuitMPS, autodiff_backend="jax")

N = 6
TIMES = (0.3, 0.6, 0.9)
SHOTS = 4000
FIELDS = [0.40, -0.50, 0.15, 0.20, -0.30, 0.10]
BONDS = [(i, i + 1) for i in range(N - 1)]


def ham():
    t = []
    for i, j in BONDS:
        t += [("XX", [i, j], 0.65), ("YY", [i, j], 0.65), ("ZZ", [i, j], 0.25)]
    t += [("Z", [i], FIELDS[i]) for i in range(N)]
    return SPO.from_sparse_list(t, num_qubits=N).simplify()


H = ham()
PREP = QuantumCircuit(N); PREP.ry(1.3, 0)
PSI = np.asarray(Statevector(PREP).data)


def trot(t, reps):
    qc = QuantumCircuit(N)
    qc.append(ns["PauliEvolutionGate"](H, time=t,
              synthesis=ns["SuzukiTrotter"](order=2, reps=reps)), range(N))
    return transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
                     seed_transpiler=0)


def compile_aqc(t):
    """Compress the evolution at time t and return (circuit, theta, state infidelity).
    theta is the global phase the fidelity objective is blind to; it is cancelled on the
    ancilla, and is available here for free from the same simulation that produced W."""
    a, init = generate_ansatz_from_circuit(trot(t, 1), qubits_initially_zero=True)
    ft = QuantumCircuit(N); ft.compose(PREP, inplace=True); ft.compose(trot(t, 3), inplace=True)
    fa = QuantumCircuit(N); fa.compose(PREP, inplace=True); fa.compose(a, inplace=True)
    res = minimize(OneMinusFidelity(tensornetwork_from_circuit(ft, sim), fa, sim),
                   np.array(init), jac=True, method="L-BFGS-B", options={"maxiter": 400})
    bound = a.assign_parameters(res.x)
    W = Operator(bound).data
    U = ns["exact_unitary"](H, t)
    theta = float(np.angle(np.vdot(U @ PSI, W @ PSI)))
    infid = 1 - abs(np.vdot(W @ PSI, U @ PSI))
    return bound, theta, float(infid)


def hadamard_test(t, phi, arm, aqc=None, theta=0.0, measure=True):
    """Standard Hadamard test; the controlled evolution is built one of three ways."""
    sys_reg, anc = QuantumRegister(N, "sys"), QuantumRegister(1, "anc")
    qc = QuantumCircuit(sys_reg, anc)
    qc.compose(PREP, qubits=sys_reg, inplace=True)
    qc.h(anc[0])
    if arm == "exact":
        qc.append(ns["build_controlled_evolution"](H, t, "exact"), [anc[0], *sys_reg])
    elif arm == "trotter":
        qc.append(ns["build_controlled_evolution"](H, t, "trotter", 2), [anc[0], *sys_reg])
    elif arm == "aqc":
        qc.append(aqc.to_gate().control(1), [anc[0], *sys_reg])
        qc.p(-theta, anc[0])            # cancel the phase the objective could not see
    if phi != 0.0:
        qc.p(phi, anc[0])
    qc.h(anc[0])
    if measure:
        creg = ClassicalRegister(1, "c"); qc.add_register(creg)
        qc.measure(anc[0], creg[0])
    return qc


def chi_exact(t):
    return complex(PSI.conj() @ ns["exact_unitary"](H, t) @ PSI)


# ============================ PRE-FLIGHT ============================
print("=" * 78)
print("PRE-FLIGHT -- all three arms must reproduce chi(t) on the statevector")
print("=" * 78)
AQC = {}
worst = {"exact": 0.0, "trotter": 0.0, "aqc": 0.0}
for t in TIMES:
    AQC[t] = compile_aqc(t)
    print(f"  t={t}: AQC compiled, state infidelity {AQC[t][2]:.2e}, "
          f"theta={AQC[t][1]:+.4f} rad")
    for arm in ("exact", "trotter", "aqc"):
        got = []
        for phi in (PHI_RE, PHI_IM):
            qc = hadamard_test(t, phi, arm, AQC[t][0], AQC[t][1], measure=False)
            p = np.abs(np.asarray(Statevector(qc).data)) ** 2
            d = 2 ** N
            got.append(float(p[:d].sum() - p[d:].sum()))
        dev = abs(complex(*got) - chi_exact(t))
        worst[arm] = max(worst[arm], dev)
print(f"\n  worst |chi_circuit - chi_exact|:  exact {worst['exact']:.2e},  "
      f"trotter {worst['trotter']:.2e},  AQC+phase {worst['aqc']:.2e}")
assert worst["exact"] < 1e-9, "the exact arm is not exact -- stop"
assert worst["aqc"] < 0.05, "AQC arm is off even ideally -- do not spend QPU time"
print("  PRE-FLIGHT PASSED (the Trotter arm carries genuine product-formula error, "
      "as it should)\n")

# ============================ COST + PREDICTION ============================
if "--dry-run" in sys.argv and len(sys.argv) == 2:
    print("dry run: statevector only, no backend contacted"); sys.exit(0)

from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
svc = QiskitRuntimeService()
targets = [a for a in sys.argv[1:] if a.startswith("ibm_")]
backend = svc.backend(targets[0] if targets else "ibm_marrakesh")
props = backend.properties()
TWOQ = sorted({n for n, inst in backend.target.items()
               if inst and any(k is not None and len(k) == 2 for k in inst)}
              - {"measure", "delay", "reset", "barrier"})
print("=" * 78)
print(f"TRANSPILED COST AND PREDICTION on {backend.name}  (2q basis {TWOQ})")
print("=" * 78)

circuits, meta = [], []
pred = {}
for arm in ("exact", "trotter", "aqc"):
    per = []
    for t in TIMES:
        for phi, tag in ((PHI_RE, "re"), (PHI_IM, "im")):
            qc = hadamard_test(t, phi, arm, AQC[t][0], AQC[t][1])
            tq = transpile(qc, backend, optimization_level=1, seed_transpiler=2026)
            n2 = sum(v for k, v in tq.count_ops().items() if k in TWOQ)
            circuits.append(tq); meta.append(dict(arm=arm, t=t, phi=tag, two_q=int(n2)))
            per.append(n2)
    med = float(np.median(per))
    # survival from the median edge error actually used, as in R042
    errs = []
    for inst in circuits[-1].data:
        if inst.operation.name in TWOQ:
            q = [circuits[-1].find_bit(b).index for b in inst.qubits]
            try:
                errs.append(props.gate_error(inst.operation.name, q))
            except Exception:
                pass
    e = float(np.median(errs)) if errs else 1.4e-3
    surv = (1 - e) ** med
    pred[arm] = dict(median_2q=med, median_edge_error=e, predicted_survival=float(surv))
    print(f"  {arm:>8}: median {med:>8.0f} two-qubit gates   "
          f"predicted |chi| survival {surv:.2e}")

print("\n  PREDICTION, recorded before submission and falsifiable:")
print(f"    exact arm returns noise (survival {pred['exact']['predicted_survival']:.1e});")
print(f"    AQC arm returns a recognisable chi(t) (survival "
      f"{pred['aqc']['predicted_survival']:.2f}).")
print(f"    If the AQC arm is ALSO noise, the compilation advantage does not translate to")
print(f"    hardware at this size, and we report that.")

if "--dry-run" in sys.argv:
    print("\ndry run -- nothing submitted"); sys.exit(0)

sampler = SamplerV2(mode=backend)
job = sampler.run(circuits, shots=SHOTS)
out = dict(backend=backend.name, n=N, times=list(TIMES), shots=SHOTS, meta=meta,
           prediction=pred, job_id=job.job_id(),
           aqc={str(t): dict(theta=AQC[t][1], infidelity=AQC[t][2]) for t in TIMES},
           chi_exact={str(t): [chi_exact(t).real, chi_exact(t).imag] for t in TIMES})
with open(os.path.join(REPO, "evidence/aqc_hw_job.json"), "w") as fh:
    json.dump(out, fh, indent=2)
print(f"\nsubmitted {len(circuits)} circuits x {SHOTS} shots to {backend.name}")
print(f"job {job.job_id()}  ->  evidence/aqc_hw_job.json")
