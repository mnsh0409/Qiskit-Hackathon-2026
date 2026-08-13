import json

path = "/home/martin/Documents/QiskitHackathon/2026/shadow_hadamard_challenge_PARTICIPANT.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

TARGET_ID = "8c988cf4"

new_source = '''def matrix_pencil(y: np.ndarray, dt: float, n_modes: int | None = None,
                  sv_threshold: float = 0.06):
    """Frequencies E_k of  y_j = sum_k A_k exp(-i E_k t_j)  on a uniform grid.

    Returns (energies, rank).  If n_modes is None the rank is chosen as the number of
    singular values above `sv_threshold` times the largest one.
    """
    n = len(y)
    ell = n // 2
    H = hankel(y[: ell + 1], y[ell:])      # shape (ell+1, n-ell)
    Y0, Y1 = H[:-1, :], H[1:, :]           # the pencil pair

    U, S, Vh = svd(Y0, full_matrices=False)
    r = n_modes if n_modes is not None else int(np.sum(S > sv_threshold * S[0]))
    Ur, Sr, Vr = U[:, :r], S[:r], Vh[:r, :].conj().T

    A = (Ur.conj().T @ Y1 @ Vr) @ np.diag(1.0 / Sr)
    z = eigvals(A)
    energies = -np.angle(z) / dt           # z_k = exp(-i E_k dt)  ->  E_k = -arg(z_k)/dt
    return energies, r


def amplitudes_at(energies: np.ndarray, ts: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Least-squares A_k in  y(t) = sum_k A_k exp(-i E_k t)  at FIXED energies."""
    vand = np.exp(-1j * np.outer(ts, energies))
    return lstsq(vand, y)[0]


def reconstruct(ts, chi, chi_q, n_modes=None, weight_threshold=0.02):
    """Full Track-A pipeline -> (energies, weights p_k, labels q_k, rank), sorted by energy.

    Uses ONLY the measured series.  No exact diagonalisation anywhere.
    """
    dt = ts[1] - ts[0]
    energies, rank = matrix_pencil(chi, dt, n_modes=n_modes)
    amps = amplitudes_at(energies, ts, chi)

    keep = np.abs(amps) > weight_threshold
    energies, amps = energies[keep], amps[keep]

    amps_q = amplitudes_at(energies, ts, chi_q)          # SAME frequencies, second series

    order = np.argsort(energies)
    energies = energies[order]
    p_k = np.real(amps[order])
    q_hat = np.real(amps_q[order] / amps[order])
    return energies, p_k, q_hat, rank


E_HAT, P_HAT, Q_HAT_LABEL, RANK = reconstruct(TS, CHI, CHI_Q)
print(f"matrix-pencil rank chosen automatically: {RANK}")
print(f"modes surviving the weight threshold   : {len(E_HAT)}\\n")
for e, p, q in zip(E_HAT, P_HAT, Q_HAT_LABEL):
    print(f"   E = {e:+8.4f}    p = {p:7.4f}    q_hat = {q:+7.3f}  ->  q = {int(np.rint(q)):+d}")'''

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
