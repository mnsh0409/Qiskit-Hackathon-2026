"""PROTOTYPE: symmetry-resolved DENSITY OF STATES from the existing shadow-Hadamard
pipeline, with the input state swapped from |psi> to the maximally mixed state.

MOTIVATION. The DOS is the Fourier transform of Tr[U(t)] -- the TRACE of the propagator,
not an expectation in a particular state. Our chi(t) = Tr[U(t) rho]. So setting rho = I/2^n
turns the same experiment into a DOS estimator, and our chi_Q channel turns it into a
CHARGE-RESOLVED DOS estimator -- which for a fermionic system under Jordan-Wigner is a
particle-number-resolved DOS, since N = (n - Q)/2.

HOW THE MIXED STATE IS REALISED, and why not the obvious way. Random-state typicality has
error O(2^(-n/2)) = 35% at n=3 -- useless here. But the trace is EXACTLY the sum over
computational basis states, Tr[U] = sum_z <z|U|z>, so averaging the ordinary Hadamard test
over all 2^n = 8 basis-state preparations is exact, not stochastic, and costs only 8 preps.
(At large n one would go back to typicality; at n=3 exact enumeration is strictly better.)

NOTHING ELSE CHANGES. Same circuit builder, same parse_memory, same three estimators, same
matrix pencil, same bootstrap -- only `prep` differs. That is the point of the prototype:
to find out whether the existing machinery transfers, not to build a new pipeline.

WHAT TO EXPECT, stated before running so it is falsifiable:
  - peaks should now sit at the FULL spectrum (all 8 eigenvalues), not the 4 populated ones
  - peak weights should be ~degeneracy/2^n rather than state populations
  - the chi_Q/chi ratio at each peak should give that level's charge sector
  - the near-degenerate UNPOPULATED pair near E~0.45 (full-spectrum min gap 0.0136, per
    Gate 0) CANNOT be resolved at T_max=12.4 -- Rayleigh limit is 2pi/12.4 = 0.507, so that
    pair must merge into one peak. Predicted failure, not a surprise.
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions

import json
import time
import numpy as np

ns = load_notebook_definitions()
HAM, CHARGE, N_SYS = ns["HAM"], ns["CHARGE"], ns["N_SYS"]
QuantumCircuit = ns["QuantumCircuit"]

N_TIMES, DT, SHOTS = 32, 0.4, 500
TS = np.arange(N_TIMES) * DT
DIM = 2 ** N_SYS
print(f"grid: {N_TIMES} times, dt={DT}, T_max={TS[-1]:.1f}; {DIM} basis-state preps; "
      f"{SHOTS} shots/setting")
print(f"total {DIM * N_TIMES * 2 * SHOTS:,} shots  (Nyquist pi/dt={np.pi/DT:.2f} vs "
      f"spectral radius {np.max(np.abs(np.linalg.eigvalsh(HAM.to_matrix()))):.3f} -- no aliasing)")


def basis_prep(z):
    qc = QuantumCircuit(N_SYS, name=f"prep{z}")
    for j in range(N_SYS):
        if (z >> j) & 1:
            qc.x(j)
    return qc


# ---------- exact references (evaluation only) ----------
def exact_trace_signals(ts):
    Hm, Qm = HAM.to_matrix(), CHARGE.to_matrix()
    ev, evec = np.linalg.eigh(Hm)
    q_diag = np.real(np.diag(evec.conj().T @ Qm @ evec))
    chi = np.array([np.sum(np.exp(-1j * ev * t)) / DIM for t in ts])
    chi_q = np.array([np.sum(q_diag * np.exp(-1j * ev * t)) / DIM for t in ts])
    return chi, chi_q, ev, q_diag


CHI_EX, CHIQ_EX, EVALS_FULL, QDIAG_FULL = exact_trace_signals(TS)
print(f"\nfull spectrum (all {DIM} levels): {np.round(EVALS_FULL, 4).tolist()}")
print(f"their charges:                    {np.round(QDIAG_FULL).astype(int).tolist()}")
print(f"full-spectrum min gap: {np.min(np.diff(EVALS_FULL)):.4f}  "
      f"vs Rayleigh limit 2pi/T_max = {2*np.pi/TS[-1]:.4f}  -> "
      f"{'SOME PAIRS UNRESOLVABLE (expected)' if np.min(np.diff(EVALS_FULL)) < 2*np.pi/TS[-1] else 'all resolvable'}")

# ---------- run the SAME sweep machinery, once per basis state ----------
t0 = time.time()
chis, chiqs = [], []
for z in range(DIM):
    sw = ns["run_time_sweep"](HAM, TS, SHOTS, ns["sub_seed"](f"dos-z{z}"),
                              joint_observables={"Q": CHARGE}, prep=basis_prep(z),
                              verbose=False)
    chis.append(sw.chi); chiqs.append(sw.chi_obs["Q"])
    print(f"  prep |{z:0{N_SYS}b}>  done ({time.time()-t0:.0f}s elapsed)")

CHI_DOS = np.mean(chis, axis=0)          # = Tr[U(t)]/2^n
CHIQ_DOS = np.mean(chiqs, axis=0)        # = Tr[Q U(t)]/2^n

# cache immediately: the sweep above costs ~7 min and a downstream bug should not repeat it
np.savez("/home/martin/Documents/QiskitHackathon/2026/evidence/dos_signals.npz",
         ts=TS, chi=CHI_DOS, chi_q=CHIQ_DOS, chi_exact=CHI_EX, chiq_exact=CHIQ_EX)

err = np.abs(CHI_DOS - CHI_EX)
errq = np.abs(CHIQ_DOS - CHIQ_EX)
print(f"\nmeasured vs exact trace signals: chi rms {np.sqrt(np.mean(err**2)):.4f}, "
      f"chi_Q rms {np.sqrt(np.mean(errq**2)):.4f}")
print(f"  chi(0) = {CHI_DOS[0].real:+.4f} (exact 1.0000 -- Tr[I]/2^n)")
print(f"  chi_Q(0) = {CHIQ_DOS[0].real:+.4f} (exact {CHIQ_EX[0].real:+.4f} -- Tr[Q]/2^n)")

# ---------- run the UNMODIFIED Track-A reconstruction on it ----------
print("\nrunning the unmodified reconstruct() on the DOS signals...")
E, P, Qlab, rank = ns["reconstruct"](TS, CHI_DOS, CHIQ_DOS)
print(f"rank {rank}, {len(E)} modes\n")
print(f"{'E found':>10} {'weight':>9} {'q_hat':>8} | {'nearest exact E':>16} {'its q':>6} "
      f"{'degeneracy':>11}")
ROWS = []
for e, p, q in zip(E, P, Qlab):
    k = int(np.argmin(np.abs(EVALS_FULL - e)))
    deg = int(np.sum(np.abs(EVALS_FULL - EVALS_FULL[k]) < 2 * np.pi / TS[-1]))
    print(f"{e:>10.4f} {p:>9.4f} {q:>8.3f} | {EVALS_FULL[k]:>16.4f} "
          f"{np.round(QDIAG_FULL[k]).astype(int):>6d} {deg:>11d}")
    ROWS.append(dict(E_found=float(e), weight=float(p), q_hat=float(q),
                     nearest_exact_E=float(EVALS_FULL[k]),
                     its_charge=int(np.round(QDIAG_FULL[k])), merged_degeneracy=deg))

print(f"\nweights sum to {P.sum():.4f} (expect ~1.0 = Tr[I]/2^n)")
print("\nINTERPRETATION: peak weights are now DEGENERACIES/2^n, not state populations, and")
print("q_hat is the mean charge of whatever levels merged into that peak. Pairs closer than")
print("the Rayleigh limit necessarily merge -- that is a resolution limit of the time grid,")
print("not a failure of the estimator, and it was predicted before the run.")

with open("/home/martin/Documents/QiskitHackathon/2026/evidence/dos_prototype_result.json",
          "w") as fh:
    json.dump(dict(n_times=N_TIMES, dt=DT, shots=SHOTS, total_shots=DIM*N_TIMES*2*SHOTS,
                   full_spectrum=[float(x) for x in EVALS_FULL],
                   full_charges=[int(x) for x in np.round(QDIAG_FULL)],
                   chi_rms=float(np.sqrt(np.mean(err**2))),
                   chiq_rms=float(np.sqrt(np.mean(errq**2))),
                   rank=int(rank), modes=ROWS, weight_sum=float(P.sum())), fh, indent=2)
print("\nwrote evidence/dos_prototype_result.json")
