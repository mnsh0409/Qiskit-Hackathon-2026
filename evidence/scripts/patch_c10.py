import json

path = "/home/martin/Documents/QiskitHackathon/2026/shadow_hadamard_challenge_PARTICIPANT.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

TARGET_ID = "0b7ebb48"

new_source = '''def krylov_lowest_energy(ts, chi, chi_h, m=16, threshold=2e-2):
    """Thresholded real-time Krylov GEVP from measured series only.

    Requires a uniform grid starting at t = 0. Uses chi(-t) = conj(chi(t)).
    """
    if len(ts) < 2:
        raise ValueError("krylov_lowest_energy needs at least two time points")
    dt = ts[1] - ts[0]
    if not np.isclose(ts[0], 0.0) or not np.allclose(np.diff(ts), dt):
        raise ValueError("krylov_lowest_energy requires a uniform grid starting at t = 0")
    if m > len(ts):
        raise ValueError(f"m={m} exceeds the number of available time points ({len(ts)})")

    def series(y, k):
        return y[k] if k >= 0 else np.conj(y[-k])

    S = np.array([[series(chi, k - j) for k in range(m)] for j in range(m)])
    H = np.array([[series(chi_h, k - j) for k in range(m)] for j in range(m)])
    S = 0.5 * (S + S.conj().T)
    H = 0.5 * (H + H.conj().T)

    evals, evecs = np.linalg.eigh(S)              # canonical orthogonalisation
    keep = evals > threshold * evals.max()
    proj = evecs[:, keep] / np.sqrt(evals[keep])

    H_red = proj.conj().T @ H @ proj
    E0 = float(np.linalg.eigvalsh(H_red)[0])       # eigvalsh, not eigvals: real by construction
    return E0, int(np.sum(keep))


E0_EXACT_POPULATED = float(E_EXACT[0])
E0_KRYLOV, KEPT = krylov_lowest_energy(TS, CHI, CHI_H, m=min(16, N_TIMES), threshold=2e-2)
print(f"Krylov GEVP (m = {min(16, N_TIMES)}, threshold = 0.02, {KEPT} vectors kept)")
print(f"  estimate          {E0_KRYLOV:+.4f}")
print(f"  lowest populated  {E0_EXACT_POPULATED:+.4f}   (error {abs(E0_KRYLOV - E0_EXACT_POPULATED):.4f})")
print(f"  global ground     {float(np.min(SPEC.energies)):+.4f}   <-- unpopulated, invisible here")
print(f"  matrix-pencil     {float(E_HAT[0]):+.4f}   (the §7 pipeline, for comparison)")'''

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
