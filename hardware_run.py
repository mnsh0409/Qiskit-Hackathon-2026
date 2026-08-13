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

    python hardware_run.py --list
    python hardware_run.py --submit --backend ibm_nighthawk                 # chi only, 2 circuits
    python hardware_run.py --submit --backend ibm_nighthawk --model 2site --shadow
    python hardware_run.py --fetch <JOB_ID>

TWO MODES, and the difference matters (see BUGLOG B04):

  default (fixed basis) -- 2 circuits. Estimates chi(t) ONLY. The shadow estimator
      3^w prod(s_j) 1[b_j == P_j] is unbiased only for i.i.d.-uniform bases; with a
      single fixed basis the indicator is deterministic and system observables come
      out as a different quantity entirely. This script REFUSES to report them.

  --shadow (balanced ensemble) -- 3^n bases x 2 quadratures, equal shots each. The
      empirical basis distribution is then exactly uniform, so system observables
      (<Q>, <H>, ...) are valid. At n=2 that is only 9x2 = 18 circuits, which is why
      --model 2site is the cheap way to get a genuine shadow result on hardware.

MODELS:
  frozen  -- the 3-qubit benchmark of CONVENTIONS §2 (4 qubits with the ancilla)
  2site   -- a reduced 2-qubit instance (3 qubits total). NOT the frozen benchmark;
             a separate side model, for ROBUSTNESS CLAIMS ONLY. Going-further
             robustness item 4 asks for exactly this.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NOTEBOOK = os.path.join(HERE, "shadow_hadamard_challenge_PARTICIPANT.ipynb")
JOBDB = os.path.join(HERE, "hardware_jobs.json")

