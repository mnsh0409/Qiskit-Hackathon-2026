"""Process the real_machine/*.json files -- results from a teammate's independent hardware
run, using OUR OWN hardware_run.py/layout_search.py tools from a different IBM account
(their own account reaches ibm_miami, a device this account cannot see).

These are raw qiskit_ibm_runtime job dumps (job_id/backend/status/inputs/result/metrics),
decoded here with the standard RuntimeDecoder and run through the SAME graded
parse_memory / estimate_hadamard_signal code every other hardware result in this project
uses -- not a new analysis path, no reimplemented physics. This is the offline equivalent
of `hardware_run.py --fetch`, adapted to read a saved JSON dump instead of a live API call
(the teammate ran on their own account/token, which this account cannot query directly).

All 6 jobs are fixed-basis submissions (per BUGLOG B04, chi only -- no <Q> claims here).
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions, get_model

import json
import numpy as np
from qiskit_ibm_runtime.json import RuntimeDecoder

ns = load_notebook_definitions()

FILES = [
    ("ibm_kingston_frozen_result.json", "frozen"),
    ("ibm_kingston_2site_result.json", "2site"),
    ("ibm_kingston_4site_result.json", "4site"),
    ("ibm_miami_frozen_result.json", "frozen"),
    ("ibm_miami_2site_result.json", "2site"),
    ("ibm_miami_4site_result.json", "4site"),
]

T = 0.9   # every job in real_machine/log.txt was submitted with hardware_run.py's default -t
rows = []

print(f"{'file':>32} {'backend':>14} {'model':>8} | {'survival':>9} {'dev_re':>7} {'dev_im':>7}")
print("-" * 90)

for fname, model in FILES:
    path = f"/home/martin/Documents/QiskitHackathon/2026/real_machine/{fname}"
    d = json.load(open(path, encoding="utf-8"))
    n, H, Q, prep, psi, label = get_model(ns, model)

    result = json.loads(json.dumps(d["result"]), cls=RuntimeDecoder)
    bits_re = result[0].data.c.get_bitstrings()
    bits_im = result[1].data.c.get_bitstrings()

    outc_re, anc_re = ns["parse_memory"](bits_re, n)
    outc_im, anc_im = ns["parse_memory"](bits_im, n)
    rec_re = ns["ShadowRecords"](t=T, phi=ns["PHI_RE"], bases=np.tile([0, 1, 2][:n], (len(anc_re), 1)),
                                 outcomes=outc_re, ancilla=anc_re, n_circuits=1)
    rec_im = ns["ShadowRecords"](t=T, phi=ns["PHI_IM"], bases=np.tile([0, 1, 2][:n], (len(anc_im), 1)),
                                 outcomes=outc_im, ancilla=anc_im, n_circuits=1)

    chi_hw, s_re, s_im = ns["estimate_hadamard_signal"](rec_re, rec_im)
    chi_ref = ns["exact_chi"](H, psi, [T])[0]
    survival = abs(chi_hw) / abs(chi_ref)
    dev_re = abs(chi_hw.real - chi_ref.real) / s_re
    dev_im = abs(chi_hw.imag - chi_ref.imag) / s_im

    print(f"{fname:>32} {d['backend']:>14} {model:>8} | {survival:>9.3f} {dev_re:>7.1f} {dev_im:>7.1f}")
    rows.append(dict(file=fname, job_id=d["job_id"], backend=d["backend"], model=model,
                     n_shots=len(bits_re), chi_hw_re=float(chi_hw.real), chi_hw_im=float(chi_hw.imag),
                     sem_re=float(s_re), sem_im=float(s_im), chi_exact_re=float(chi_ref.real),
                     chi_exact_im=float(chi_ref.imag), survival=float(survival),
                     dev_re_sigma=float(dev_re), dev_im_sigma=float(dev_im)))

with open("/home/martin/Documents/QiskitHackathon/2026/evidence/real_machine_analysis.json", "w") as fh:
    json.dump(rows, fh, indent=2)
print("\nwrote evidence/real_machine_analysis.json")

# cross-check: does our OWN 4site+kingston job (same model, same searched layout,
# different job submission) land in a similar place to the teammate's independent run?
print("\ncross-check against our own 4site+kingston result (R026, different job, same layout):")
own = next(r for r in rows if r["model"] == "4site" and r["backend"] == "ibm_kingston")
print(f"  teammate's independent run: survival {own['survival']:.3f}")
print(f"  (compare with our own job d9ultm0u5hac73ahd9kg once it returns)")
