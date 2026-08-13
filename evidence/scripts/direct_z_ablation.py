"""ABLATION: direct Z-basis readout of the system register vs the classical-shadow ensemble.

WHY THIS ABLATION EXISTS. Every other comparison in this project asks "which estimator?"
This one asks the more basic question a sceptic should ask: *do you need classical shadows
at all?* The conserved charge Q = sum_j Z_j is DIAGONAL in the computational basis, so it
can be read directly, every shot, with no randomisation and no 3^w inversion. If direct Z
readout resolves the symmetry just as well, the shadow machinery is unjustified.

We report the answer we found, not the one that flatters the method:

  FOR Q ALONE, DIRECT Z READOUT IS BETTER. It uses every shot (the shadow estimator
  discards any shot whose drawn basis does not match), and its per-shot second moment is
  E[Q^2] <= 9 against the shadow's <= 15. Lower variance, simpler circuit, no inversion.

  THE SHADOW ENSEMBLE EARNS ITS KEEP ELSEWHERE. A Z-only experiment can only ever see the
  Z-diagonal part of any observable. For our H that is 5 of 9 Pauli terms; the 4 missing
  ones are the hopping terms XX/YY with the LARGEST coefficients (0.65 each). The
  consequence is not a small bias: <H> is conserved and must be flat in time, but
  <H_Zdiag> DRIFTS (gap up to ~0.147 over our grid). A Z-only experiment therefore reports
  a time-varying wrong answer for a conserved quantity -- and, having no other channel,
  cannot detect that it is wrong.

So the honest motivation for shadows is NOT "they measure Q better". It is: the same shots
that give you Q also give you observables that do not commute with it, and you do not have
to decide in advance which ones you want.
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions

import json
import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator

ns = load_notebook_definitions()
HAM, CHARGE, PSI, N_SYS = ns["HAM"], ns["CHARGE"], ns["PSI"], ns["N_SYS"]
SPO = ns["SparsePauliOp"]
TS = ns["TS"]
SHOTS = 2000

H_ZDIAG = SPO.from_list([(l, c) for l, c in HAM.to_list() if set(l) <= {"I", "Z"}])
H_HOP = SPO.from_list([(l, c) for l, c in HAM.to_list() if not set(l) <= {"I", "Z"}])
print(f"H has {len(HAM)} Pauli terms: {len(H_ZDIAG)} Z-diagonal (directly measurable), "
      f"{len(H_HOP)} not (invisible to a Z-only experiment)")
print(f"  invisible terms: {[(l, float(np.real(c))) for l, c in H_HOP.to_list()]}")


def direct_z_sweep(ts, shots, seed0=900):
    """Fixed all-Z readout: 1 circuit per (t, phi). No randomisation, no inversion.
    Q is read straight off each shot as s_0 + s_1 + s_2."""
    backend = AerSimulator()
    chi, chi_q, sems_q = [], [], []
    for i, t in enumerate(ts):
        per_quad, per_quad_q, sem_q = [], [], []
        for phi, sd in ((ns["PHI_RE"], seed0 + 2 * i), (ns["PHI_IM"], seed0 + 2 * i + 1)):
            qc = ns["build_shadow_hadamard_circuit"](HAM, t, phi, basis=[2] * N_SYS,
                                                     method="exact")
            mem = backend.run(transpile(qc, backend), shots=shots, memory=True,
                              seed_simulator=sd).result().get_memory(0)
            outc, anc = ns["parse_memory"](mem, N_SYS)
            q_shot = outc.sum(axis=1)                 # Q = sum_j Z_j, read directly
            per_quad.append(float(np.mean(anc)))
            vals = anc * q_shot
            per_quad_q.append(float(np.mean(vals)))
            sem_q.append(float(np.std(vals, ddof=1) / np.sqrt(len(vals))))
        chi.append(complex(*per_quad))
        chi_q.append(complex(*per_quad_q))
        sems_q.append(sem_q)
    return np.array(chi), np.array(chi_q), np.array(sems_q)


print(f"\nrunning direct-Z sweep: {len(TS)} times x 2 quadratures x {SHOTS} shots "
      f"(1 circuit per setting, vs up to 27 for the shadow ensemble)")
CHI_D, CHIQ_D, SEMQ_D = direct_z_sweep(TS, SHOTS)

CHI_EX = ns["exact_chi"](HAM, PSI, TS)
CHIQ_EX = ns["exact_chi_O"](HAM, PSI, CHARGE, TS)

rms_chi = float(np.sqrt(np.mean(np.abs(CHI_D - CHI_EX) ** 2)))
rms_chiq = float(np.sqrt(np.mean(np.abs(CHIQ_D - CHIQ_EX) ** 2)))
sem_q_direct = float(np.mean(np.hypot(SEMQ_D[:, 0], SEMQ_D[:, 1])))

# shadow-side numbers come from the audited rows, not recomputed here
SEM_Q_SHADOW = 0.1012      # R021, measured
print("\n" + "=" * 74)
print("(1) SYMMETRY CHANNEL chi_Q -- can direct Z do it, and how well?")
print("=" * 74)
print(f"  direct-Z   chi_Q rms error {rms_chiq:.4f}, mean sem {sem_q_direct:.4f}")
print(f"  shadow     chi_Q            mean sem {SEM_Q_SHADOW:.4f}   [R021]")
print(f"  ratio sem_shadow / sem_direct = {SEM_Q_SHADOW / sem_q_direct:.2f}x")
print(f"  -> direct Z is CHEAPER for the symmetry channel: every shot contributes, and the")
print(f"     per-shot second moment is E[Q^2] <= 9 against the shadow's <= 15.")
print(f"  (chi itself is ancilla-only and identical either way: rms {rms_chi:.4f})")

print("\n" + "=" * 74)
print("(2) WHAT DIRECT Z CANNOT DO -- the reason shadows are still needed")
print("=" * 74)
rows = []
print(f"  {'t':>5} {'<H> exact':>10} {'<H_Zdiag>':>11} {'gap':>9}")
for t in (0.0, 0.9, 2.1, 4.2, 6.3, 9.0, 12.6):
    a = ns["exact_system_marginal_expectation"](HAM, PSI, HAM, t)
    b = ns["exact_system_marginal_expectation"](HAM, PSI, H_ZDIAG, t)
    print(f"  {t:>5.1f} {a:>+10.4f} {b:>+11.4f} {a-b:>+9.4f}")
    rows.append(dict(t=float(t), H_exact=float(a), H_zdiag=float(b), gap=float(a - b)))
gaps = [abs(r["gap"]) for r in rows]
print(f"\n  <H> is CONSERVED and must be flat. <H_Zdiag> drifts by up to {max(gaps):.4f}.")
print("  A Z-only experiment reports a time-varying wrong answer for a conserved quantity,")
print("  and -- having no second channel -- cannot detect that it is wrong.")

print("\n" + "=" * 74)
print("CONCLUSION (the honest motivation)")
print("=" * 74)
print("  Direct Z wins for Q alone. Shadows win the moment you want anything that does not")
print("  commute with Q -- from the SAME shots, without deciding in advance. The premium is")
print(f"  {SEM_Q_SHADOW / sem_q_direct:.2f}x on the symmetry channel; the return is every other observable.")

with open("/home/martin/Documents/QiskitHackathon/2026/evidence/direct_z_ablation.json", "w") as fh:
    json.dump(dict(shots=SHOTS, n_times=len(TS),
                   chi_rms_direct=rms_chi, chiq_rms_direct=rms_chiq,
                   sem_q_direct=sem_q_direct, sem_q_shadow=SEM_Q_SHADOW,
                   shadow_premium=SEM_Q_SHADOW / sem_q_direct,
                   n_terms_total=len(HAM), n_terms_zdiag=len(H_ZDIAG),
                   invisible_terms=[[l, float(np.real(c))] for l, c in H_HOP.to_list()],
                   H_drift=rows, max_gap=max(gaps)), fh, indent=2)
print("\nwrote evidence/direct_z_ablation.json")
