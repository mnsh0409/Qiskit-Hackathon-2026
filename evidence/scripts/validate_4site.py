"""Ideal-simulator validation of the 4-site side model, before spending QPU time.
Mirrors validate_2site.py's discipline. Run: python validate_4site.py
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions, get_model
import itertools
import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator

ns = load_notebook_definitions()
n, H, Q, prep, psi, label = get_model(ns, "4site")
print(label)
ev = np.linalg.eigvalsh(H.to_matrix())
print(f"spectrum {np.round(ev, 4)}")
print(f"[H,Q] norm = {np.linalg.norm(H.to_matrix()@Q.to_matrix()-Q.to_matrix()@H.to_matrix()):.2e}")

T = 0.9
chi_exact = ns["exact_chi"](H, psi, [T])[0]
q_exact = ns["exact_system_marginal_expectation"](H, psi, Q, T)
print(f"exact chi({T})={chi_exact:.4f}  exact <Q>_rho^(I)={q_exact:+.4f}")

BASES = list(itertools.product(range(3), repeat=n))
backend = AerSimulator()
recs = {}
for phi, tag, sd in ((ns["PHI_RE"], "re", 41), (ns["PHI_IM"], "im", 42)):
    circs = [ns["build_shadow_hadamard_circuit"](H, T, phi, basis=list(b), prep=prep,
                                                  method="exact") for b in BASES]
    res = backend.run(transpile(circs, backend), shots=3000, memory=True,
                      seed_simulator=sd).result()
    B, O, A = [], [], []
    for i, b in enumerate(BASES):
        outc, anc = ns["parse_memory"](res.get_memory(i), n)
        B.append(np.tile(b, (len(anc), 1))); O.append(outc); A.append(anc)
    recs[tag] = ns["ShadowRecords"](t=T, phi=phi, bases=np.concatenate(B),
                                    outcomes=np.concatenate(O), ancilla=np.concatenate(A),
                                    n_circuits=len(BASES))
chi_hat, s_re, s_im = ns["estimate_hadamard_signal"](recs["re"], recs["im"])
q_hat, q_sem = ns["estimate_system_observable"]([recs["re"], recs["im"]], Q)
print(f"shots: {len(BASES)*2*3000:,}")
print(f"chi_hat={chi_hat:.4f}  ({abs(chi_hat.real-chi_exact.real)/s_re:.1f},"
      f"{abs(chi_hat.imag-chi_exact.imag)/s_im:.1f} sigma)")
print(f"<Q>_hat={q_hat:+.4f}+-{q_sem:.4f}  ({abs(q_hat-q_exact)/q_sem:.1f} sigma)")
ok = (abs(chi_hat.real-chi_exact.real) < 5*s_re and abs(chi_hat.imag-chi_exact.imag) < 5*s_im
      and abs(q_hat-q_exact) < 5*q_sem)
print("VALIDATION", "PASS" if ok else "FAIL")
