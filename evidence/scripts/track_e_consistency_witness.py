"""Track E (own proposal): ancilla-vs-system consistency as a SELF-VALIDATING decoherence
witness, plus product-state fidelity from the same records.

THE IDENTITY (notebook §7.5 states it; we exploit it as a witness). For a PURE input state,
exactly:

        Tr[(rho^(I))^2]  =  (1 + |chi(t)|^2) / 2

  LHS  measurable from the SYSTEM register alone (shadow snapshot pairs)
  RHS  measurable from the ANCILLA alone

Two INDEPENDENT measurement channels of the same experiment. On ideal hardware they agree
exactly; under decoherence they diverge. The GAP therefore certifies decoherence with NO
exact reference and NO classical simulation -- i.e. it still works at sizes where nothing
can be verified classically. That is the point: every other check in this project compares
against exact diagonalisation, which does not scale. This one does not need it.

Sign expectation (derived, not assumed): under global depolarising with parameter p,
LHS -> p^2(1+|chi|^2)/2 + 2p(1-p)/d + (1-p)^2/d  while  RHS -> (1 + p^2|chi|^2)/2.
At p=1 they coincide; at p->0, LHS->1/d and RHS->1/2, so for d>2 the GAP GOES NEGATIVE.
Measured purity falling BELOW the ancilla's prediction is the decoherence signature.

PURITY FROM SHADOW PAIRS (standard HKP): for two independent snapshots,
Tr[rho_hat_1 rho_hat_2] = prod_j Tr[(3P_1j - I)(3P_2j - I)], and per qubit that equals
  same basis & same outcome -> 9*1 - 4 = +5
  same basis & diff outcome -> 9*0 - 4 = -4
  different bases           -> 9*(1/2) - 4 = +0.5
Averaging over distinct pairs is an unbiased U-statistic for Tr[rho^2].

DEBIASING (matters, easy to get wrong): |chi|^2 from finite samples is BIASED UPWARD, since
E[mean(a)^2] = mean^2 + Var(mean). We subtract the sem^2 on each quadrature so the RHS is an
unbiased estimate of the true |chi|^2, otherwise the witness would report a spurious gap even
on a perfect simulator.

rho^(I) is provably phi-independent (Checkpoint 3b), so both quadratures are pooled here --
legitimate per the notebook's own pooling rules, and it doubles the statistics.
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions, get_model

import itertools
import json
import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator

ns = load_notebook_definitions()
T = 0.9
RNG = np.random.default_rng(2026)
N_PAIRS = 400_000


def _purity_pairs(bases, outs, n_pairs, rng):
    m = len(bases)
    i = rng.integers(0, m, size=n_pairs)
    j = rng.integers(0, m, size=n_pairs)
    ok = i != j                     # distinct snapshots only
    i, j = i[ok], j[ok]
    same_basis = bases[i] == bases[j]
    same_out = outs[i] == outs[j]
    per_qubit = np.where(same_basis, np.where(same_out, 5.0, -4.0), 0.5)
    return float(np.mean(np.prod(per_qubit, axis=1)))


def purity_from_records(records_list, n_blocks=20, pairs_per_block=40_000, rng=RNG):
    """Unbiased Tr[rho^2] from shadow snapshot pairs, with a HONEST error bar.

    METHOD NOTE (this was a real bug, caught because the ideal simulator -- where the
    identity holds exactly -- reported a suspicious -2.2 sigma gap): the naive
    std(pair_values)/sqrt(n_pairs) badly UNDERSTATES the uncertainty, because pairs are not
    independent -- every shot appears in many pairs, so the effective sample size is set by
    the NUMBER OF SHOTS, not the number of pairs drawn. Fixed by splitting the shots into
    disjoint blocks, estimating within each block independently, and taking the spread
    ACROSS blocks. Shots are shuffled first: they arrive grouped by basis, so contiguous
    blocks would each contain a single basis and the estimator would be meaningless.

    rho^(I) is phi-independent (Checkpoint 3b) so both quadratures are pooled.
    """
    bases = np.concatenate([r.bases for r in records_list])
    outs = np.concatenate([r.outcomes for r in records_list])
    perm = rng.permutation(len(bases))          # MUST shuffle: records are basis-grouped
    bases, outs = bases[perm], outs[perm]
    bs = len(bases) // n_blocks
    ests = [_purity_pairs(bases[k * bs:(k + 1) * bs], outs[k * bs:(k + 1) * bs],
                          pairs_per_block, rng) for k in range(n_blocks)]
    return float(np.mean(ests)), float(np.std(ests, ddof=1) / np.sqrt(n_blocks))


def chi_sq_debiased(rec_re, rec_im):
    """|chi|^2 with the finite-sample upward bias removed."""
    re, im = float(np.mean(rec_re.ancilla)), float(np.mean(rec_im.ancilla))
    sem_re = float(np.std(rec_re.ancilla, ddof=1) / np.sqrt(rec_re.n_shots))
    sem_im = float(np.std(rec_im.ancilla, ddof=1) / np.sqrt(rec_im.n_shots))
    val = (re ** 2 - sem_re ** 2) + (im ** 2 - sem_im ** 2)
    # propagate: Var[re^2] ~ (2*re*sem_re)^2
    sem = float(np.sqrt((2 * re * sem_re) ** 2 + (2 * im * sem_im) ** 2))
    return val, sem


def projector_onto_zeros(n):
    """|0..0><0..0| = prod_j (I + Z_j)/2, expanded into 2^n Pauli strings."""
    SPO = ns["SparsePauliOp"]
    terms = []
    for support in itertools.chain.from_iterable(
            itertools.combinations(range(n), k) for k in range(n + 1)):
        if support:
            terms.append(("Z" * len(support), list(support), 1.0 / 2 ** n))
        else:
            terms.append(("I", [0], 1.0 / 2 ** n))
    return SPO.from_sparse_list(terms, num_qubits=n).simplify()


def ideal_shadow_records(model, t=T, shots_per_basis=4000, seed0=71, backend=None):
    """Full balanced shadow ensemble. backend=None -> ideal; pass a noisy AerSimulator to
    exercise the witness where decoherence is genuinely present."""
    n, H, Q, prep, psi, label = get_model(ns, model)
    bases = list(itertools.product(range(3), repeat=n))
    backend = backend if backend is not None else AerSimulator()
    recs = []
    for phi, sd in ((ns["PHI_RE"], seed0), (ns["PHI_IM"], seed0 + 1)):
        circs = [ns["build_shadow_hadamard_circuit"](H, t, phi, basis=list(b), prep=prep,
                                                      method="exact") for b in bases]
        res = backend.run(transpile(circs, backend), shots=shots_per_basis, memory=True,
                          seed_simulator=sd).result()
        B, O, A = [], [], []
        for k, b in enumerate(bases):
            outc, anc = ns["parse_memory"](res.get_memory(k), n)
            B.append(np.tile(b, (len(anc), 1))); O.append(outc); A.append(anc)
        recs.append(ns["ShadowRecords"](t=t, phi=phi, bases=np.concatenate(B),
                                        outcomes=np.concatenate(O), ancilla=np.concatenate(A),
                                        n_circuits=len(bases)))
    return n, H, psi, recs


def report(tag, n, recs, psi, H):
    pur, pur_sem = purity_from_records(recs)
    cs, cs_sem = chi_sq_debiased(recs[0], recs[1])
    rhs = (1 + cs) / 2
    rhs_sem = cs_sem / 2
    gap = pur - rhs
    gap_sem = float(np.sqrt(pur_sem ** 2 + rhs_sem ** 2))
    z = gap / gap_sem if gap_sem > 0 else float("nan")

    proj = projector_onto_zeros(n)
    fid, fid_sem = ns["estimate_system_observable"](recs, proj)
    fid_exact = ns["exact_system_marginal_expectation"](H, psi, proj, T)

    print(f"\n--- {tag} ---")
    print(f"  LHS Tr[(rho^I)^2] from SHADOWS  = {pur:.4f} +- {pur_sem:.4f}")
    print(f"  RHS (1+|chi|^2)/2 from ANCILLA  = {rhs:.4f} +- {rhs_sem:.4f}")
    print(f"  GAP (LHS - RHS)                 = {gap:+.4f} +- {gap_sem:.4f}   ({z:+.1f} sigma)")
    print(f"  fidelity <|0..0><0..0|> shadows = {fid:.4f} +- {fid_sem:.4f}  "
          f"(exact {fid_exact:.4f}, {abs(fid-fid_exact)/fid_sem:.1f} sigma)")
    return dict(tag=tag, purity=pur, purity_sem=pur_sem, rhs=rhs, rhs_sem=rhs_sem,
                gap=gap, gap_sem=gap_sem, gap_sigma=float(z),
                fidelity=float(fid), fidelity_sem=float(fid_sem),
                fidelity_exact=float(fid_exact))


ROWS = []
print("=" * 78)
print("(1) IDEAL SIMULATOR -- does the identity hold? (validates the estimator itself)")
print("=" * 78)
for model in ("2site", "frozen"):
    n, H, psi, recs = ideal_shadow_records(model)
    ROWS.append(report(f"ideal sim, {model} (n={n})", n, recs, psi, H))

print("\n" + "=" * 78)
print("(2) NOISY SIMULATOR -- does the witness actually FIRE when decoherence is present?")
print("     (the control leg: without this, a null result on clean hardware is uninformative)")
print("=" * 78)
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

def toy_noise(p1=3e-4, p2=6e-3, p_ro=1.2e-2):
    """Same parameters as the notebook's own Challenge 11 noise model."""
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["rz", "sx", "x", "h", "s", "sdg"])
    nm.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cx"])
    nm.add_all_qubit_readout_error(ReadoutError([[1 - p_ro, p_ro], [p_ro, 1 - p_ro]]))
    return nm

