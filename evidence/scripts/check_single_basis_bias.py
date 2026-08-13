"""Is the <Q> figure in R008 measuring what I claimed?

R008 used ONE fixed shadow basis [X,Y,Z]. The shadow estimator assumes bases are drawn
i.i.d. uniform per shot; with a fixed basis the indicator 1[b_j == P_j] is deterministic,
so terms whose basis does not match are structurally zero rather than averaged.

If that is what happened, the "<Q> = 1.5945 vs exact 2.2675, 16.7 sigma" line in R008 is
an artefact of my analysis, NOT evidence of hardware noise -- and it must be corrected.

Test on the IDEAL simulator, where there is no noise to blame.
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions

import numpy as np

ns = load_notebook_definitions()
HAM, CHARGE, PSI = ns["HAM"], ns["CHARGE"], ns["PSI"]
t = 0.9

exact_marginal = ns["exact_system_marginal_expectation"](HAM, PSI, CHARGE, t)
print(f"exact <Q> under rho^(I)({t})            = {exact_marginal:+.4f}")
print(f"exact <Q> under rho (input state)       = "
      f"{float(np.real(PSI.conj() @ CHARGE.to_matrix() @ PSI)):+.4f}\n")

# (1) the CORRECT protocol: random bases, as run_shadow_hadamard does
rec_re = ns["run_shadow_hadamard"](HAM, t, ns["PHI_RE"], 20000, seed=11)
rec_im = ns["run_shadow_hadamard"](HAM, t, ns["PHI_IM"], 20000, seed=12)
q_rand, sem_rand = ns["estimate_system_observable"]([rec_re, rec_im], CHARGE)
print(f"IDEAL sim, RANDOM bases (correct)       = {q_rand:+.4f} +- {sem_rand:.4f}   "
      f"({abs(q_rand-exact_marginal)/sem_rand:.1f} sigma)")

# (2) what R008 actually did: ONE fixed basis [X, Y, Z], no noise
from qiskit_aer import AerSimulator
from qiskit import transpile
backend = AerSimulator()
BASIS = [0, 1, 2]
recs = []
for phi, sd in ((ns["PHI_RE"], 21), (ns["PHI_IM"], 22)):
    qc = ns["build_shadow_hadamard_circuit"](HAM, t, phi, basis=BASIS, method="exact")
    mem = backend.run(transpile(qc, backend), shots=20000, memory=True,
                      seed_simulator=sd).result().get_memory(0)
    outc, anc = ns["parse_memory"](mem, ns["N_SYS"])
    recs.append(ns["ShadowRecords"](t=t, phi=phi,
                                    bases=np.tile(BASIS, (len(anc), 1)),
                                    outcomes=outc, ancilla=anc, n_circuits=1))
q_fix, sem_fix = ns["estimate_system_observable"](recs, CHARGE)
print(f"IDEAL sim, FIXED basis [X,Y,Z] (R008)   = {q_fix:+.4f} +- {sem_fix:.4f}   "
      f"({abs(q_fix-exact_marginal)/sem_fix:.1f} sigma)")

print(f"\nR008 reported from HARDWARE             = +1.5945 +- 0.0402  (16.7 sigma, "
      f"attributed to noise)")

# what the fixed basis actually estimates: only the Z2 term survives (b=[X,Y,Z])
z2 = ns["SparsePauliOp"].from_sparse_list([("Z", [2], 1.0)], num_qubits=ns["N_SYS"])
z2_exact = ns["exact_system_marginal_expectation"](HAM, PSI, z2, t)
print(f"\ndiagnosis: with basis [X,Y,Z] only the Z2 term of Q can match, so the estimator")
print(f"           returns 3*<Z2>, not <Q>.  3 * exact <Z2>_rho^(I) = {3*z2_exact:+.4f}")
print(f"           compare fixed-basis ideal result above: {q_fix:+.4f}")
