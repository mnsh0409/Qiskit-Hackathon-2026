#!/usr/bin/env python
"""Find the best physical-qubit window for our circuit on a given backend.

Not a reimplementation of packing.py (which cannot run here — see HANDOVER.md /
BUGLOG for why). This solves the same practical problem with stock Qiskit:

  1. Score every coupling-map edge by its CALIBRATED two-qubit gate error.
  2. Greedily grow connected windows of the needed size, seeded from the
     best-calibrated edges (not randomly), so the search targets good hardware
     rather than sampling blindly.
  3. Transpile our actual circuit pinned to each candidate window
     (initial_layout=..., optimization_level=3) and read the REAL post-transpile
     two-qubit gate count and depth -- topology is roughly homogeneous on a
     heavy-hex device, so gate count barely moves between windows; calibrated
     error on the specific edges actually used is what varies, and that is
     scored from the transpiled circuit's real gate list, not a window average.
  4. Rank by predicted survival = product over used 2-qubit gates of (1 - that
     gate's calibrated error) -- exact, not the median-based estimate used
     earlier in RESULTS.md.

Usage:
    python layout_search.py --backend ibm_kingston --model frozen --candidates 12
    python layout_search.py --backend ibm_kingston --model 4site  --candidates 12
"""
from __future__ import annotations

import argparse
import sys

sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions  # noqa: E402


def get_model(ns, name):
    import numpy as np
    if name == "frozen":
        prep = None
        return ns["N_SYS"], ns["HAM"], prep, "frozen 3-qubit benchmark (CONVENTIONS §2)"
    if name == "2site":
        SPO, QC = ns["SparsePauliOp"], ns["QuantumCircuit"]
        H = SPO.from_sparse_list(
            [("XX", [0, 1], 0.65), ("YY", [0, 1], 0.65), ("ZZ", [0, 1], 0.25),
             ("Z", [0], 0.40), ("Z", [1], -0.50)], num_qubits=2).simplify()
        prep = QC(2); prep.ry(1.3, 0)
        return 2, H, prep, "reduced 2-site side model -- robustness claims only"
    if name == "4site":
        SPO, QC = ns["SparsePauliOp"], ns["QuantumCircuit"]
        n = 4
        terms = []
        for i in range(n - 1):
            terms += [("XX", [i, i + 1], 0.65), ("YY", [i, i + 1], 0.65),
                      ("ZZ", [i, i + 1], 0.25)]
        for i, h in enumerate((0.40, -0.50, 0.15, 0.20)):
            terms.append(("Z", [i], h))
        H = SPO.from_sparse_list(terms, num_qubits=n).simplify()
        prep = QC(n); prep.ry(1.3, 0)
        return n, H, prep, "extended 4-site side model -- robustness claims only, NOT the benchmark"
    sys.exit(f"unknown model {name!r}")


def edge_errors(backend):
    """{(q0,q1): calibrated two-qubit error} for every coupling-map edge, both orders."""
    target = backend.target
    out = {}
    for names in target.operation_names:
        if target.operation_from_name(names).num_qubits != 2:
            continue
        for qargs in target.qargs_for_operation_name(names) or []:
            if qargs is None or len(qargs) != 2:
                continue
            props = target[names].get(qargs)
            err = getattr(props, "error", None) if props else None
            if err is not None:
                out[qargs] = min(out.get(qargs, 1.0), err)
    return out


