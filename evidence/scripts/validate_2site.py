"""Validate a reduced 2-site instance on the IDEAL simulator before spending QPU time.

Going-further robustness item 4 asks for a reduced two-qubit instance on real hardware.
This is NOT the frozen 3-qubit benchmark of CONVENTIONS §2 -- it is a separate side model,
usable for robustness claims only.

At n=2 the full random-basis shadow ensemble is just 3^2 = 9 circuits per quadrature, so a
GENUINE shadow run (valid system observables, not just chi) is affordable on hardware --
which also closes the BUGLOG B04 gap, where fixed-basis jobs could only ever report chi.

Balanced allocation (equal shots per basis) is used instead of multinomial grouping: the
empirical basis distribution is then exactly uniform, which the estimator assumes, so it
stays unbiased and has slightly lower variance.
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions

import itertools
import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator

ns = load_notebook_definitions()
SparsePauliOp, QuantumCircuit, Statevector = ns["SparsePauliOp"], ns["QuantumCircuit"], ns["Statevector"]

N2 = 2
H2 = SparsePauliOp.from_sparse_list(
    [("XX", [0, 1], 0.65), ("YY", [0, 1], 0.65), ("ZZ", [0, 1], 0.25),
     ("Z", [0], 0.40), ("Z", [1], -0.50)], num_qubits=N2).simplify()
Q2 = SparsePauliOp.from_sparse_list([("Z", [j], 1.0) for j in range(N2)], num_qubits=N2)
PREP2 = QuantumCircuit(N2, name="prep"); PREP2.ry(1.3, 0)
PSI2 = np.asarray(Statevector(PREP2).data)

print("2-site model (side experiment, NOT the frozen benchmark):")
print(f"  H2 = {H2.to_list()}")
ev = np.linalg.eigvalsh(H2.to_matrix())
print(f"  spectrum {np.round(ev,4)}   |E|max {np.max(np.abs(ev)):.3f}")
print(f"  [H2,Q2] norm = {np.linalg.norm(H2.to_matrix()@Q2.to_matrix()-Q2.to_matrix()@H2.to_matrix()):.2e}")

T = 0.9
chi_exact = ns["exact_chi"](H2, PSI2, [T])[0]
q_exact = ns["exact_system_marginal_expectation"](H2, PSI2, Q2, T)
print(f"\nexact chi({T}) = {chi_exact.real:+.4f} {chi_exact.imag:+.4f}j")
print(f"exact <Q2>_rho^(I)({T}) = {q_exact:+.4f}")

# ---- circuit cost: this is the point of going to n=2 ----
for label, nsys, ham, prep in (("3-site (frozen)", 3, ns["HAM"], None),
                               ("2-site (this)", 2, H2, PREP2)):
    qc = ns["build_shadow_hadamard_circuit"](ham, T, ns["PHI_RE"], basis=[2]*nsys,
                                             prep=prep, method="exact")
    tq = transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
                   seed_transpiler=0)
    print(f"\n{label}: {qc.num_qubits} qubits, transpiled depth {tq.depth()}, "
          f"{tq.count_ops().get('cx',0)} CX")

# ---- full balanced shadow run on the ideal simulator ----
BASES = list(itertools.product(range(3), repeat=N2))      # 9 bases
SHOTS_PER = 4000
backend = AerSimulator()
print(f"\nideal-sim shadow run: {len(BASES)} bases x 2 quadratures, {SHOTS_PER} shots each "
      f"= {len(BASES)*2*SHOTS_PER:,} shots")

recs = {}
for phi, tag, sd in ((ns["PHI_RE"], "re", 31), (ns["PHI_IM"], "im", 32)):
    circs = [ns["build_shadow_hadamard_circuit"](H2, T, phi, basis=list(b), prep=PREP2,
                                                 method="exact") for b in BASES]
    res = backend.run(transpile(circs, backend), shots=SHOTS_PER, memory=True,
                      seed_simulator=sd).result()
    B, O, A = [], [], []
    for i, b in enumerate(BASES):
        outc, anc = ns["parse_memory"](res.get_memory(i), N2)
        B.append(np.tile(b, (len(anc), 1))); O.append(outc); A.append(anc)
    recs[tag] = ns["ShadowRecords"](t=T, phi=phi, bases=np.concatenate(B),
                                    outcomes=np.concatenate(O), ancilla=np.concatenate(A),
                                    n_circuits=len(BASES))

chi_hat, s_re, s_im = ns["estimate_hadamard_signal"](recs["re"], recs["im"])
q_hat, q_sem = ns["estimate_system_observable"]([recs["re"], recs["im"]], Q2)
print(f"\n  chi  = {chi_hat.real:+.4f} {chi_hat.imag:+.4f}j  vs exact "
      f"{chi_exact.real:+.4f} {chi_exact.imag:+.4f}j   "
      f"({abs(chi_hat.real-chi_exact.real)/s_re:.1f}, {abs(chi_hat.imag-chi_exact.imag)/s_im:.1f} sigma)")
print(f"  <Q2> = {q_hat:+.4f} +- {q_sem:.4f}  vs exact {q_exact:+.4f}   "
      f"({abs(q_hat-q_exact)/q_sem:.1f} sigma)")
ok = (abs(chi_hat.real-chi_exact.real) < 5*s_re and abs(chi_hat.imag-chi_exact.imag) < 5*s_im
      and abs(q_hat-q_exact) < 5*q_sem)
print(f"\n  VALIDATION {'PASS' if ok else 'FAIL'} -- balanced 9-basis shadow run recovers both "
      f"chi and a genuine system observable")
