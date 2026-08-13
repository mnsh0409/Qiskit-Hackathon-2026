import json

path = "/home/martin/Documents/QiskitHackathon/2026/shadow_hadamard_challenge_PARTICIPANT.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

TARGET_ID = "5aaa97f0"

new_source = '''def bootstrap_uncertainties(ts, chi, chi_q, sem, sem_q, n_modes, ref_energies,
                            n_boot=200, seed=0, match_radius=0.35):
    """Parametric bootstrap of the Track-A pipeline. Returns (E_sd, p_sd, q_sd).

    Each is an array of length len(ref_energies), aligned with the point-estimate modes:
    entry k is the spread of the replicate peak matched to ref_energies[k]. The given code
    indexes these with point-estimate indices, so the length must not depend on how many
    peaks an individual replicate happened to find.
    """
    rng = np.random.default_rng(seed)
    n_ref = len(ref_energies)
    e_reps = np.full((n_boot, n_ref), np.nan)
    p_reps = np.full((n_boot, n_ref), np.nan)
    q_reps = np.full((n_boot, n_ref), np.nan)

    for b in range(n_boot):
        chi_b = chi + rng.normal(scale=sem[:, 0]) + 1j * rng.normal(scale=sem[:, 1])
        chi_q_b = chi_q + rng.normal(scale=sem_q[:, 0]) + 1j * rng.normal(scale=sem_q[:, 1])
        try:
            e_b, p_b, q_b, _ = reconstruct(ts, chi_b, chi_q_b, n_modes=n_modes)
        except Exception:
            continue                                     # an occasional replicate may not converge
        for k, e_ref in enumerate(ref_energies):
            j = int(np.argmin(np.abs(e_b - e_ref)))
            if abs(e_b[j] - e_ref) < match_radius:
                e_reps[b, k], p_reps[b, k], q_reps[b, k] = e_b[j], p_b[j], q_b[j]

    return (np.nanstd(e_reps, axis=0), np.nanstd(p_reps, axis=0), np.nanstd(q_reps, axis=0))


_t0 = time.time()
E_SD, P_SD, Q_SD = bootstrap_uncertainties(
    TS, CHI, CHI_Q, SWEEP.chi_sem, SWEEP.chi_obs_sem["Q"],
    n_modes=RANK, ref_energies=E_HAT, n_boot=200, seed=sub_seed("bootstrap"))
print(f"200 bootstrap replicates in {time.time() - _t0:.1f} s")'''

found = False
for cell in nb["cells"]:
    if cell.get("id") == TARGET_ID:
        assert cell["cell_type"] == "code"
        old_source = "".join(cell["source"])
        assert "raise NotImplementedError" in old_source, "unexpected cell content, aborting"
        cell["source"] = new_source.splitlines(keepends=True)
        found = True
        break

assert found, "target cell id not found"

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")

print("patched cell", TARGET_ID)
