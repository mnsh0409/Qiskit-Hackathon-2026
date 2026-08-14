"""JUDGE Q: "Have you compared your method against pure AQC — no Hadamard test, no shadow?"

Clarifies R046/BUGLOG-adjacent Q11 in qa_crib.md, which compared AQC's OWN certificate
(state fidelity) against what OUR interferometric protocol measures (chi). That is not the
same question as this one. "Pure AQC" here means AQC used the way the compiling literature
normally uses it: compress a STATE-PREPARATION circuit, then measure ordinary observables
directly on the resulting state -- no ancilla, no controlled-U, no interference circuit of
any kind, no classical shadow ensemble. Does THAT work?

THE KEY DISTINCTION, stated before measuring anything (so the result can falsify it):
chi = <psi|U|psi> is NOT the expectation value of any observable in any single state -- it
is an INTERFERENCE term between |psi> and |U psi>, and physically extracting it requires an
ancilla-based circuit (a Hadamard test, or something informationally equivalent: a Loschmidt
echo, a SWAP/Hilbert-Schmidt test). There is no way to "just measure" chi directly. By
contrast, an ordinary observable expectation value on the AQC-PREPARED state,
<O>_W = <psi|W^dagger O W|psi>, needs no ancilla and no interference -- standard Pauli
sampling on the compressed state suffices, exactly the AQC's textbook use case.

THE PREDICTED CONSEQUENCE: <O>_W is invariant under the exact phase ambiguity that breaks
chi. If W|psi> = e^{i theta} U|psi> (R046's own finding), then
    <O>_W = <psi|W^dagger O W|psi> = <psi|U^dagger e^{-i theta} O e^{i theta} U|psi>
          = <psi|U^dagger O U|psi> = <O>_U     EXACTLY, for ANY theta and ANY Hermitian O.
So "pure AQC" (state-prep + direct measurement) should NOT trip the phase trap at all --
the trap is specific to using AQC INSIDE an interferometric protocol, not to AQC itself.
Verified two ways: (1) the algebraic identity above; (2) numerically, at every n already
measured for R046, on multiple observables, AND by an explicit global-phase-perturbation
test that <O>_W is unchanged when W is multiplied by an arbitrary extra phase.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json
sys.path.insert(0, REPO)
from hardware_run import load_notebook_definitions

import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator, Statevector, SparsePauliOp

from qiskit_addon_aqc_tensor.ansatz_generation import generate_ansatz_from_circuit
from qiskit_addon_aqc_tensor.objective import OneMinusFidelity
from qiskit_addon_aqc_tensor.simulation import tensornetwork_from_circuit
from qiskit_addon_aqc_tensor.simulation.quimb import QuimbSimulator
import quimb.tensor

ns = load_notebook_definitions()
T = 0.9
NS = [int(a) for a in sys.argv[1:]] or [3, 5, 7]        # subset of R046's n=3..7 trend
simulator = QuimbSimulator(quimb.tensor.CircuitMPS, autodiff_backend="jax")

FIELDS = (0.40, -0.50, 0.15, 0.20, -0.30, 0.10, 0.25)    # identical to aqc_scaling.py


def chain_ham(n):
    terms = []
    for i in range(n - 1):
        terms += [("XX", [i, i + 1], 0.65), ("YY", [i, i + 1], 0.65),
                  ("ZZ", [i, i + 1], 0.25)]
    terms += [("Z", [i], FIELDS[i]) for i in range(n)]
    return SparsePauliOp.from_sparse_list(terms, num_qubits=n).simplify()


def trotter_circuit(H, n, reps):
    from qiskit.synthesis import SuzukiTrotter
    from qiskit.circuit.library import PauliEvolutionGate
    qc = QuantumCircuit(n)
    qc.append(PauliEvolutionGate(H, time=T, synthesis=SuzukiTrotter(order=2, reps=reps)),
              range(n))
    return transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
                     seed_transpiler=0)


RNG = np.random.default_rng(2026)
ROWS = []
for n in NS:
    print("=" * 78)
    print(f"n = {n}  (state-prep only -- no ancilla, no controlled-U, no interference)")
    print("=" * 78)
    H = chain_ham(n)
    prep = QuantumCircuit(n); prep.ry(1.3, 0)
    psi = np.asarray(Statevector(prep).data)
    U_exact = ns["exact_unitary"](H, T)

    seed_qc = trotter_circuit(H, n, reps=1)
    ansatz, initial = generate_ansatz_from_circuit(seed_qc, qubits_initially_zero=True)
    full_target = QuantumCircuit(n)
    full_target.compose(prep, inplace=True)
    full_target.compose(trotter_circuit(H, n, reps=3), inplace=True)
    tgt_mps = tensornetwork_from_circuit(full_target, simulator)
    full_ansatz = QuantumCircuit(n)
    full_ansatz.compose(prep, inplace=True)
    full_ansatz.compose(ansatz, inplace=True)
    res = minimize(OneMinusFidelity(tgt_mps, full_ansatz, simulator), np.array(initial),
                   jac=True, method="L-BFGS-B", options={"maxiter": 400})
    bound = ansatz.assign_parameters(res.x)
    W_aqc = Operator(bound).data
    psi_aqc = np.asarray(Statevector(full_ansatz.assign_parameters(res.x)).data)  # = W|psi>

    # ---- reproduce R046's chi error, as a same-n cross-check that this IS the same W ----
    chi_u = complex(psi.conj() @ U_exact @ psi)
    chi_w = complex(psi.conj() @ W_aqc @ psi)
    chi_err = abs(chi_w - chi_u)
    print(f"  chi error (interferometric, R046's quantity): {chi_err:.4f}  "
          f"(sanity check vs R046's own n={n} value)")

    # ---- THE NEW MEASUREMENT: direct observables on the two PREPARED states ----
    OBS = {"Q": SparsePauliOp.from_sparse_list(
               [("Z", [j], 1.0) for j in range(n)], num_qubits=n),
           "H": H,
           "Z0": SparsePauliOp.from_sparse_list([("Z", [0], 1.0)], num_qubits=n)}
    psi_U = U_exact @ psi
    obs_errs = {}
    for name, O in OBS.items():
        Om = O.to_matrix()
        o_w = float(np.real(psi_aqc.conj() @ Om @ psi_aqc))
        o_u = float(np.real(psi_U.conj() @ Om @ psi_U))
        obs_errs[name] = dict(W=o_w, U=o_u, err=abs(o_w - o_u))
        print(f"    <{name}>_W {o_w:+.4f}  vs  <{name}>_U {o_u:+.4f}   "
              f"|err| {abs(o_w - o_u):.4f}  <- direct measurement, NO ancilla needed")

    # ---- explicit phase-invariance check: perturb W by an arbitrary extra global phase ----
    extra_theta = float(RNG.uniform(0, 2 * np.pi))
    psi_aqc_phased = np.exp(1j * extra_theta) * psi_aqc
    worst_phase_effect = 0.0
    for name, O in OBS.items():
        Om = O.to_matrix()
        o_before = float(np.real(psi_aqc.conj() @ Om @ psi_aqc))
        o_after = float(np.real(psi_aqc_phased.conj() @ Om @ psi_aqc_phased))
        worst_phase_effect = max(worst_phase_effect, abs(o_after - o_before))
    print(f"  phase-invariance check: multiplying W|psi> by e^i{extra_theta:.2f} changes "
          f"every <O> by <= {worst_phase_effect:.2e} (want ~0, unlike chi's 1.3-scale error)")
    assert worst_phase_effect < 1e-9, "observable expectation values should be exactly phase-invariant"

    ROWS.append(dict(n=n, chi_err_interferometric=float(chi_err), observables=obs_errs,
                      phase_perturbation_effect=float(worst_phase_effect)))
    print()

print("=" * 78)
print("SUMMARY: interferometric chi vs direct observable estimation, same n, same W")
print("=" * 78)
print(f"{'n':>3}{'chi err (needs ancilla)':>26}{'worst <O> err (no ancilla)':>29}")
for r in ROWS:
    worst_obs = max(v["err"] for v in r["observables"].values())
    print(f"{r['n']:>3}{r['chi_err_interferometric']:>26.4f}{worst_obs:>29.4f}")

with open(os.path.join(REPO, "evidence/aqc_direct_observable.json"), "w") as fh:
    json.dump(dict(t=T, ns=NS, rows=ROWS), fh, indent=2)
print("\nwrote evidence/aqc_direct_observable.json")