for mult, tag in ((1, "1x"), (5, "5x")):
    nb_ = AerSimulator(noise_model=toy_noise(p1=3e-4 * mult, p2=6e-3 * mult,
                                             p_ro=1.2e-2 * mult))
    n, H, psi, recs = ideal_shadow_records("2site", seed0=91 + mult, backend=nb_)
    ROWS.append(report(f"NOISY sim {tag} (toy depolarising+readout), 2site", n, recs, psi, H))

print("\n" + "=" * 78)
print("(3) REAL HARDWARE -- the witness applied to actual QPU data (no exact ref needed)")
print("=" * 78)
from qiskit_ibm_runtime import QiskitRuntimeService

JOB_ID = "d9uk99k98n5s7392vhsg"          # our own 2site balanced shadow ensemble, R023
db = json.load(open("/home/martin/Documents/QiskitHackathon/2026/hardware_jobs.json"))
meta = db[JOB_ID]
n, H, Q, prep, psi, label = get_model(ns, meta["model"])
svc = QiskitRuntimeService()
res = svc.job(JOB_ID).result()
phis = [ns["PHI_RE"], ns["PHI_IM"]]
acc = {0: dict(b=[], o=[], a=[]), 1: dict(b=[], o=[], a=[])}
for idx, (pi, basis) in enumerate(meta["plan"]):
    outc, anc = ns["parse_memory"](res[idx].data.c.get_bitstrings(), n)
    acc[pi]["b"].append(np.tile(basis, (len(anc), 1)))
    acc[pi]["o"].append(outc); acc[pi]["a"].append(anc)
hw_recs = [ns["ShadowRecords"](t=meta["t"], phi=phis[pi],
                               bases=np.concatenate(acc[pi]["b"]),
                               outcomes=np.concatenate(acc[pi]["o"]),
                               ancilla=np.concatenate(acc[pi]["a"]),
                               n_circuits=len(acc[pi]["b"])) for pi in (0, 1)]
ROWS.append(report(f"REAL HARDWARE ibm_kingston, 2site (job {JOB_ID})", n, hw_recs, psi, H))

print("\ninterpretation: a NEGATIVE gap means measured purity fell below what the ancilla")
print("predicts -- the decoherence signature derived in this file's header. Crucially this")
print("comparison used no exact diagonalisation at all, so it remains available at sizes")
print("where classical verification is impossible.")

with open("/home/martin/Documents/QiskitHackathon/2026/evidence/track_e_result.json", "w") as fh:
    json.dump(ROWS, fh, indent=2)
print("\nwrote evidence/track_e_result.json")
