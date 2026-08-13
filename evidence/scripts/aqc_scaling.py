"""DOES AQC ACTUALLY HELP A HADAMARD TEST? Yes -- but only after fixing a trap that
silently destroys the answer. Both halves are measured here.

THE TRAP, found by this script and worth stating first. AQC-Tensor optimises STATE FIDELITY,
|<psi_target|psi_ansatz>|, which is BLIND TO GLOBAL PHASE. A Hadamard test is precisely an
interferometer that measures global phase. So a "successful" AQC compression at state
infidelity 3e-4 produces a controlled evolution whose chi = <psi|W|psi> is wrong by ~2.5-3
RADIANS -- |chi_err| ~ 1.3 on a quantity bounded by 1. R035's certificate used |chi_AB|,
a magnitude, and therefore could not have caught this.

THE FIX, one gate. If W|psi> = e^{i theta} U|psi>, then theta = arg(<U psi|W psi>) is known
at compile time -- the same MPS run that produces W gives it for free -- and a P(-theta) on
the ANCILLA cancels it exactly, because the ancilla's |1> branch is the one carrying W.
Cost: one single-qubit gate. Effect: |chi_err| 1.33 -> 0.008.

SCOPE, stated plainly: AQC here is compressed against ONE input state, so its PROCESS
infidelity is large (~0.96) -- it is NOT a general-purpose controlled-U. That is legitimate
for a Hadamard test, whose controlled gate only ever acts on that one state, and illegitimate
for anything that feeds it other inputs. Both numbers are reported below.

DOES AQC ACTUALLY HELP? Find the crossover by measuring it at n=3..7.

R035 left this genuinely open. For the CONTROLLED evolution -- which is what a Hadamard test
actually runs -- AQC was 2.6x WORSE than exact synthesis at n=3 but 1.09x BETTER at n=4.
Two points do not establish a trend, and "it should win beyond n=4" was an extrapolation,
not a measurement. This script measures it.

WHY A CROSSOVER SHOULD EXIST (stated before running, so the result can falsify it):
  * The notebook's build_controlled_evolution("exact") builds |0><0| (x) I + |1><1| (x) U
    directly as ONE UnitaryGate on n+1 qubits. Synthesising an arbitrary m-qubit unitary
    costs O(4^m) CX, so this baseline grows like 4^(n+1) -- exponentially, with a bad base.
  * A controlled AQC ansatz pays a constant per-gate control overhead on a circuit whose
    own size grows only polynomially with n.
  * So exact synthesis must lose eventually. The only question is WHERE, and whether the
    infidelity price is acceptable when it does.

THE BASELINE IS THE HONEST ONE. R035 records that comparing AQC against a naive
.control() of a synthesised circuit flatters AQC by ~4x. We use the notebook's actual
construction, which is markedly cheaper and therefore harder to beat.

Every AQC row carries its infidelity. A shallower circuit that computes the wrong thing is
not a win and is not reported as one.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json, time
sys.path.insert(0, REPO)
from hardware_run import load_notebook_definitions

import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator, Statevector

from qiskit_addon_aqc_tensor.ansatz_generation import generate_ansatz_from_circuit
from qiskit_addon_aqc_tensor.objective import OneMinusFidelity
from qiskit_addon_aqc_tensor.simulation import tensornetwork_from_circuit
from qiskit_addon_aqc_tensor.simulation.quimb import QuimbSimulator
import quimb.tensor

ns = load_notebook_definitions()
SPO, UnitaryGate = ns["SparsePauliOp"], ns["UnitaryGate"]
T = 0.9
NS = [int(a) for a in sys.argv[1:]] or [3, 4, 5, 6]
simulator = QuimbSimulator(quimb.tensor.CircuitMPS, autodiff_backend="jax")

FIELDS = (0.40, -0.50, 0.15, 0.20, -0.30, 0.10, 0.25)     # extends the frozen benchmark


def chain_ham(n):
    """Same family as the frozen 3-site benchmark, extended to n sites."""
    terms = []
    for i in range(n - 1):
        terms += [("XX", [i, i + 1], 0.65), ("YY", [i, i + 1], 0.65),
                  ("ZZ", [i, i + 1], 0.25)]
    terms += [("Z", [i], FIELDS[i]) for i in range(n)]
    return SPO.from_sparse_list(terms, num_qubits=n).simplify()


def cx_of(qc):
    t = transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
                  seed_transpiler=0)
    return int(t.count_ops().get("cx", 0)), int(t.depth())


def trotter_circuit(H, n, reps):
    qc = QuantumCircuit(n)
    qc.append(ns["PauliEvolutionGate"](H, time=T,
              synthesis=ns["SuzukiTrotter"](order=2, reps=reps)), range(n))
    return transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
                     seed_transpiler=0)


ROWS = []
for n in NS:
    print("=" * 78)
    print(f"n = {n} system qubits  ({n+1} qubits with the ancilla)")
    print("=" * 78)
    H = chain_ham(n)
    prep = QuantumCircuit(n); prep.ry(1.3, 0)
    psi = np.asarray(Statevector(prep).data)
    U_exact = ns["exact_unitary"](H, T)

    # ---- baseline A: the notebook's exact controlled block, |0><0|(x)I + |1><1|(x)U ----
    t0 = time.time()
    cq = QuantumCircuit(n + 1)
    cq.append(ns["build_controlled_evolution"](H, T, "exact"), [n, *range(n)])
    cex_cx, cex_depth = cx_of(cq)
    t_exact = time.time() - t0
    print(f"  exact controlled block : {cex_cx:>6} CX, depth {cex_depth:>5}  "
          f"(synthesis {t_exact:.1f}s)  -- infidelity 0 by construction")

    # ---- baseline B: controlled Trotter (reps=2) ----
    trot = trotter_circuit(H, n, reps=2)
    ctq = QuantumCircuit(n + 1)
    ctq.append(trot.to_gate().control(1), [n, *range(n)])
    ctr_cx, ctr_depth = cx_of(ctq)
    U_trot = Operator(trot).data
    trot_infid = 1 - abs(psi.conj() @ (U_trot.conj().T @ U_exact) @ psi)
    print(f"  controlled Trotter r=2 : {ctr_cx:>6} CX, depth {ctr_depth:>5}  "
          f"infidelity {trot_infid:.2e}")

    # ---- AQC: compress, then control ----
    seed_qc = trotter_circuit(H, n, reps=1)
    ansatz, initial = generate_ansatz_from_circuit(seed_qc, qubits_initially_zero=True)
    full_target = QuantumCircuit(n)
    full_target.compose(prep, inplace=True)
    full_target.compose(trotter_circuit(H, n, reps=3), inplace=True)
    tgt_mps = tensornetwork_from_circuit(full_target, simulator)
    full_ansatz = QuantumCircuit(n)
    full_ansatz.compose(prep, inplace=True)
    full_ansatz.compose(ansatz, inplace=True)

    t0 = time.time()
    res = minimize(OneMinusFidelity(tgt_mps, full_ansatz, simulator), np.array(initial),
                   jac=True, method="L-BFGS-B", options={"maxiter": 400})
    t_aqc = time.time() - t0
    bound = ansatz.assign_parameters(res.x)
    caq = QuantumCircuit(n + 1)
    caq.append(bound.to_gate().control(1), [n, *range(n)])
    caqc_cx, caqc_depth = cx_of(caq)
    psi_aqc = np.asarray(Statevector(full_ansatz.assign_parameters(res.x)).data)
    aqc_infid = 1 - abs(np.vdot(psi_aqc, U_exact @ psi))
    # AQC optimises fidelity ON ONE INPUT STATE, while the exact block is correct as an
    # OPERATOR. So the state infidelity above flatters AQC unless the process infidelity
    # is also small. Measure it: F_proc = |Tr[W^dag U]| / 2^n.
    W_aqc = Operator(bound).data
    aqc_proc_infid = 1 - abs(np.trace(W_aqc.conj().T @ U_exact)) / (2 ** n)
    trot_proc_infid = 1 - abs(np.trace(U_trot.conj().T @ U_exact)) / (2 ** n)
    print(f"  controlled AQC         : {caqc_cx:>6} CX, depth {caqc_depth:>5}  "
          f"infidelity {aqc_infid:.2e}  (optimised {t_aqc:.1f}s, {len(initial)} params)")
    print(f"     state infidelity {aqc_infid:.2e}  vs  PROCESS infidelity "
          f"{aqc_proc_infid:.2e}   (Trotter r=2 process: {trot_proc_infid:.2e})")

    # ---- THE PHASE TRAP, and the one-gate fix ----
    chi_u = complex(psi.conj() @ U_exact @ psi)
    chi_w = complex(psi.conj() @ W_aqc @ psi)
    theta = float(np.angle(np.vdot(U_exact @ psi, W_aqc @ psi)))
    chi_fixed = np.exp(-1j * theta) * chi_w
    err_naive, err_fixed = abs(chi_w - chi_u), abs(chi_fixed - chi_u)
    print(f"     chi naive  {chi_w:+.4f}  vs exact {chi_u:+.4f}   |err| {err_naive:.4f} "
          f"<- BROKEN by the phase-blind objective")
    print(f"     chi + P({-theta:+.3f}) on ancilla ..................  |err| {err_fixed:.4f} "
          f"<- fixed by ONE 1q gate ({err_naive/max(err_fixed,1e-12):.0f}x better)")

    ratio = cex_cx / caqc_cx if caqc_cx else float("nan")
    verdict = (f"AQC WINS by {ratio:.2f}x" if ratio > 1 else
               f"exact synthesis wins by {1/ratio:.2f}x")
    print(f"  -> {verdict}   (exact {cex_cx} vs AQC {caqc_cx} CX)")
    ROWS.append(dict(n=n, exact_cx=cex_cx, exact_depth=cex_depth,
                     trotter_cx=ctr_cx, trotter_depth=ctr_depth,
                     trotter_infidelity=float(trot_infid),
                     aqc_cx=caqc_cx, aqc_depth=caqc_depth,
                     aqc_infidelity=float(aqc_infid),
                     aqc_process_infidelity=float(aqc_proc_infid),
                     trotter_process_infidelity=float(trot_proc_infid), n_params=len(initial),
                     aqc_vs_exact=float(ratio), aqc_opt_seconds=float(t_aqc),
                     chi_exact=[chi_u.real, chi_u.imag], chi_aqc_naive=[chi_w.real, chi_w.imag],
                     phase_theta=float(theta), chi_err_naive=float(err_naive),
                     chi_err_phase_fixed=float(err_fixed),
                     exact_synth_seconds=float(t_exact)))
    print()

print("=" * 78)
print("CONTROLLED two-qubit gate count -- what a Hadamard test actually pays")
print("=" * 78)
print(f"{'n':>3}{'exact block':>13}{'Trotter r=2':>13}{'AQC':>8}"
      f"{'AQC vs exact':>14}{'AQC state':>12}{'AQC process':>13}")
print("-" * 78)
for r in ROWS:
    tag = f"{r['aqc_vs_exact']:.2f}x " + ("WIN" if r["aqc_vs_exact"] > 1 else "loss")
    print(f"{r['n']:>3}{r['exact_cx']:>13}{r['trotter_cx']:>13}{r['aqc_cx']:>8}"
          f"{tag:>14}{r['aqc_infidelity']:>12.2e}{r['aqc_process_infidelity']:>13.2e}")

wins = [r for r in ROWS if r["aqc_vs_exact"] > 1]
if wins:
    first = min(r["n"] for r in wins)
    best = max(ROWS, key=lambda r: r["aqc_vs_exact"])
    print(f"\n  CROSSOVER MEASURED AT n = {first}. Best margin {best['aqc_vs_exact']:.2f}x "
          f"at n = {best['n']}, infidelity {best['aqc_infidelity']:.1e}.")
    print("  The exact block grows like 4^(n+1); AQC does not. The crossover is structural,")
    print("  not a tuning artefact -- but it is measured here only up to n =", max(NS))
    wn = max(r["chi_err_naive"] for r in ROWS)
    wf = max(r["chi_err_phase_fixed"] for r in ROWS)
    print(f"\n  AND THE GATE COUNT ONLY COUNTS IF THE ANSWER IS RIGHT: worst |chi error| is")
    print(f"  {wn:.3f} without the ancilla phase correction (i.e. useless) and {wf:.4f} with it.")
    print("  One single-qubit gate is the difference between a broken and a working test.")
else:
    print("\n  NO CROSSOVER in the range tested -- exact synthesis wins at every n here.")
    print("  Report that; do not extrapolate a win we did not measure.")

with open(os.path.join(REPO, "evidence/aqc_scaling.json"), "w") as fh:
    json.dump(dict(t=T, reps_trotter=2, rows=ROWS), fh, indent=2)
print("\nwrote evidence/aqc_scaling.json")
