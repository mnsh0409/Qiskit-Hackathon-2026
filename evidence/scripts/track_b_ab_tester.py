"""Track B (partial) -- dynamics A/B tester via an anti-controlled Hadamard test.

DERIVATION (this circuit is NOT the standard Hadamard test, so it needs its own identity
and its own statevector validation -- the whole point of CONVENTIONS §3's discipline):

  |0>_a |psi>
    --h(a)-->            (|0> + |1>)|psi> / sqrt2
    --x, c-W, x-->       (|0> W|psi> + |1>|psi>) / sqrt2      (W on the |0> branch)
    --c-U-->             (|0> W|psi> + |1> U|psi>) / sqrt2
    --p(phi,a)-->        (|0> W|psi> + e^{i phi}|1> U|psi>) / sqrt2
    --h(a)-->            (1/2)[ |0>(W + e^{i phi}U)|psi> + |1>(W - e^{i phi}U)|psi> ]

  <Z_a> = (1/4)[ ||(W + e^{i phi}U)psi||^2 - ||(W - e^{i phi}U)psi||^2 ]
        = (1/4)[ (2 + e^{i phi}<W'U> + c.c.) - (2 - e^{i phi}<W'U> - c.c.) ]
        = Re[ e^{i phi} <psi| W^dag U |psi> ]

So with the SAME phi convention as the standard test (phi=0 -> Re, phi=-pi/2 -> Im), the
ancilla now measures the OVERLAP OF TWO DYNAMICS:

        chi_AB(t) = <psi| W(t)^dag U(t) |psi>

W=I recovers the ordinary Hadamard test, so this is a strict generalisation. Here we take
U = exact evolution and W = Trotterised evolution, so chi_AB(t) directly measures how far
the product formula has drifted from the true dynamics -- with chi_AB(0)=1 exactly and
1 - |chi_AB| a natural disagreement measure.

SCOPE: partial, deliberately. Delivered here are the overlap-vs-time curves and the
gate-cost comparison. NOT delivered: per-observable disagreement profiles, which need the
X-basis ancilla readout (rho^(X), "delete the final Hadamard") -- a separate derivation the
scaffold flags and which we did not attempt. Stated so nobody reads this as complete Track B.
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions

import json
import numpy as np
from qiskit import transpile

ns = load_notebook_definitions()
HAM, PSI, N_SYS = ns["HAM"], ns["PSI"], ns["N_SYS"]
QuantumCircuit, QuantumRegister = ns["QuantumCircuit"], ns["QuantumRegister"]
ClassicalRegister = ns["ClassicalRegister"]
Statevector, Operator = ns["Statevector"], ns["Operator"]
PHI_RE, PHI_IM = ns["PHI_RE"], ns["PHI_IM"]


def build_ab_circuit(ham, t, phi, reps_w, basis=None, measure=False):
    """Anti-controlled Hadamard test: W = Trotter(reps_w) on the |0> branch, U = exact on
    the |1> branch. Structure follows the notebook's own §7.5 scaffold."""
    sys_reg, anc_reg = QuantumRegister(N_SYS, "sys"), QuantumRegister(1, "anc")
    qc = QuantumCircuit(sys_reg, anc_reg)
    qc.compose(ns["state_prep_circuit"](), qubits=sys_reg, inplace=True)
    qc.h(anc_reg[0])
    qc.x(anc_reg[0])                                                   # anti-control W ...
    qc.append(ns["build_controlled_evolution"](ham, t, "trotter", reps_w),
              [anc_reg[0], *sys_reg])
    qc.x(anc_reg[0])                                                   # ... undo
    qc.append(ns["build_controlled_evolution"](ham, t, "exact"), [anc_reg[0], *sys_reg])
    if phi != 0.0:
        qc.p(phi, anc_reg[0])
    qc.h(anc_reg[0])                                                   # Z-basis readout
    if basis is not None:
        for j, b in enumerate(basis):
            if b == 0:
                qc.h(sys_reg[j])
            elif b == 1:
                qc.sdg(sys_reg[j]); qc.h(sys_reg[j])
    if measure:
        creg = ClassicalRegister(N_SYS + 1, "c")
        qc.add_register(creg)
        for j in range(N_SYS):
            qc.measure(sys_reg[j], creg[j])
        qc.measure(anc_reg[0], creg[N_SYS])
    return qc


def trotter_unitary(t, reps_w):
    """The Trotter unitary EXACTLY as the circuit realises it.

    TRAP (cost a debugging cycle, worth recording): building
    `PauliEvolutionGate(H, t, synthesis=SuzukiTrotter(...))` into a circuit and calling
    `Operator(qc)` does NOT give the Trotterised unitary -- Qiskit defers synthesis, so
    Operator() evaluates the gate's exact definition and hands back exp(-iHt) itself
    (verified: it matched exact_unitary to 8e-16, i.e. zero Trotter error, which is
    impossible for reps=1). Synthesis only happens at transpile time. So the honest
    reference is to pull W out of the very gate the circuit uses -- guaranteeing the
    reference and the circuit cannot diverge."""
    g = ns["build_controlled_evolution"](HAM, t, "trotter", reps_w)
    qc = QuantumCircuit(N_SYS + 1)
    qc.append(g, [N_SYS, *range(N_SYS)])       # ancilla is the control, and the high bit
    M = Operator(qc).data
    d = 2 ** N_SYS
    return M[d:, d:]                            # the |1><1| block == W


