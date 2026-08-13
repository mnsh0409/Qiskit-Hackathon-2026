"""Multi-seed Part-B study: writes data/ CSVs per CONVENTIONS §7 and reports
across-seed statistics, so the >=10-seed house rule is met and the bootstrap CIs
of R013 can be checked against real seed-to-seed spread.

Drives the GRADED notebook code itself (nbclient) -- no reimplementation. The
reconstruct/matrix_pencil definitions are lifted programmatically out of the
notebook cell, never hand-copied.
"""
import json
import nbformat
from nbclient import NotebookClient

REPO = "/home/martin/Documents/QiskitHackathon/2026"
NB = f"{REPO}/shadow_hadamard_challenge_PARTICIPANT.ipynb"
N_SEEDS = 12

src = json.load(open(NB, encoding="utf-8"))

# cells 0..47: all definitions incl. run_time_sweep, but NOT cell 48's big sweep
nb = nbformat.v4.new_notebook()
nb.metadata = src.get("metadata", {})
for c in src["cells"][:48]:
    if c["cell_type"] == "code":
        nb.cells.append(nbformat.v4.new_code_cell(source="".join(c["source"])))

# lift the estimator definitions out of cell 70 (id 8c988cf4), dropping its driver tail
cell70 = next("".join(c["source"]) for c in src["cells"] if c.get("id") == "8c988cf4")
marker = "E_HAT, P_HAT, Q_HAT_LABEL, RANK = reconstruct("
assert marker in cell70, "cell 70 driver marker not found -- notebook changed?"
nb.cells.append(nbformat.v4.new_code_cell(source=cell70.split(marker)[0]))

