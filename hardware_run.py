#!/usr/bin/env python
"""Submit / fetch a shadow-Hadamard hardware job on ANY IBM backend.

Written so a colleague with access to hardware we cannot reach (e.g. Nighthawk)
can reproduce and extend our hardware arm without touching the graded notebook.

It does NOT reimplement any physics. Circuit construction, memory parsing and the
estimators are executed straight out of shadow_hadamard_challenge_PARTICIPANT.ipynb,
so this script cannot drift from the graded code.

    # one-off: save your own credentials
    python -c "from qiskit_ibm_runtime import QiskitRuntimeService as S; \
               S.save_account(channel='ibm_cloud', token='YOUR_TOKEN', overwrite=True)"

    python hardware_run.py --list                          # what can you reach?
    python hardware_run.py --submit --backend ibm_nighthawk
    python hardware_run.py --fetch <JOB_ID>

Defaults reproduce our reference point exactly (t=0.9, both quadratures,
basis [X,Y,Z], 2000 shots/circuit, optimization_level=1) so results are
directly comparable to RESULTS.md rows R008 and R018.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NOTEBOOK = os.path.join(HERE, "shadow_hadamard_challenge_PARTICIPANT.ipynb")

# Definition cells pulled from the notebook, in order. Each entry is a marker that
# must appear in the cell, plus an optional string at which to truncate the cell so
# its expensive/plotting driver tail is not executed.
NEEDED = [
    ("import qiskit", None),                       # imports
    ("BUDGET =", None),                            # budget constants, SEED
    ("def check(", None),                          # check(), sub_seed()
    ("def benchmark_hamiltonian", None),           # HAM, CHARGE, prep, PHI_RE/PHI_IM
    ("def exact_chi_O", None),                     # exact references (evaluation only)
    ("def build_controlled_evolution", None),      # Challenge 1
    ("def build_shadow_hadamard_circuit", "\ndemo = "),   # Challenge 2 (strip the drawing)
    ("def parse_memory", None),                    # Challenge 3
    ("def pauli_snapshot_values", None),           # Challenge 4 estimators
]


def load_notebook_definitions(verbose: bool = True) -> dict:
    """exec the notebook's definition cells into a namespace. No kernel required."""
    import contextlib
    import io
    import types

    if not os.path.exists(NOTEBOOK):
        sys.exit(f"cannot find {NOTEBOOK}")
    nb = json.load(open(NOTEBOOK, encoding="utf-8"))
    code = [("".join(c["source"])) for c in nb["cells"] if c["cell_type"] == "code"]

    # A real module object, registered in sys.modules: @dataclass resolves annotations
    # via sys.modules[cls.__module__], so a bare dict would raise AttributeError.
    mod = types.ModuleType("_nb_defs")
    sys.modules["_nb_defs"] = mod
    ns = mod.__dict__

    buf = io.StringIO()
    for marker, cut in NEEDED:
        hits = [s for s in code if marker in s]
        if not hits:
            sys.exit(f"notebook cell containing {marker!r} not found -- notebook changed?")
        body = hits[0].split(cut)[0] if cut else hits[0]
        with contextlib.redirect_stdout(buf):          # the cells print banners; hush them
            exec(compile(body, f"<nb:{marker}>", "exec"), ns)
    if verbose:
        print(f"loaded notebook definitions ({ns['N_SYS']} system qubits + 1 ancilla, "
              f"seed {ns['SEED']})")
    return ns


