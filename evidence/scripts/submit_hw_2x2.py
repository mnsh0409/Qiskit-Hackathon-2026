"""Submit the 3 missing arms of a hardware 2x2: {trotter, exact} x {marrakesh, kingston}.
R008 (trotter + marrakesh) is already in hand, so this completes the grid and lets us
separate DEVICE quality from CIRCUIT DEPTH empirically instead of by model.

Everything else is held fixed to R008: t=0.9, both quadratures, basis [X,Y,Z],
2000 shots/circuit, optimization_level=1, same seed_transpiler.
"""
import json
import nbformat
from nbclient import NotebookClient

REPO = "/home/martin/Documents/QiskitHackathon/2026"
OUT = "/tmp/qh26_scratch"

src = json.load(open(f"{REPO}/shadow_hadamard_challenge_PARTICIPANT.ipynb", encoding="utf-8"))
nb = nbformat.v4.new_notebook()
nb.metadata = src.get("metadata", {})
for c in src["cells"][:23]:            # definitions only -- no sweeps, fast
    if c["cell_type"] == "code":
        nb.cells.append(nbformat.v4.new_code_cell(source="".join(c["source"])))

submit = r'''
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

_service = QiskitRuntimeService()
T_HW, BASIS_HW, SHOTS_HW = 0.9, [0, 1, 2], 2000

# R008 already covers trotter+marrakesh; submit the other three arms
ARMS = [("exact",   "ibm_kingston"),
        ("exact",   "ibm_marrakesh"),
        ("trotter", "ibm_kingston")]

submitted = []
for method, bname in ARMS:
    backend = _service.backend(bname)
    circs = [build_shadow_hadamard_circuit(HAM, T_HW, phi, basis=BASIS_HW,
                                           method=method, reps=1)
             for phi in (PHI_RE, PHI_IM)]
    isa = transpile(circs, backend=backend, optimization_level=1,
                    seed_transpiler=sub_seed("hw-transpile"))
    ops = isa[0].count_ops()
    twoq = sum(v for k, v in ops.items() if k in ("cz", "cx", "ecr"))
    job = SamplerV2(mode=backend).run(isa, shots=SHOTS_HW)
    rec = dict(method=method, backend=bname, job_id=job.job_id(),
               depth=int(isa[0].depth()), two_q=int(twoq),
               status=str(job.status()), pending=int(backend.status().pending_jobs))
    submitted.append(rec)
    print(f"{method:>8} + {bname:14s} : depth {rec['depth']:5d}  2q {twoq:4d}  "
          f"job {rec['job_id']}  ({rec['status']}, {rec['pending']} queued)")

with open("''' + OUT + r'''/hw_2x2_jobs.json", "w") as fh:
    json.dump(submitted, fh, indent=2)
print("\nwrote hw_2x2_jobs.json")
print("\nreference arm already held: trotter + ibm_marrakesh = d9u95vs98n5s7392iao0 "
      "(depth 1729, 435 CZ, damping 0.179)")
'''

nb.cells.append(nbformat.v4.new_code_cell(source=submit))
NotebookClient(nb, timeout=1800, kernel_name="qh26-t5",
               resources={"metadata": {"path": REPO}}).execute()
nbformat.write(nb, f"{OUT}/executed_hw_2x2.ipynb")
print("DONE")
