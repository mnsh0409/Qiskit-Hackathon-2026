"""Fetch and analyse the AQC hardware jobs from aqc_hardware_submit.py.

Three arms of the SAME Hadamard test at n=6, differing only in how the controlled evolution
is built, on every backend the job record contains. Each arm is compared against the exact
chi(t) and against the survival predicted BEFORE submission.

    python aqc_hardware_fetch.py                 # every backend in the record
    python aqc_hardware_fetch.py ibm_kingston    # just one
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json
sys.path.insert(0, REPO)
import numpy as np
from qiskit_ibm_runtime import QiskitRuntimeService

JOB = json.load(open(os.path.join(REPO, "evidence/aqc_hw_job.json")))
TIMES = JOB["times"]
EXACT = {t: complex(*JOB["chi_exact"][str(t)]) for t in TIMES}
ARMS = ("exact", "trotter", "aqc")

SVC = QiskitRuntimeService()
WANT = sys.argv[1] if len(sys.argv) > 1 else None

ready = {}
for bname, rec in JOB["jobs"].items():
    if WANT and not bname.startswith(WANT):
        continue
    try:
        st = str(SVC.job(rec["job_id"]).status())
    except Exception as e:
        # jobs submitted from ANOTHER account (ours, in the teammate's clone) are not
        # visible here -- skip them instead of crashing the whole fetch
        print(f"job {rec['job_id']} on {bname}: not visible from this account, skipping")
        continue
    print(f"job {rec['job_id']} on {bname}: {st}")
    if "DONE" in st.upper():
        ready[bname] = rec
if not ready:
    print("\nnothing ready yet -- rerun when a job finishes")
    sys.exit(0)


def analyse(bname, rec):
    res = SVC.job(rec["job_id"]).result()
    meta = rec.get("meta", JOB["meta"])              # self-contained records take priority
    exact = {t: complex(*rec["chi_exact"][str(t)]) for t in TIMES} \
        if "chi_exact" in rec else EXACT
    meas = {}
    for idx, m in enumerate(meta):
        d = res[idx].data
        arr = getattr(d, "c", None) or getattr(d, "meas", None)
        bits = arr.get_bitstrings()
        z = float(np.mean([1 - 2 * int(b[-1]) for b in bits]))      # <Z_a>
        meas.setdefault(m["arm"], {}).setdefault(m["t"], {})[m["phi"]] = z

    print("\n" + "=" * 78)
    print(f"{bname} -- chi(t), three ways to build the same controlled evolution")
    print("=" * 78)
    out = {}
    for arm in ARMS:
        p = rec["prediction"][arm]
        print(f"\n  {arm.upper()}  ({p['median_2q']:.0f} two-qubit gates, "
              f"predicted survival {p['predicted_survival']:.2e})")
        rows = []
        for t in TIMES:
            g = complex(meas[arm][t]["re"], meas[arm][t]["im"])
            e = exact[t]
            surv = abs(g) / max(abs(e), 1e-12)
            rows.append(dict(t=t, measured=[g.real, g.imag], exact=[e.real, e.imag],
                             abs_measured=abs(g), abs_exact=abs(e),
                             survival=float(surv), err=abs(g - e)))
            print(f"    t={t}:  measured {g:+.4f}   exact {e:+.4f}   "
                  f"|chi| {abs(g):.4f} vs {abs(e):.4f}   survival {surv:.3f}   "
                  f"|err| {abs(g - e):.4f}")
        out[arm] = dict(prediction=p, rows=rows,
                        mean_survival=float(np.mean([r["survival"] for r in rows])),
                        mean_err=float(np.mean([r["err"] for r in rows])))
    return out


RESULTS = {b: analyse(b, r) for b, r in ready.items()}

print("\n" + "=" * 78)
print("VERDICT")
print("=" * 78)
print(f"  {'backend':>15}{'arm':>10}{'2q gates':>10}{'pred surv':>12}"
      f"{'meas surv':>11}{'mean |err|':>12}")
print("  " + "-" * 70)
for b, o in RESULTS.items():
    for arm in ARMS:
        r = o[arm]
        print(f"  {b:>15}{arm:>10}{r['prediction']['median_2q']:>10.0f}"
              f"{r['prediction']['predicted_survival']:>12.2e}"
              f"{r['mean_survival']:>11.3f}{r['mean_err']:>12.4f}")
    print()

for b, o in RESULTS.items():
    best = min(ARMS, key=lambda a: o[a]["mean_err"])
    verdict = ("the compilation advantage (R046/R052) translates into a measured one"
               if best == "aqc" else
               "the compilation advantage does NOT translate at this size")
    print(f"  {b}: closest to exact is {best.upper()} -- {verdict}.")

# MERGE, not overwrite: a filtered run (e.g. one new backend key) used to silently drop
# every other backend's already-fetched analysis from this file -- same clobber class as
# the submit script's job-record bug, just one file over. Caught when a shots-sweep fetch
# for ibm_marrakesh_s2000 alone wiped the existing marrakesh/kingston R054 analysis.
result_path = os.path.join(REPO, "evidence/aqc_hw_result.json")
prior = json.load(open(result_path)) if os.path.exists(result_path) else {}
prior.update(RESULTS)
with open(result_path, "w") as fh:
    json.dump(prior, fh, indent=2)
print(f"\nwrote evidence/aqc_hw_result.json ({len(prior)} backend keys total)")
