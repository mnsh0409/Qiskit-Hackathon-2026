"""Reproducible replacement for R025's original ad-hoc, unscripted check (flagged by the
C4 audit: not committed, not reproducible, and its n=3/opt=1/exact figure (92) diverged
from R018's independently-verified 101 for the nominally same circuit).

ROOT CAUSE, found and confirmed exactly (not hand-waved): R018 was submitted by
evidence/scripts/submit_hw_2x2.py, which transpiles with
`seed_transpiler=sub_seed("hw-transpile")` -- the project's own deterministic seed
derivation, NOT a literal constant. My original interactive R025 checks and even my first
attempt at this replacement script guessed seed_transpiler=1234 (hardware_run.py's CLI
default, added later and unrelated). Recomputing `sub_seed("hw-transpile")` explicitly
(it evaluates to 2020549847 under SEED=2026) and re-transpiling with THAT seed reproduces
R018's confirmed 101 two-qubit gates exactly, on both quadrature circuits. Verified before
writing this file -- see the git commit message for the standalone check.

Run: python transpile_cost_n3_n4.py
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions, get_model

from qiskit import transpile
from qiskit_ibm_runtime import QiskitRuntimeService

ns = load_notebook_definitions()
_SEED_TRANSPILER = ns["sub_seed"]("hw-transpile")   # == 2020549847; matches submit_hw_2x2.py
svc = QiskitRuntimeService()
backend = svc.backend("ibm_kingston")

print(f"backend: {backend.name}\n")
print(f"{'n':>3} {'total q':>8} {'method':>8} {'opt':>4} {'depth':>6} {'2q gates':>9}")
print("-" * 46)

rows = []
for model_name, n_declared in (("frozen", 3), ("4site", 4)):
    n, H, Q, prep, psi, label = get_model(ns, model_name)
    assert n == n_declared
    basis = [0, 1, 2][:n]                        # EXACTLY what hardware_run.py's fixed-basis
                                                   # mode uses -- for n=4 this truncates to 3
                                                   # entries (qubit 3 gets no rotation, which
                                                   # is a real but harmless latent bug: it has
                                                   # zero effect on 2-qubit gate count, since
                                                   # basis rotations are 1-qubit-only and never
                                                   # touch the controlled-U's CX/CZ structure)
    for method, reps in (("exact", 1), ("trotter", 1)):
        qc = ns["build_shadow_hadamard_circuit"](H, 0.9, ns["PHI_RE"], basis=basis, prep=prep,
                                                  method=method, reps=reps)
        for opt in (1, 3):
            tq = transpile(qc, backend=backend, optimization_level=opt, seed_transpiler=_SEED_TRANSPILER)
            ops = tq.count_ops()
            twoq = ops.get("cz", 0) + ops.get("cx", 0) + ops.get("ecr", 0)
            print(f"{n:>3} {n+1:>8} {method:>8} {opt:>4} {tq.depth():>6} {twoq:>9}")
            rows.append(dict(n=n, method=method, opt=opt, depth=tq.depth(), two_q=int(twoq)))

r3_e1 = next(r["two_q"] for r in rows if r["n"] == 3 and r["method"] == "exact" and r["opt"] == 1)
r3_t1 = next(r["two_q"] for r in rows if r["n"] == 3 and r["method"] == "trotter" and r["opt"] == 1)
r4_e3 = next(r["two_q"] for r in rows if r["n"] == 4 and r["method"] == "exact" and r["opt"] == 3)
r4_t3 = next(r["two_q"] for r in rows if r["n"] == 4 and r["method"] == "trotter" and r["opt"] == 3)
r3_e3 = next(r["two_q"] for r in rows if r["n"] == 3 and r["method"] == "exact" and r["opt"] == 3)
r3_t3 = next(r["two_q"] for r in rows if r["n"] == 3 and r["method"] == "trotter" and r["opt"] == 3)

print(f"\nn=3, opt=3: trotter/exact = {r3_t3}/{r3_e3} = {r3_t3/r3_e3:.2f}x")
print(f"n=4, opt=3: trotter/exact = {r4_t3}/{r4_e3} = {r4_t3/r4_e3:.2f}x")
print(f"\nR018 cross-check: n=3/opt=1/exact reported {r3_e1} here vs 101 independently "
      f"confirmed in R018's real submission -- {'MATCH' if r3_e1 == 101 else 'MISMATCH'}")
