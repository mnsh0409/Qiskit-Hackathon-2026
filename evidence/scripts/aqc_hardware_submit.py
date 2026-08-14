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

N = 6                            # override with --n (7 supported; FIELDS covers it)
if "--n" in sys.argv:
    N = int(sys.argv[sys.argv.index("--n") + 1])
TIMES = (0.3, 0.6, 0.9)
SHOTS = 4000                     # override with --shots N
# The exact arm exists only to be dead (it is the control), yet at equal shots it eats 77%
# of the job's quantum seconds (602 us/shot at n=6). --cheap keeps its role but not its
# bill: 500 shots still resolves 'noise vs signal' at the +-0.045 level, plenty to certify
# a corpse. Use for paid-plan runs (e.g. ibm_miami / Nighthawk via the teammate account).
EXACT_SHOTS = None               # --cheap sets 500
if "--shots" in sys.argv:
    SHOTS = int(sys.argv[sys.argv.index("--shots") + 1])
if "--cheap" in sys.argv:
    EXACT_SHOTS = 500
FIELDS = [0.40, -0.50, 0.15, 0.20, -0.30, 0.10, 0.25]   # 7 entries: supports --n 7
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
# statevector-only when no backend named: the old check (len(sys.argv)==2) silently fell
# through to a real backend query the moment any other flag (--n, --shots) was present.
if "--dry-run" in sys.argv and not [a for a in sys.argv if a.startswith("ibm_")]:
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
if EXACT_SHOTS is None:
    job = sampler.run(circuits, shots=SHOTS)
else:
    pubs = [(c, None, EXACT_SHOTS if m["arm"] == "exact" else SHOTS)
            for c, m in zip(circuits, meta)]
    est = sum(m["two_q"] * 68e-9 * (EXACT_SHOTS if m["arm"] == "exact" else SHOTS)
              for m in meta)
    print(f"  --cheap: exact arm at {EXACT_SHOTS} shots; rough execution estimate "
          f"{est:.1f} s of circuit time (vs {sum(m['two_q']*68e-9*SHOTS for m in meta):.1f} s)")
    job = sampler.run(pubs)
# MERGE into any existing record. Writing a fresh dict here silently destroyed the
# marrakesh job id the moment the same script was pointed at a second backend.
path = os.path.join(REPO, "evidence/aqc_hw_job.json")
out = json.load(open(path)) if os.path.exists(path) else {}
out.update(n=N, times=list(TIMES), shots=SHOTS, meta=meta,
           aqc={str(t): dict(theta=AQC[t][1], infidelity=AQC[t][2]) for t in TIMES},
           chi_exact={str(t): [chi_exact(t).real, chi_exact(t).imag] for t in TIMES})
# Each job entry is SELF-CONTAINED (n, meta, exact references): the top-level fields are
# whatever the LAST submit wrote, so an n=7 submit would silently corrupt the analysis of
# an earlier n=6 job fetched afterwards.
# KEY BUG FIXED (2026-08-14): the key used to be backend+n only, so a shots-only rerun at
# the default n=6 (e.g. a shots-trend sweep) would silently overwrite the earlier job at a
# different shot count on the same backend/n -- same class of clobber as the backend/n bug
# above, just on the axis that bug didn't cover. Shots is now part of the key too.
job_key = backend.name + (f"_n{N}" if N != 6 else "") + (f"_s{SHOTS}" if SHOTS != 4000 else "")
out.setdefault("jobs", {})[job_key] = dict(
    job_id=job.job_id(), prediction=pred, n=N, shots=SHOTS, exact_shots=EXACT_SHOTS,
    meta=meta,
    chi_exact={str(t): [chi_exact(t).real, chi_exact(t).imag] for t in TIMES})
with open(path, "w") as fh:
    json.dump(out, fh, indent=2)
shots_desc = (f"{SHOTS} shots" if EXACT_SHOTS is None
              else f"{SHOTS} shots ({EXACT_SHOTS} on the exact arm)")
print(f"\nsubmitted {len(circuits)} circuits x {shots_desc} to {backend.name}")
print(f"job {job.job_id()}  ->  evidence/aqc_hw_job.json")