seed_cell = r'''
import csv, os
REPO = "''' + REPO + r'''"
N_SEEDS = ''' + str(N_SEEDS) + r'''
os.makedirs(f"{REPO}/data", exist_ok=True)

print(f"{N_SEEDS} independent full-budget sweeps "
      f"({N_TIMES} times x 2 quadratures x {SHOTS} shots each)\n")

results = []
for k in range(N_SEEDS):
    sk = sub_seed("multiseed", k)
    sw = run_time_sweep(HAM, TS, SHOTS, sk, joint_observables={"Q": CHARGE}, verbose=False)

    # CONVENTIONS §7: header exactly t,re,im ; dt written as the literal 0.2
    for tag, series in (("g1", sw.chi), ("gM", sw.chi_obs["Q"])):
        path = f"{REPO}/data/{tag}_dt{DT:g}_N{N_TIMES}_s{SHOTS}_seed{k}.csv"
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["t", "re", "im"])
            for t, y in zip(TS, series):
                w.writerow([f"{t:.10g}", f"{y.real:.10g}", f"{y.imag:.10g}"])

    e, p, q, r = reconstruct(TS, sw.chi, sw.chi_obs["Q"])
    results.append(dict(seed_index=k, seed=int(sk), E=e, p=p, q=q, rank=int(r)))
    print(f"  seed {k:2d} (={sk}): rank {r}, {len(e)} modes, "
          f"shots {sw.total_shots:,}")

print(f"\nwrote {2*N_SEEDS} CSVs to data/\n")

# ---- across-seed statistics (evaluation side: E_EXACT used only to match/grade) ----
print("Across-seed spectrum statistics (>=10 seeds, house law)\n")
print(f"{'exact E':>9} {'q':>3} | {'seeds':>5} | {'E mean':>9} {'E sd':>7} | "
      f"{'p mean':>8} {'p sd':>7} | {'q mean':>8} {'q sd':>7} | {'lbl ok':>7}")
print("-" * 96)
AGG = []
for e0, q0, p0 in zip(E_EXACT, Q_EXACT_LABELS, P_EXACT):
    Es, ps, qs, oks = [], [], [], []
    for res in results:
        j = int(np.argmin(np.abs(res["E"] - e0)))
        if abs(res["E"][j] - e0) < 0.35:
            Es.append(res["E"][j]); ps.append(res["p"][j]); qs.append(res["q"][j])
            oks.append(int(np.rint(res["q"][j])) == q0)
    if not Es:
        print(f"{e0:+9.4f} {q0:+3d} |     0 | (recovered by no seed)")
        continue
    row = dict(E_exact=float(e0), q_exact=int(q0), p_exact=float(p0), n_seeds=len(Es),
               E_mean=float(np.mean(Es)), E_sd=float(np.std(Es, ddof=1)) if len(Es) > 1 else 0.0,
               p_mean=float(np.mean(ps)), p_sd=float(np.std(ps, ddof=1)) if len(ps) > 1 else 0.0,
               q_mean=float(np.mean(qs)), q_sd=float(np.std(qs, ddof=1)) if len(qs) > 1 else 0.0,
               labels_ok=int(sum(oks)))
    AGG.append(row)
    print(f"{e0:+9.4f} {q0:+3d} | {len(Es):5d} | {row['E_mean']:+9.4f} {row['E_sd']:7.4f} | "
          f"{row['p_mean']:8.4f} {row['p_sd']:7.4f} | {row['q_mean']:+8.3f} {row['q_sd']:7.3f} | "
          f"{sum(oks):3d}/{len(oks):<3d}")

all_ok = sum(1 for res in results
             if all(int(np.rint(res["q"][int(np.argmin(np.abs(res["E"] - e0)))])) == q0
                    for e0, q0 in zip(E_EXACT, Q_EXACT_LABELS)
                    if abs(res["E"][int(np.argmin(np.abs(res["E"] - e0)))] - e0) < 0.35))
print(f"\nseeds where every recovered label rounds correctly: {all_ok}/{N_SEEDS}")

# ---- is the R013 bootstrap honest? compare its sd against real seed-to-seed sd ----
BOOT_E_SD = [0.0053, 0.0053, 0.0014, 0.0167]      # R013, seed 2026
BOOT_Q_SD = [0.052, 0.063, 0.016, 0.187]
print("\nBootstrap sd (R013, single seed) vs across-seed sd (this study):")
print(f"{'exact E':>9} | {'E boot':>8} {'E seeds':>8} {'ratio':>6} | "
      f"{'q boot':>7} {'q seeds':>8} {'ratio':>6}")
print("-" * 72)
for row, be, bq in zip(AGG, BOOT_E_SD, BOOT_Q_SD):
    re_ = row["E_sd"] / be if be else float("nan")
    rq_ = row["q_sd"] / bq if bq else float("nan")
    print(f"{row['E_exact']:+9.4f} | {be:8.4f} {row['E_sd']:8.4f} {re_:6.2f} | "
          f"{bq:7.3f} {row['q_sd']:8.3f} {rq_:6.2f}")
print("\nratio ~1 => the parametric bootstrap is a faithful proxy for seed-to-seed spread;")
print("ratio >1 => the bootstrap UNDERSTATES the real uncertainty.")

with open(f"{REPO}/data/multiseed_summary.json", "w") as fh:
    json.dump(dict(n_seeds=N_SEEDS, shots_per_sweep=int(N_TIMES * 2 * SHOTS),
                   total_shots=int(N_SEEDS * N_TIMES * 2 * SHOTS),
                   seeds=[r["seed"] for r in results],
                   ranks=[r["rank"] for r in results],
                   seeds_all_labels_correct=int(all_ok), rows=AGG), fh, indent=2)
print("\nwrote data/multiseed_summary.json")
'''

nb.cells.append(nbformat.v4.new_code_cell(source=seed_cell))
NotebookClient(nb, timeout=7200, kernel_name="qh26-t5", resources={"metadata": {"path": REPO}}).execute()
nbformat.write(nb, "/tmp/qh26_scratch/executed_seedsweep.ipynb")
print("DONE")
