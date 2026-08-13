"""THE MOTIVATION LADDER: four ways to treat the system ("garbage") register, compared on
one figure. Each rung buys something and costs something.

  (0) DISCARD IT          -- the standard Hadamard test. The garbage is thrown away.
  (1) POST-SELECT all-Z   -- keep the SAME shadow experiment, but use only the shots whose
                             random basis happened to come out all-Z. Costs no new circuits.
  (2) DEDICATED all-Z     -- spend the whole budget on Z readout. 1 circuit per setting.
  (3) RANDOM SHADOW       -- the full ensemble, up to 3^n circuits per setting.

Rung (1) is the one worth testing and the one nobody usually checks: if naive post-selection
of the shadow data were as good as the shadow inversion, the 3^w machinery would be doing no
work. It is not -- the inversion uses shots that post-selection throws away. For Q = sum_j
Z_j, each TERM Z_j only needs b_j = Z, which is 1/3 of shots, whereas requiring ALL qubits
to be Z simultaneously is 1/3^n. That gap is the shadow estimator's actual contribution and
is measured here.

Every number is measured on the same 64-point grid at the same 2000 shots/setting.
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions

import json
import numpy as np

ns = load_notebook_definitions()
HAM, CHARGE, PSI, N_SYS = ns["HAM"], ns["CHARGE"], ns["PSI"], ns["N_SYS"]
TS, SHOTS = ns["TS"], 2000
SPO = ns["SparsePauliOp"]

print(f"running the shadow sweep once ({len(TS)} times x 2 quadratures x {SHOTS} shots)...")
SW = ns["run_time_sweep"](HAM, TS, SHOTS, ns["SEED"],
                          joint_observables={"Q": CHARGE}, verbose=False)
print("done\n")

# ---------- rung 3: the shadow estimator (what the project actually uses) ----------
sem_shadow = float(np.mean(np.hypot(SW.chi_obs_sem["Q"][:, 0], SW.chi_obs_sem["Q"][:, 1])))
chiq_shadow = SW.chi_obs["Q"]

# ---------- rung 1: post-select the all-Z shots out of that SAME experiment ----------
chiq_ps, sem_ps, kept, total = [], [], 0, 0
for rec_re, rec_im in SW.records:
    vals, sems = [], []
    for rec in (rec_re, rec_im):
        allz = np.all(rec.bases == 2, axis=1)
        total += rec.n_shots; kept += int(allz.sum())
        v = rec.ancilla[allz] * rec.outcomes[allz].sum(axis=1)   # a * (s0+s1+s2)
        vals.append(float(np.mean(v)))
        sems.append(float(np.std(v, ddof=1) / np.sqrt(len(v))))
    chiq_ps.append(complex(*vals)); sem_ps.append(sems)
chiq_ps = np.array(chiq_ps); sem_ps = np.array(sem_ps)
sem_postselect = float(np.mean(np.hypot(sem_ps[:, 0], sem_ps[:, 1])))
yield_frac = kept / total

CHIQ_EX = ns["exact_chi_O"](HAM, PSI, CHARGE, TS)
rms_shadow = float(np.sqrt(np.mean(np.abs(chiq_shadow - CHIQ_EX) ** 2)))
rms_ps = float(np.sqrt(np.mean(np.abs(chiq_ps - CHIQ_EX) ** 2)))

SEM_DEDICATED = 0.0650      # R039, measured on a dedicated all-Z sweep at the same budget

print("=" * 78)
print("THE LADDER -- chi_Q (the symmetry channel), same grid, same 2000 shots/setting")
print("=" * 78)
print(f"{'rung':<26} {'circuits/setting':>17} {'shots used':>11} {'sem on chi_Q':>13}")
print("-" * 78)
print(f"{'(0) discard the garbage':<26} {'1':>17} {'0%':>11} {'IMPOSSIBLE':>13}")
print(f"{'(1) post-select all-Z':<26} {'up to 27':>17} {yield_frac*100:>10.1f}% {sem_postselect:>13.4f}")
print(f"{'(2) dedicated all-Z':<26} {'1':>17} {'100%':>11} {SEM_DEDICATED:>13.4f}")
print(f"{'(3) random shadow':<26} {'up to 27':>17} {'100%*':>11} {sem_shadow:>13.4f}")
print("\n  * the shadow inversion uses every shot, but weights each Pauli TERM by whether")
print("    that qubit's basis matched -- 1/3 per term, not 1/3^n for all terms at once.")
print(f"\n  post-selection keeps only {yield_frac*100:.1f}% of shots (expect 1/3^{N_SYS} = "
      f"{100/3**N_SYS:.1f}%)")
print(f"  shadow inversion beats naive post-selection of the SAME data by "
      f"{sem_postselect/sem_shadow:.2f}x")
print(f"  a dedicated Z experiment still beats the shadow by "
      f"{sem_shadow/SEM_DEDICATED:.2f}x  [R039]")
print(f"\n  rms error vs exact: shadow {rms_shadow:.4f}, post-select {rms_ps:.4f}")

# ---------- what each rung can measure AT ALL ----------
zdiag = [(l, c) for l, c in HAM.to_list() if set(l) <= {"I", "Z"}]
print("\n" + "=" * 78)
print("WHAT EACH RUNG CAN MEASURE AT ALL (capability, not precision)")
print("=" * 78)
print(f"{'rung':<26} {'chi(t)':>8} {'Q':>8} {'H':>18}")
print("-" * 78)
print(f"{'(0) discard the garbage':<26} {'YES':>8} {'no':>8} {'no':>18}")
print(f"{'(1) post-select all-Z':<26} {'YES':>8} {'YES':>8} {f'{len(zdiag)}/9 terms only':>18}")
print(f"{'(2) dedicated all-Z':<26} {'YES':>8} {'YES':>8} {f'{len(zdiag)}/9 terms only':>18}")
print(f"{'(3) random shadow':<26} {'YES':>8} {'YES':>8} {'YES (all 9)':>18}")
print("\n  Rungs 1-2 are blind to the 4 hopping terms (coefficient 0.65 each), so their <H>")
print("  drifts on a CONSERVED quantity by up to 0.147 and they cannot tell. [R039]")

out = dict(shots_per_setting=SHOTS, n_times=len(TS),
           sem_shadow=sem_shadow, sem_postselect=sem_postselect,
           sem_dedicated=SEM_DEDICATED, postselect_yield=yield_frac,
           shadow_beats_postselect=sem_postselect / sem_shadow,
           dedicated_beats_shadow=sem_shadow / SEM_DEDICATED,
           rms_shadow=rms_shadow, rms_postselect=rms_ps,
           n_terms_zdiag=len(zdiag), n_terms_total=len(HAM))
with open("/home/martin/Documents/QiskitHackathon/2026/evidence/protocol_escalation.json", "w") as fh:
    json.dump(out, fh, indent=2)
print("\nwrote evidence/protocol_escalation.json")