def exact_chi_ab(t, reps_w):
    """<psi| W^dag U |psi> computed classically, for evaluation only."""
    u = ns["exact_unitary"](HAM, t)
    w = trotter_unitary(t, reps_w)
    return complex(PSI.conj() @ (w.conj().T @ u) @ PSI)


# ==================================================== (1) statevector validation
print("=" * 78)
print("(1) STATEVECTOR VALIDATION of the derived identity  <Z_a> = Re[e^{i phi} <W'U>]")
print("=" * 78)
worst = 0.0
z1q = ns["SparsePauliOp"].from_sparse_list([("Z", [0], 1.0)], num_qubits=1)
ident = ns["SparsePauliOp"].from_sparse_list([("I", [0], 1.0)], num_qubits=N_SYS)
for t in (0.0, 0.7, 2.3):
    for reps_w in (1, 2):
        for phi, lbl in ((PHI_RE, "Re"), (PHI_IM, "Im")):
            sv = Statevector(build_ab_circuit(HAM, t, phi, reps_w))
            measured = float(np.real(sv.expectation_value(z1q.tensor(ident))))
            expected = float(np.real(np.exp(1j * phi) * exact_chi_ab(t, reps_w)))
            worst = max(worst, abs(measured - expected))
print(f"  max deviation over 3 times x 2 reps x 2 quadratures = {worst:.2e}")
ok_identity = worst < 1e-10
print(f"  identity {'CONFIRMED' if ok_identity else 'FAILED'} (want < 1e-10)")
print(f"  sanity: chi_AB(0) = {exact_chi_ab(0.0, 1):.6f}  (must be exactly 1 -- both "
      f"evolutions are the identity at t=0)")

# ==================================================== (2) overlap vs time, shot-based
print("\n" + "=" * 78)
print("(2) OVERLAP vs TIME -- how fast does the product formula drift from true dynamics?")
print("=" * 78)
from qiskit_aer import AerSimulator
backend = AerSimulator()
TS_B = np.array([0.0, 0.9, 1.8, 2.7, 3.6, 4.5])
SHOTS_B = 4000
ROWS = []
print(f"\n{'t':>5} | " + " | ".join(f"reps={r}: |chi_AB| (exact)" for r in (1, 2, 4)))
print("-" * 78)
for t in TS_B:
    cells = []
    for reps_w in (1, 2, 4):
        vals = []
        for phi, sd in ((PHI_RE, 601), (PHI_IM, 602)):
            qc = build_ab_circuit(HAM, t, phi, reps_w, basis=[2] * N_SYS, measure=True)
            mem = backend.run(transpile(qc, backend), shots=SHOTS_B, memory=True,
                              seed_simulator=sd + int(t * 10) + reps_w).result().get_memory(0)
            _o, anc = ns["parse_memory"](mem, N_SYS)
            vals.append(float(np.mean(anc)))
        meas = abs(complex(vals[0], vals[1]))
        ex = abs(exact_chi_ab(t, reps_w))
        cells.append(f"{meas:.3f} ({ex:.3f})")
        ROWS.append(dict(t=float(t), reps=reps_w, measured_abs=meas, exact_abs=ex))
    print(f"{t:>5.1f} | " + " | ".join(f"{c:>22s}" for c in cells))

print("\n  |chi_AB| = 1 means the two dynamics agree exactly; it falls as Trotter error grows.")
print("  More reps -> closer to 1 at fixed t, and all curves start at exactly 1.0 at t=0.")

# ==================================================== (3) gate cost of the comparison
print("\n" + "=" * 78)
print("(3) GATE COST -- what the A/B comparison costs vs a plain Hadamard test")
print("=" * 78)
print(f"\n{'circuit':>28} {'depth':>7} {'CX':>6}")
print("-" * 44)
COST = []
plain = ns["build_shadow_hadamard_circuit"](HAM, 0.9, PHI_RE, basis=[2] * N_SYS,
                                            method="exact")
tq = transpile(plain, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
               seed_transpiler=0)
print(f"{'plain Hadamard (exact)':>28} {tq.depth():>7} {tq.count_ops().get('cx', 0):>6}")
COST.append(dict(circuit="plain_hadamard_exact", depth=tq.depth(),
                 cx=int(tq.count_ops().get("cx", 0))))
for reps_w in (1, 2, 4):
    ab = build_ab_circuit(HAM, 0.9, PHI_RE, reps_w, basis=[2] * N_SYS, measure=True)
    tq = transpile(ab, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
                   seed_transpiler=0)
    print(f"{'A/B tester, W=trotter r=' + str(reps_w):>28} {tq.depth():>7} "
          f"{tq.count_ops().get('cx', 0):>6}")
    COST.append(dict(circuit=f"ab_tester_reps{reps_w}", depth=tq.depth(),
                     cx=int(tq.count_ops().get("cx", 0))))
print("\n  The A/B circuit carries BOTH evolutions, so it is necessarily deeper than either")
print("  alone -- the scaffold's own 'roughly doubles the controlled-evolution depth' note.")

with open("/home/martin/Documents/QiskitHackathon/2026/evidence/track_b_result.json", "w") as fh:
    json.dump(dict(identity_max_deviation=float(worst), identity_ok=bool(ok_identity),
                   overlap_rows=ROWS, gate_cost=COST, shots_per_setting=SHOTS_B,
                   scope="PARTIAL: overlap curves + gate cost; per-observable X-basis "
                         "disagreement profiles NOT attempted"), fh, indent=2)
print("\nwrote evidence/track_b_result.json")
