"""Fetch and analyse the Track-B hardware jobs submitted by track_b_hardware_submit.py.

Four arms, each compared against the exact reference recorded BEFORE submission:
  A  chi_AB(t) from the ancilla alone            -- the GARBAGE baseline (scalar overlap)
  B  <O>_W and <O>_U separately from shadows     -- ours (per-observable profile)
  C  Loschmidt echo P(0..0) = |<psi|W+U|psi>|^2  -- literature baseline, cheaper than ours
  D  Hilbert-Schmidt P(0..0) = |Tr[W+U]/d|^2     -- literature baseline, state-independent
"""
import sys, json
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions, get_model

import numpy as np

ns = load_notebook_definitions()
SPO = ns["SparsePauliOp"]
N2, H2, Q2, PREP2, PSI2, _ = get_model(ns, "2site")
JOBS = json.load(open("/home/martin/Documents/QiskitHackathon/2026/evidence/track_b_hw_jobs.json"))
REF, META, TIMES = JOBS["exact_reference"], JOBS["meta"], JOBS["times"]

OBS = {
    "Z_0":       SPO.from_sparse_list([("Z", [0], 1.0)], num_qubits=N2),
    "Z_1":       SPO.from_sparse_list([("Z", [1], 1.0)], num_qubits=N2),
    "Z_0Z_1":    SPO.from_sparse_list([("ZZ", [0, 1], 1.0)], num_qubits=N2),
    "X0X1+Y0Y1": SPO.from_sparse_list([("XX", [0, 1], 1.0), ("YY", [0, 1], 1.0)],
                                      num_qubits=N2),
    "H":         H2,
    "Q":         Q2,
}
PMAP = {"X": 0, "Y": 1, "Z": 2}


def pauli_hat(label, coeff, basis, s):
    """3^w prod_j s_j 1[b_j = P_j]; identity factors contribute 1. label is Qiskit order
    (rightmost = qubit 0), so index with label[::-1]."""
    lab = label[::-1]
    v, w = 1.0, 0
    for j, ch in enumerate(lab):
        if ch == "I":
            continue
        w += 1
        if basis[j] != PMAP[ch]:
            return 0.0
        v *= s[j]
    return (3 ** w) * v * float(np.real(coeff))


def analyse(backend, job_id):
    from qiskit_ibm_runtime import QiskitRuntimeService
    svc = QiskitRuntimeService()
    job = svc.job(job_id)
    st = str(job.status())
    if "DONE" not in st.upper():
        print(f"  {backend}: job {job_id} status {st} -- not ready")
        return None
    res = job.result()
    out = {"backend": backend, "job_id": job_id, "A": {}, "B": {}, "C": {}, "D": {}}

    for idx, m in enumerate(META):
        d = res[idx].data
        arr = getattr(d, "c", None) or getattr(d, "meas", None)
        bits = arr.get_bitstrings()
        arm, t = m["arm"], str(m["t"])
        if arm in ("C_echo", "D_hst"):
            p0 = sum(1 for b in bits if set(b) == {"0"}) / len(bits)
            out["C" if arm == "C_echo" else "D"][t] = p0
            continue
        # leftmost bit is the highest classical index = ancilla (CONVENTIONS)
        anc = np.array([1 - 2 * int(b[0]) for b in bits], float)
        s = np.array([[1 - 2 * int(c) for c in b[1:][::-1]] for b in bits], float)
        basis = m["basis"]
        if arm == "A":
            out["A"].setdefault(t, {})[m["phi"]] = float(np.mean(anc)) if basis == [2, 2] \
                else out["A"].get(t, {}).get(m["phi"])
            # chi_AB is ancilla-only, so pool over ALL bases rather than one
            key = ("pool", m["phi"])
            out["A"].setdefault(t, {}).setdefault("_pool_" + m["phi"], []).append(
                float(np.mean(anc)))
        else:  # arm B
            for name, o in OBS.items():
                tot_sum = np.zeros(len(bits)); tot_dif = np.zeros(len(bits))
                for lab, co in o.to_list():
                    ph = np.array([pauli_hat(lab, co, basis, s[k]) for k in range(len(bits))])
                    tot_sum += ph; tot_dif += ph * anc
                e = out["B"].setdefault(t, {}).setdefault(name, {"sum": [], "dif": []})
                e["sum"].append(float(np.mean(tot_sum))); e["dif"].append(float(np.mean(tot_dif)))
    return out


def report(out):
    b = out["backend"]
    print("\n" + "=" * 78)
    print(f"{b}  (job {out['job_id']})")
    print("=" * 78)
    print("ARM A -- chi_AB(t) from the ancilla alone [GARBAGE baseline]")
    for t in map(str, TIMES):
        re_ = float(np.mean(out["A"][t]["_pool_re"])); im_ = float(np.mean(out["A"][t]["_pool_im"]))
        ex = complex(*REF[t]["chi_AB"])
        got = complex(re_, im_)
        print(f"   t={float(t):4.1f}  measured {got:+.4f}   exact {ex:+.4f}   "
              f"|.| {abs(got):.4f} vs {abs(ex):.4f}   survival {abs(got)/max(abs(ex),1e-9):.3f}")

    print("\nARM C -- Loschmidt echo, and ARM D -- Hilbert-Schmidt  [literature baselines]")
    for t in map(str, TIMES):
        print(f"   t={float(t):4.1f}  echo {out['C'][t]:.4f} (exact {REF[t]['echo_p0']:.4f})"
              f"    HST {out['D'][t]:.4f} (exact {REF[t]['hst_p0']:.4f})")

    print("\nARM B -- <O>_W and <O>_U SEPARATELY from the shadows  [ours; nothing else does this]")
    for t in map(str, TIMES):
        print(f"   t={float(t):4.1f}")
        for name in OBS:
            e = out["B"][t][name]
            sm, df = float(np.mean(e["sum"])), float(np.mean(e["dif"]))
            w, u = sm + df, sm - df
            ew, eu = REF[t]["obs"][name]["W"], REF[t]["obs"][name]["U"]
            print(f"      {name:<10} W {w:+.3f} (exact {ew:+.3f})   "
                  f"U {u:+.3f} (exact {eu:+.3f})   disagreement {w-u:+.3f} "
                  f"(exact {ew-eu:+.3f})")


results = []
for name, j in JOBS["jobs"].items():
    r = analyse(name, j["job_id"])
    if r:
        report(r); results.append(r)
if results:
    with open("/home/martin/Documents/QiskitHackathon/2026/evidence/track_b_hw_result.json",
              "w") as fh:
        json.dump(results, fh, indent=2)
    print("\nwrote evidence/track_b_hw_result.json")
else:
    print("\nno completed jobs yet -- rerun when they finish")
