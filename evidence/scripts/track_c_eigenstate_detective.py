"""Track C -- eigenstate detective (notebook §7.5 scaffold, never implemented).

`eigenstateness_witnesses(sweep)` is GIVEN CODE from the scaffold -- used verbatim, not
rewritten. The work here is what the scaffold actually asks for: "calibrate on a family
interpolating between the exact eigenstate |000> and strongly mixed-sector states, and
report detection power vs. shot budget."

theta=0 gives EXACTLY |000>, which CONVENTIONS §2 / Checkpoint 2 already establish is a true
eigenstate of H at E=0.55 -- so the calibration family has a guaranteed-true zero point, not
an assumed one.

Reduced budget throughout (this is exploratory, not the Part A/B official 256,000-shot
record set): N_TIMES=16 points spanning the SAME T_max=12.6 (DT=0.7875, not the official
0.2) so the state gets the same total dephasing time to reveal mixedness, just measured more
coarsely. Nyquist check: pi/DT=3.99 > full spectral radius 2.635, still alias-free.
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions

import json
import time
import numpy as np

ns = load_notebook_definitions()
HAM, CHARGE, N_SYS = ns["HAM"], ns["CHARGE"], ns["N_SYS"]
QuantumCircuit, SparsePauliOp = ns["QuantumCircuit"], ns["SparsePauliOp"]
run_time_sweep = ns["run_time_sweep"]
estimate_system_observable = ns["estimate_system_observable"]
sub_seed, T_MAX = ns["sub_seed"], ns["T_MAX"]

N_TIMES_REDUCED = 16
TS_REDUCED = np.linspace(0, T_MAX, N_TIMES_REDUCED, endpoint=False)
print(f"reduced grid: {N_TIMES_REDUCED} points over T_max={T_MAX:.2f}  "
      f"(DT={TS_REDUCED[1]-TS_REDUCED[0]:.4f} vs official 0.2)")


def prep(theta):
    qc = QuantumCircuit(N_SYS, name="prep")
    qc.ry(theta, 0)
    return qc


def eigenstateness_witnesses(sweep):
    """GIVEN, from the notebook's own §7.5 scaffold -- verbatim."""
    w1 = 1.0 - np.mean(np.abs(sweep.chi))
    o = SparsePauliOp.from_sparse_list([("Z", [0], 1.0)], N_SYS)
    traj = np.array([estimate_system_observable(list(p), o)[0] for p in sweep.records])
    w2 = float(np.std(traj))
    return w1, w2


def bootstrap_w1(sweep, n_boot=200, seed=0):
    """Parametric bootstrap of w1 alone: perturb each chi(t) by its own sem, same style as
    the notebook's own bootstrap_uncertainties (Challenge 9)."""
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        chi_b = (sweep.chi.real + rng.normal(scale=sweep.chi_sem[:, 0])
                 + 1j * (sweep.chi.imag + rng.normal(scale=sweep.chi_sem[:, 1])))
        vals.append(1.0 - np.mean(np.abs(chi_b)))
    return float(np.std(vals))


# ============================================================ (1) calibration family
THETAS = [0.0, 0.2, 0.4, 0.65, 1.0, 1.3]
SHOTS_CAL = 1000
print(f"\n(1) calibration family: theta in {THETAS}, {SHOTS_CAL} shots/setting\n")
print(f"{'theta':>6} {'w1':>9} {'sem(w1)':>9} {'z=w1/sem':>9} {'w2':>9}")
print("-" * 48)

CAL_ROWS = []
_t0 = time.time()
for theta in THETAS:
    sweep = run_time_sweep(HAM, TS_REDUCED, SHOTS_CAL, sub_seed(f"trackc-theta-{theta}"),
                           prep=prep(theta), verbose=False)
    w1, w2 = eigenstateness_witnesses(sweep)
    sem_w1 = bootstrap_w1(sweep, seed=sub_seed(f"trackc-boot-{theta}"))
    z = w1 / sem_w1 if sem_w1 > 0 else float("inf")
    print(f"{theta:>6.2f} {w1:>9.4f} {sem_w1:>9.4f} {z:>9.2f} {w2:>9.4f}")
    CAL_ROWS.append(dict(theta=theta, w1=float(w1), sem_w1=float(sem_w1), z=float(z),
                         w2=float(w2), total_shots=int(sweep.total_shots)))
print(f"\ncalibration family took {time.time()-_t0:.1f}s")
print("theta=0.0 is an EXACT eigenstate (Checkpoint 2: |000> at E=0.55) -- w1/w2 there are")
print("the noise floor, not an assumption; everything above it is genuine detected mixedness.")

# ============================================================ (2) detection power vs shots
SHOT_COUNTS = [200, 800, 3200]
DETECT_THETAS = [0.2, 1.3]     # weakly mixed vs our actual benchmark (strongly mixed)
print(f"\n(2) detection power vs shot budget: theta in {DETECT_THETAS}, "
      f"shots in {SHOT_COUNTS}\n")
print(f"{'theta':>6} {'shots':>6} {'w1':>9} {'sem(w1)':>9} {'z':>7}")
print("-" * 42)

POWER_ROWS = []
_t0 = time.time()
for theta in DETECT_THETAS:
    for n_sh in SHOT_COUNTS:
        sweep = run_time_sweep(HAM, TS_REDUCED, n_sh,
                               sub_seed(f"trackc-power-{theta}", n_sh),
                               prep=prep(theta), verbose=False)
        w1, _ = eigenstateness_witnesses(sweep)
        sem_w1 = bootstrap_w1(sweep, seed=sub_seed(f"trackc-power-boot-{theta}", n_sh))
        z = w1 / sem_w1 if sem_w1 > 0 else float("inf")
        print(f"{theta:>6.2f} {n_sh:>6d} {w1:>9.4f} {sem_w1:>9.4f} {z:>7.2f}")
        POWER_ROWS.append(dict(theta=theta, shots=n_sh, w1=float(w1), sem_w1=float(sem_w1),
                               z=float(z)))
print(f"\ndetection-power sub-study took {time.time()-_t0:.1f}s")

with open("/home/martin/Documents/QiskitHackathon/2026/evidence/track_c_result.json", "w") as fh:
    json.dump(dict(calibration=CAL_ROWS, detection_power=POWER_ROWS,
                   n_times_reduced=N_TIMES_REDUCED, t_max=float(T_MAX)), fh, indent=2)
print("\nwrote evidence/track_c_result.json")
