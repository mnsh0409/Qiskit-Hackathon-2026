"""THE PHASE TRAP ON REAL HARDWARE: fix-on vs fix-off, same job -- paper 1's missing leg.

Every hardware AQC arm so far (R054/R058) already carried the P(-theta) phase fix, so the
trap itself -- paper 1's central claim -- has only ever been demonstrated on the
statevector. It could not be shown at n=6: everything decoheres to noise there, and a
rotated noise blob is indistinguishable from an unrotated one. At n=3 the circuits are
shallow enough to keep signal (R023's 15-gate circuit survived at 0.96; R008's 435-gate at
0.18; the ~200-routed-gate AQC arm here should land in between), so fix-on vs fix-off is
measurable.

THREE ARMS, ONE JOB (same device, same hour):
  exact      -- the notebook's exact controlled block (n=3: ~50 CX ideal). Reference.
  aqc_naive  -- controlled AQC ansatz, NO phase correction. The trap, shipped.
  aqc_fixed  -- same ansatz + P(-theta) on the ancilla. The one-gate fix.

PRE-REGISTERED, FALSIFIABLE PREDICTIONS (recorded by this script before submission):
  P1. The naive and fixed arms have the SAME gate count and should show the SAME
      |chi| survival -- a magnitude metric cannot tell them apart. That is the trap's
      signature: the broken arm looks identical to the working arm on every
      magnitude-only figure of merit.
  P2. The measured PHASE difference arg(chi_naive) - arg(chi_fixed) equals the
      compile-time theta(t), per time -- decoherence damps magnitude, but a coherent
      global-phase offset on the ancilla branch is a rotation, not a contraction.
  P3. The fixed arm's chi points along the exact chi (damped); the naive arm's does not.

Usage:
  python fix_ab_hardware.py --dry-run            # pre-flight only, nothing submitted
  python fix_ab_hardware.py ibm_marrakesh        # submit
  python fix_ab_hardware.py --fetch              # fetch + analyse all recorded jobs
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

ns = load_notebook_definitions()
SPO = ns["SparsePauliOp"]
PHI_RE, PHI_IM = ns["PHI_RE"], ns["PHI_IM"]

N = 3                                    # the frozen 3-site benchmark family
TIMES = (0.3, 0.6, 0.9)
SHOTS = 4000
FIELDS = [0.40, -0.50, 0.15]
ARMS = ("exact", "aqc_naive", "aqc_fixed")
JOB_PATH = os.path.join(REPO, "evidence/fix_ab_job.json")


def ham():
    t = []
    for i in range(N - 1):
        t += [("XX", [i, i + 1], 0.65), ("YY", [i, i + 1], 0.65),
              ("ZZ", [i, i + 1], 0.25)]
    t += [("Z", [i], FIELDS[i]) for i in range(N)]
    return SPO.from_sparse_list(t, num_qubits=N).simplify()


H = ham()
PREP = QuantumCircuit(N); PREP.ry(1.3, 0)
PSI = np.asarray(Statevector(PREP).data)


def chi_exact(t):
    return complex(PSI.conj() @ ns["exact_unitary"](H, t) @ PSI)


def trot(t, reps):
    qc = QuantumCircuit(N)
    qc.append(ns["PauliEvolutionGate"](H, time=t,
              synthesis=ns["SuzukiTrotter"](order=2, reps=reps)), range(N))
    return transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
                     seed_transpiler=0)


def hadamard_test(t, phi, arm, aqc, theta, measure=True):
    sys_reg, anc = QuantumRegister(N, "sys"), QuantumRegister(1, "anc")
    qc = QuantumCircuit(sys_reg, anc)
    qc.compose(PREP, qubits=sys_reg, inplace=True)
    qc.h(anc[0])
    if arm == "exact":
        qc.append(ns["build_controlled_evolution"](H, t, "exact"), [anc[0], *sys_reg])
    else:
        qc.append(aqc.to_gate().control(1), [anc[0], *sys_reg])
        if arm == "aqc_fixed":
            qc.p(-theta, anc[0])         # the one-gate fix; aqc_naive omits exactly this
    if phi != 0.0:
        qc.p(phi, anc[0])
    qc.h(anc[0])
    if measure:
        creg = ClassicalRegister(1, "c"); qc.add_register(creg)
        qc.measure(anc[0], creg[0])
    return qc


def sv_chi(t, arm, aqc, theta):
    got = []
    for phi in (PHI_RE, PHI_IM):
        qc = hadamard_test(t, phi, arm, aqc, theta, measure=False)
        p = np.abs(np.asarray(Statevector(qc).data)) ** 2
        d = 2 ** N
        got.append(float(p[:d].sum() - p[d:].sum()))
    return complex(*got)


# ============================ FETCH MODE ============================
if "--fetch" in sys.argv:
    from qiskit_ibm_runtime import QiskitRuntimeService
    svc = QiskitRuntimeService()
    REC = json.load(open(JOB_PATH))
    out_all = {}
    for bname, rec in REC["jobs"].items():
        job = svc.job(rec["job_id"])
        st = str(job.status())
        print(f"job {rec['job_id']} on {bname}: {st}")
        if "DONE" not in st.upper():
            continue
        res = job.result()
        meas = {}
        for idx, m in enumerate(rec["meta"]):
            d = res[idx].data
            arr = getattr(d, "c", None) or getattr(d, "meas", None)
            bits = arr.get_bitstrings()
            z = float(np.mean([1 - 2 * int(b[-1]) for b in bits]))
            meas.setdefault(m["arm"], {}).setdefault(m["t"], {})[m["phi"]] = z
        print("\n" + "=" * 78)
        print(f"{bname} -- the trap, on hardware ({rec['shots']} shots/circuit)")
        print("=" * 78)
        rows = []
        for t in rec["times"]:
            ex = complex(*rec["chi_exact"][str(t)])
            theta = rec["theta"][str(t)]
            got = {a: complex(meas[a][t]["re"], meas[a][t]["im"]) for a in ARMS}
            dphi = float(np.angle(got["aqc_naive"] / got["aqc_fixed"])) \
                if abs(got["aqc_fixed"]) > 1e-6 else float("nan")
            print(f"\n  t={t}  exact chi {ex:+.4f}  (compile-time theta {theta:+.4f})")
            for a in ARMS:
                g = got[a]
                print(f"    {a:>10}: measured {g:+.4f}  |chi| {abs(g):.4f} "
                      f"(survival {abs(g)/abs(ex):.3f})  phase err vs exact "
                      f"{np.angle(g/ex):+.4f} rad")
            print(f"    P2 check: measured arg(naive/fixed) = {dphi:+.4f} rad "
                  f"vs pre-registered theta = {theta:+.4f} rad "
                  f"(deviation {abs(dphi-theta):.4f})")
            rows.append(dict(t=t, chi_exact=[ex.real, ex.imag], theta=theta,
                             measured={a: [got[a].real, got[a].imag] for a in ARMS},
                             phase_diff_measured=dphi))
        out_all[bname] = rows
    if out_all:
        with open(os.path.join(REPO, "evidence/fix_ab_result.json"), "w") as fh:
            json.dump(out_all, fh, indent=2)
        print("\nwrote evidence/fix_ab_result.json")
    sys.exit(0)

# ============================ COMPILE + PRE-FLIGHT ============================
from qiskit_addon_aqc_tensor.ansatz_generation import generate_ansatz_from_circuit
from qiskit_addon_aqc_tensor.objective import OneMinusFidelity
from qiskit_addon_aqc_tensor.simulation import tensornetwork_from_circuit
from qiskit_addon_aqc_tensor.simulation.quimb import QuimbSimulator
import quimb.tensor
sim = QuimbSimulator(quimb.tensor.CircuitMPS, autodiff_backend="jax")

print("=" * 78)
print(f"PRE-FLIGHT at n={N} -- compile, then verify all three arms on the statevector")
print("=" * 78)
AQC = {}
for t in TIMES:
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
    AQC[t] = (bound, theta, float(infid))
    ex = chi_exact(t)
    naive = sv_chi(t, "aqc_naive", bound, theta)
    fixed = sv_chi(t, "aqc_fixed", bound, theta)
    exact_sv = sv_chi(t, "exact", bound, theta)
    print(f"  t={t}: infidelity {infid:.2e}  theta {theta:+.4f} rad")
    print(f"         exact arm  {exact_sv:+.4f}  (dev {abs(exact_sv-ex):.2e})")
    print(f"         fixed arm  {fixed:+.4f}  (|err| {abs(fixed-ex):.4f})")
    print(f"         naive arm  {naive:+.4f}  (|err| {abs(naive-ex):.4f}  "
          f"<- the trap, ideally; phase off by {np.angle(naive/fixed):+.4f})")
    assert abs(exact_sv - ex) < 1e-9, "exact arm broken -- stop"
    assert abs(fixed - ex) < 0.05, "fixed arm off ideally -- stop"
    assert abs(naive - ex) > 3 * abs(fixed - ex), \
        "naive arm not visibly broken ideally -- the experiment would be pointless"
print("  PRE-FLIGHT PASSED: naive broken, fixed clean, exact exact -- as required\n")

if "--dry-run" in sys.argv and not [a for a in sys.argv if a.startswith("ibm_")]:
    print("dry run: statevector only, no backend contacted"); sys.exit(0)

# ============================ TRANSPILE + PREDICT + SUBMIT ============================
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
svc = QiskitRuntimeService()
targets = [a for a in sys.argv[1:] if a.startswith("ibm_")]
assert targets, "give a backend, e.g. ibm_marrakesh"
backend = svc.backend(targets[0])
props = backend.properties()
TWOQ = sorted({nme for nme, inst in backend.target.items()
               if inst and any(k is not None and len(k) == 2 for k in inst)}
              - {"measure", "delay", "reset", "barrier"})

circuits, meta = [], []
for arm in ARMS:
    for t in TIMES:
        for phi, tag in ((PHI_RE, "re"), (PHI_IM, "im")):
            qc = hadamard_test(t, phi, arm, AQC[t][0], AQC[t][1])
            tq = transpile(qc, backend, optimization_level=1, seed_transpiler=2026)
            n2 = sum(v for k, v in tq.count_ops().items() if k in TWOQ)
            circuits.append(tq); meta.append(dict(arm=arm, t=t, phi=tag, two_q=int(n2)))

print("=" * 78)
print(f"TRANSPILED on {backend.name}; PREDICTIONS, recorded before submission:")
print("=" * 78)
pred = {}
for arm in ARMS:
    med = float(np.median([m["two_q"] for m in meta if m["arm"] == arm]))
    errs = []
    for c, m in zip(circuits, meta):
        if m["arm"] != arm:
            continue
        for inst in c.data:
            if inst.operation.name in TWOQ:
                q = [c.find_bit(b).index for b in inst.qubits]
                try:
                    errs.append(props.gate_error(inst.operation.name, q))
                except Exception:
                    pass
    e = float(np.median(errs)) if errs else 1.7e-3
    pred[arm] = dict(median_2q=med, median_edge_error=e,
                     predicted_survival=float((1 - e) ** med))
    print(f"  {arm:>10}: median {med:>5.0f} 2q gates  predicted survival "
          f"{pred[arm]['predicted_survival']:.3f}")
print("  P1: naive and fixed have the same count -> same predicted survival;")
print("      a magnitude metric cannot separate them. Only the phase can.")
print("  P2: arg(chi_naive/chi_fixed) should equal theta(t): "
      + ", ".join(f"{AQC[t][1]:+.3f}" for t in TIMES))

if "--dry-run" in sys.argv:
    print("\ndry run -- nothing submitted"); sys.exit(0)

sampler = SamplerV2(mode=backend)
job = sampler.run(circuits, shots=SHOTS)
out = json.load(open(JOB_PATH)) if os.path.exists(JOB_PATH) else {"jobs": {}}
out.setdefault("jobs", {})[backend.name] = dict(
    job_id=job.job_id(), n=N, times=list(TIMES), shots=SHOTS, meta=meta, prediction=pred,
    theta={str(t): AQC[t][1] for t in TIMES},
    infidelity={str(t): AQC[t][2] for t in TIMES},
    chi_exact={str(t): [chi_exact(t).real, chi_exact(t).imag] for t in TIMES})
with open(JOB_PATH, "w") as fh:
    json.dump(out, fh, indent=2)
print(f"\nsubmitted {len(circuits)} circuits x {SHOTS} shots to {backend.name}")
print(f"job {job.job_id()}  ->  evidence/fix_ab_job.json  (fetch with --fetch)")