def best_windows(coupling_edges, err, k, n_candidates, seed=0):
    """Greedily grow connected k-qubit windows from the best-calibrated edges."""
    import random
    import rustworkx as rx

    nodes = sorted({q for e in coupling_edges for q in e})
    idx = {q: i for i, q in enumerate(nodes)}
    g = rx.PyGraph()
    g.add_nodes_from(nodes)
    for (a, b), e in err.items():
        if a in idx and b in idx:
            g.add_edge(idx[a], idx[b], e)

    ranked_edges = sorted(err.items(), key=lambda kv: kv[1])
    rng = random.Random(seed)
    seen = set()
    windows = []
    for (a, b), _ in ranked_edges:
        if len(windows) >= n_candidates * 3:      # over-generate, dedupe, trim later
            break
        window = {idx[a], idx[b]}
        frontier = set(g.neighbors(idx[a])) | set(g.neighbors(idx[b]))
        frontier -= window
        while len(window) < k and frontier:
            # prefer the lowest-error edge into the current window
            cand = min(frontier, key=lambda v: min(
                (g.get_edge_data(v, w) for w in g.neighbors(v) if w in window),
                default=1.0))
            window.add(cand)
            frontier |= set(g.neighbors(cand))
            frontier -= window
        if len(window) == k:
            phys = tuple(sorted(nodes[i] for i in window))
            if phys not in seen:
                seen.add(phys)
                mean_err = sum(err.get((a, b), err.get((b, a), 1.0))
                               for a in phys for b in phys if a < b
                               and ((a, b) in err or (b, a) in err)) or 1.0
                windows.append(phys)
    return windows[:n_candidates]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--backend", required=True)
    p.add_argument("--model", default="frozen", choices=["frozen", "2site", "4site"])
    p.add_argument("--t", type=float, default=0.9)
    p.add_argument("--method", default="exact", choices=["exact", "trotter"])
    p.add_argument("--reps", type=int, default=1)
    p.add_argument("--candidates", type=int, default=10)
    p.add_argument("--opt", type=int, default=3)
    args = p.parse_args()

    from qiskit import transpile
    from qiskit_ibm_runtime import QiskitRuntimeService

    ns = load_notebook_definitions()
    n, H, prep, label = get_model(ns, args.model)
    print(f"model: {label}  ({n} system qubits, {n+1} total)")

    svc = QiskitRuntimeService()
    backend = svc.backend(args.backend)
    err = edge_errors(backend)
    edges = list(err.keys())
    print(f"backend: {backend.name}  ({len(edges)} directed coupling edges, "
          f"median 2q err {sorted(err.values())[len(err)//2]:.2e})")

    windows = best_windows(edges, err, n + 1, args.candidates)
    print(f"\nevaluating {len(windows)} candidate windows (greedy, seeded from lowest-error edges)\n")

    qc = ns["build_shadow_hadamard_circuit"](H, args.t, ns["PHI_RE"], basis=[0] * n,
                                             prep=prep, method=args.method, reps=args.reps)

    results = []
    print(f"{'window':>28} | {'depth':>6} {'2q gates':>9} {'predicted survival':>19}")
    print("-" * 70)
    for w in windows:
        try:
            tq = transpile(qc, backend=backend, optimization_level=args.opt,
                           initial_layout=list(w), seed_transpiler=0)
        except Exception as ex:
            print(f"{str(w):>28} | transpile failed: {type(ex).__name__}")
            continue
        used = [instr.qubits for instr in tq.data
                if len(instr.qubits) == 2 and not getattr(instr.operation, "_directive", False)]
        surv = 1.0
        two_q = 0
        for qargs in used:
            phys = tuple(tq.find_bit(q).index for q in qargs)
            e = err.get(phys, err.get(phys[::-1]))
            if e is not None:
                surv *= (1 - e)
                two_q += 1
        results.append(dict(window=w, depth=tq.depth(), two_q=two_q, survival=surv))
        print(f"{str(w):>28} | {tq.depth():>6} {two_q:>9} {surv:>19.4f}")

    if not results:
        sys.exit("no candidate transpiled successfully")
    best = max(results, key=lambda r: r["survival"])
    print(f"\nBEST: window {best['window']}, {best['two_q']} two-qubit gates, "
          f"predicted survival {best['survival']:.4f}")
    print(f"\nsubmit with:\n  python hardware_run.py --submit --backend {args.backend} "
          f"--model {args.model} --initial-layout \"{','.join(map(str, best['window']))}\"")


if __name__ == "__main__":
    main()