NEEDED = [
    ("import qiskit", None),
    ("BUDGET =", None),
    ("def check(", None),
    ("def benchmark_hamiltonian", None),
    ("def exact_chi_O", None),
    ("def build_controlled_evolution", None),
    ("def build_shadow_hadamard_circuit", "\ndemo = "),
    ("def parse_memory", None),
    ("def pauli_snapshot_values", None),
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

    # A real module object registered in sys.modules: @dataclass resolves annotations via
    # sys.modules[cls.__module__], so a bare dict raises AttributeError.
    mod = types.ModuleType("_nb_defs")
    sys.modules["_nb_defs"] = mod
    ns = mod.__dict__

    buf = io.StringIO()
    for marker, cut in NEEDED:
        hits = [s for s in code if marker in s]
        if not hits:
            sys.exit(f"notebook cell containing {marker!r} not found -- notebook changed?")
        body = hits[0].split(cut)[0] if cut else hits[0]
        with contextlib.redirect_stdout(buf):
            exec(compile(body, f"<nb:{marker}>", "exec"), ns)
    if verbose:
        print(f"loaded notebook definitions ({ns['N_SYS']} system qubits + 1 ancilla, "
              f"seed {ns['SEED']})")
    return ns


def get_model(ns: dict, name: str):
    """-> (n_sys, H, Q, prep, psi, label). 'frozen' is the graded benchmark."""
    import numpy as np
    if name == "frozen":
        return (ns["N_SYS"], ns["HAM"], ns["CHARGE"], None, ns["PSI"],
                "frozen 3-qubit benchmark (CONVENTIONS §2)")
    if name == "2site":
        SPO, QC, SV = ns["SparsePauliOp"], ns["QuantumCircuit"], ns["Statevector"]
        n = 2
        H = SPO.from_sparse_list(
            [("XX", [0, 1], 0.65), ("YY", [0, 1], 0.65), ("ZZ", [0, 1], 0.25),
             ("Z", [0], 0.40), ("Z", [1], -0.50)], num_qubits=n).simplify()
        Q = SPO.from_sparse_list([("Z", [j], 1.0) for j in range(n)], num_qubits=n)
        prep = QC(n, name="prep"); prep.ry(1.3, 0)
        return (n, H, Q, prep, np.asarray(SV(prep).data),
                "reduced 2-site side model -- ROBUSTNESS CLAIMS ONLY, not the benchmark")
    sys.exit(f"unknown model {name!r}")


def _jobdb(update: dict | None = None) -> dict:
    db = json.load(open(JOBDB)) if os.path.exists(JOBDB) else {}
    if update:
        db.update(update)
        with open(JOBDB, "w") as fh:
            json.dump(db, fh, indent=2)
    return db


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
    n, H, Q, prep, psi, label = get_model(ns, args.model)
    print(f"model: {label}")

    bases = ([list(b) for b in itertools.product(range(3), repeat=n)] if args.shadow
             else [[0, 1, 2][:n]])
    phis = [ns["PHI_RE"], ns["PHI_IM"]]
    plan = [(pi, b) for pi in range(2) for b in bases]           # submission order
    circs = [ns["build_shadow_hadamard_circuit"](H, args.t, phis[pi], basis=b, prep=prep,
                                                 method=args.method, reps=args.reps)
             for pi, b in plan]

    svc = QiskitRuntimeService()
    backend = svc.backend(args.backend)
    isa = transpile(circs, backend=backend, optimization_level=args.opt, seed_transpiler=1234)
    twoq = max(sum(v for k, v in c.count_ops().items() if k in ("cz", "cx", "ecr")) for c in isa)
    print(f"{len(circs)} circuits ({'balanced shadow ensemble' if args.shadow else 'fixed basis'}), "
          f"depth {max(c.depth() for c in isa)}, {twoq} two-qubit gates")
    try:
        props = backend.properties()
        e2 = [props.gate_error(g.gate, g.qubits) for g in props.gates if len(g.qubits) == 2]
        e2 = [e for e in e2 if e is not None and e < 1]
        if e2:
            print(f"  {backend.name} median 2q error {np.median(e2):.2e} -> naive survival "
                  f"(1-p)^{twoq} = {(1-np.median(e2))**twoq:.3f}")
    except Exception:
        pass

    job = SamplerV2(mode=backend).run(isa, shots=args.shots)
    _jobdb({job.job_id(): dict(model=args.model, shadow=bool(args.shadow), t=args.t,
                               method=args.method, reps=args.reps, shots=args.shots,
                               backend=backend.name, n=n,
                               plan=[[pi, b] for pi, b in plan])})
    print(f"\nJOB_ID: {job.job_id()}\nstatus : {job.status()}")
    print(f"total shots: {len(circs) * args.shots:,}")
    print(f"\nfetch with:  python {os.path.basename(__file__)} --fetch {job.job_id()}")


def cmd_fetch(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService
    import numpy as np

    meta = _jobdb().get(args.fetch)
    if meta is None:
        sys.exit(f"job {args.fetch} not in {JOBDB}. It was submitted by a different copy of "
                 f"this script; re-run --submit or add its metadata by hand.")

    ns = load_notebook_definitions()
    n, H, Q, prep, psi, label = get_model(ns, meta["model"])
    print(f"model: {label}")
    print(f"basis mode: {'balanced shadow ensemble' if meta['shadow'] else 'FIXED basis'}")

    svc = QiskitRuntimeService()
    job = svc.job(args.fetch)
    print(f"job {args.fetch} on {job.backend().name}: {job.status()}")
    if str(job.status()) != "DONE":
        sys.exit("job not finished yet")
    res = job.result()

    phis = [ns["PHI_RE"], ns["PHI_IM"]]
    acc = {0: dict(b=[], o=[], a=[]), 1: dict(b=[], o=[], a=[])}
    for idx, (pi, basis) in enumerate(meta["plan"]):
        outc, anc = ns["parse_memory"](res[idx].data.c.get_bitstrings(), n)
        acc[pi]["b"].append(np.tile(basis, (len(anc), 1)))
        acc[pi]["o"].append(outc)
        acc[pi]["a"].append(anc)
    recs = [ns["ShadowRecords"](t=meta["t"], phi=phis[pi],
                                bases=np.concatenate(acc[pi]["b"]),
                                outcomes=np.concatenate(acc[pi]["o"]),
                                ancilla=np.concatenate(acc[pi]["a"]),
                                n_circuits=len(acc[pi]["b"])) for pi in (0, 1)]

    chi, s_re, s_im = ns["estimate_hadamard_signal"](*recs)
    ref = ns["exact_chi"](H, psi, [meta["t"]])[0]
    print(f"\n  hardware chi({meta['t']}) = {chi.real:+.4f} {chi.imag:+.4f}j  "
          f"(sem {s_re:.4f}, {s_im:.4f})")
    print(f"  exact    chi({meta['t']}) = {ref.real:+.4f} {ref.imag:+.4f}j")
    print(f"  deviation: {abs(chi.real-ref.real)/s_re:.1f} sigma (re), "
          f"{abs(chi.imag-ref.imag)/s_im:.1f} sigma (im)")
    print(f"  SIGNAL SURVIVAL |chi_hw|/|chi_exact| = {abs(chi)/abs(ref):.3f}")

    if meta["shadow"]:
        q_hat, q_sem = ns["estimate_system_observable"](recs, Q)
        q_ref = ns["exact_system_marginal_expectation"](H, psi, Q, meta["t"])
        print(f"\n  <Q> from shadows = {q_hat:+.4f} +- {q_sem:.4f}   exact {q_ref:+.4f}   "
              f"({abs(q_hat-q_ref)/q_sem:.1f} sigma)")
        print(f"  <Q> survival = {q_hat/q_ref:.3f}")
    else:
        print("\n  system observables NOT reported: this job used a single fixed basis, for")
        print("  which the shadow estimator is not unbiased (BUGLOG B04). Re-run with")
        print("  --shadow for a valid <Q>.")

    print("\n  Report robustness claims only. The exact path is shallower purely because")
    print("  n is small (O(4^n) synthesis); that advantage inverts as n grows.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--list", action="store_true", help="list reachable backends + calibration")
    p.add_argument("--submit", action="store_true", help="submit a job")
    p.add_argument("--fetch", metavar="JOB_ID", help="fetch and analyse a finished job")
    p.add_argument("--backend", default=None, help="backend name, e.g. ibm_nighthawk")
    p.add_argument("--model", default="frozen", choices=["frozen", "2site"],
                   help="frozen = graded 3-qubit benchmark; 2site = reduced side model")
    p.add_argument("--shadow", action="store_true",
                   help="balanced 3^n-basis ensemble; REQUIRED for valid system observables")
    p.add_argument("--method", default="exact", choices=["exact", "trotter"],
                   help="exact is far shallower at these sizes (recommended)")
    p.add_argument("--reps", type=int, default=1, help="Trotter repetitions")
    p.add_argument("--shots", type=int, default=2000, help="shots per circuit")
    p.add_argument("--t", type=float, default=0.9, help="evolution time")
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
