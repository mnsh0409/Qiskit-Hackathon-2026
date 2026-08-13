"""Fetch and analyse the AQC hardware job from aqc_hardware_submit.py.

Three arms of the SAME Hadamard test at n=6, differing only in how the controlled evolution
is built. Each is compared against the exact chi(t), and against the survival predicted
BEFORE submission.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json
sys.path.insert(0, REPO)
import numpy as np

JOB = json.load(open(os.path.join(REPO, "evidence/aqc_hw_job.json")))
TIMES = JOB["times"]
EXACT = {t: complex(*JOB["chi_exact"][str(t)]) for t in TIMES}

from qiskit_ibm_runtime import QiskitRuntimeService
job = QiskitRuntimeService().job(JOB["job_id"])
st = str(job.status())
print(f"job {JOB['job_id']} on {JOB['backend']}: {st}")
if "DONE" not in st.upper():
    print("not ready -- rerun when it finishes"); sys.exit(0)

res = job.result()
meas = {}
for idx, m in enumerate(JOB["meta"]):
    d = res[idx].data
    arr = getattr(d, "c", None) or getattr(d, "meas", None)
    bits = arr.get_bitstrings()
    z = float(np.mean([1 - 2 * int(b[-1]) for b in bits]))   # <Z_a>
    meas.setdefault(m["arm"], {}).setdefault(m["t"], {})[m["phi"]] = z

print("\n" + "=" * 78)
print("chi(t) FROM REAL HARDWARE -- same test, three ways to build the controlled evolution")
print("=" * 78)
OUT = {}
for arm in ("exact", "trotter", "aqc"):
    p = JOB["prediction"][arm]
    print(f"\n  {arm.upper()}  ({p['median_2q']:.0f} two-qubit gates, "
          f"predicted survival {p['predicted_survival']:.2e})")
    rows = []
    for t in TIMES:
        g = complex(meas[arm][t]["re"], meas[arm][t]["im"])
        e = EXACT[t]
        surv = abs(g) / max(abs(e), 1e-12)
        rows.append(dict(t=t, measured=[g.real, g.imag], exact=[e.real, e.imag],
                         abs_measured=abs(g), abs_exact=abs(e), survival=float(surv),
                         err=abs(g - e)))
        print(f"    t={t}:  measured {g:+.4f}   exact {e:+.4f}   "
              f"|chi| {abs(g):.4f} vs {abs(e):.4f}   survival {surv:.3f}   "
              f"|err| {abs(g-e):.4f}")
    OUT[arm] = dict(prediction=p, rows=rows,
                    mean_survival=float(np.mean([r["survival"] for r in rows])),
                    mean_err=float(np.mean([r["err"] for r in rows])))

print("\n" + "=" * 78)
print("VERDICT")
print("=" * 78)
print(f"  {'arm':>9}{'2q gates':>11}{'predicted surv':>16}{'measured surv':>15}{'mean |err|':>12}")
for arm in ("exact", "trotter", "aqc"):
    o = OUT[arm]
    print(f"  {arm:>9}{o['prediction']['median_2q']:>11.0f}"
          f"{o['prediction']['predicted_survival']:>16.2e}"
          f"{o['mean_survival']:>15.3f}{o['mean_err']:>12.4f}")
best = min(OUT, key=lambda a: OUT[a]["mean_err"])
print(f"\n  Closest to exact on hardware: {best.upper()}.")
if best == "aqc":
    print("  The compilation advantage (R046/R052) translates into a measurable one.")
else:
    print("  The compilation advantage does NOT translate at this size. Reported as such.")

with open(os.path.join(REPO, "evidence/aqc_hw_result.json"), "w") as fh:
    json.dump(OUT, fh, indent=2)
print("\nwrote evidence/aqc_hw_result.json")