def cmd_list(_args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService
    import numpy as np
    svc = QiskitRuntimeService()
    print(f"{'backend':20s} {'qubits':>7} {'median 2q err':>14} {'queue':>6}")
    print("-" * 52)
    for b in svc.backends():
        try:
            props = b.properties()
            e2 = [props.gate_error(g.gate, g.qubits) for g in props.gates if len(g.qubits) == 2]
            e2 = [e for e in e2 if e is not None and e < 1]
            med = f"{np.median(e2):.2e}" if e2 else "n/a"
        except Exception:
            med = "n/a"
        print(f"{b.name:20s} {b.num_qubits:>7} {med:>14} {b.status().pending_jobs:>6}")


def cmd_submit(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from qiskit import transpile
    import numpy as np

    ns = load_notebook_definitions()
    svc = QiskitRuntimeService()
    backend = svc.backend(args.backend)

    circs = [ns["build_shadow_hadamard_circuit"](ns["HAM"], args.t, phi,
                                                 basis=[0, 1, 2], method=args.method, reps=args.reps)
             for phi in (ns["PHI_RE"], ns["PHI_IM"])]
    isa = transpile(circs, backend=backend, optimization_level=args.opt, seed_transpiler=1234)
    ops = isa[0].count_ops()
    twoq = sum(v for k, v in ops.items() if k in ("cz", "cx", "ecr"))

    print(f"backend {backend.name}: depth {isa[0].depth()}, {twoq} two-qubit gates")
    try:
        props = backend.properties()
        e2 = [props.gate_error(g.gate, g.qubits) for g in props.gates if len(g.qubits) == 2]
        e2 = [e for e in e2 if e is not None and e < 1]
        if e2:
            print(f"  median 2q error {np.median(e2):.2e} -> naive survival estimate "
                  f"(1-p)^{twoq} = {(1 - np.median(e2)) ** twoq:.3f}")
    except Exception:
        pass

    job = SamplerV2(mode=backend).run(isa, shots=args.shots)
    print(f"\nJOB_ID: {job.job_id()}\nstatus : {job.status()}")
    print(f"\nfetch with:  python {os.path.basename(__file__)} --fetch {job.job_id()}")


def cmd_fetch(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService
    import numpy as np

    ns = load_notebook_definitions()
    svc = QiskitRuntimeService()
    job = svc.job(args.fetch)
    print(f"job {args.fetch} on {job.backend().name}: {job.status()}")
    if str(job.status()) != "DONE":
        sys.exit("job not finished yet")
    res = job.result()

    bits = [res[i].data.c.get_bitstrings() for i in (0, 1)]
    recs = []
    for i, phi in enumerate((ns["PHI_RE"], ns["PHI_IM"])):
        outc, anc = ns["parse_memory"](bits[i], ns["N_SYS"])
        recs.append(ns["ShadowRecords"](t=args.t, phi=phi,
                                        bases=np.tile([0, 1, 2], (len(anc), 1)),
                                        outcomes=outc, ancilla=anc, n_circuits=1))

    chi, s_re, s_im = ns["estimate_hadamard_signal"](*recs)
    ref = ns["exact_chi"](ns["HAM"], ns["PSI"], [args.t])[0]
    damp = abs(chi) / abs(ref)
    print(f"\n  hardware chi({args.t}) = {chi.real:+.4f} {chi.imag:+.4f}j  "
          f"(sem {s_re:.4f}, {s_im:.4f})")
    print(f"  exact    chi({args.t}) = {ref.real:+.4f} {ref.imag:+.4f}j")
    print(f"  deviation: {abs(chi.real-ref.real)/s_re:.1f} sigma (re), "
          f"{abs(chi.imag-ref.imag)/s_im:.1f} sigma (im)")
    print(f"  SIGNAL SURVIVAL |chi_hw|/|chi_exact| = {damp:.3f}")
    print("\n  our reference points (RESULTS.md R008/R018, 3 system qubits):")
    print("    trotter reps=1, 435 two-qubit gates, ibm_marrakesh : 0.179")
    print("    exact path,     101 two-qubit gates                : see R018")
    print("\n  Report robustness claims only. The exact path is shallower purely")
    print("  because n=3 is small (O(4^n) synthesis); that inverts as n grows.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--list", action="store_true", help="list reachable backends + calibration")
    p.add_argument("--submit", action="store_true", help="submit a job")
    p.add_argument("--fetch", metavar="JOB_ID", help="fetch and analyse a finished job")
    p.add_argument("--backend", default=None, help="backend name, e.g. ibm_nighthawk")
    p.add_argument("--method", default="exact", choices=["exact", "trotter"],
                   help="exact = 101 two-qubit gates (recommended); trotter = 435")
    p.add_argument("--reps", type=int, default=1, help="Trotter repetitions (method=trotter)")
    p.add_argument("--shots", type=int, default=2000, help="shots per circuit (2 circuits)")
    p.add_argument("--t", type=float, default=0.9, help="evolution time (default matches R008)")
    p.add_argument("--opt", type=int, default=1, help="transpiler optimization_level")
    a = p.parse_args()

    if a.list:
        cmd_list(a)
    elif a.fetch:
        cmd_fetch(a)
    elif a.submit:
        if not a.backend:
            sys.exit("--submit requires --backend (see --list)")
        cmd_submit(a)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
