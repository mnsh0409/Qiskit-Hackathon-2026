import json

path = "/home/martin/Documents/QiskitHackathon/2026/shadow_hadamard_challenge_PARTICIPANT.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

TARGET_ID = "3198052a"

new_source = '''def pauli_terms(obs: SparsePauliOp):
    """Yield (support {qubit: code}, real coefficient) for each Pauli term of `obs`."""
    for label, coeff in obs.simplify().to_list():
        support = {q: PAULI_CODES[ch] for q, ch in enumerate(label[::-1]) if ch != "I"}
        yield support, np.real_if_close(coeff)


def pauli_snapshot_values(records: ShadowRecords, support: Mapping[int, int]) -> np.ndarray:
    """Per-shot local-shadow estimates  hat{P}_s  of ONE Pauli string.

        hat{P} = 3^w * prod_{j in supp} s_j * 1[b_j == P_j]        (identity -> all ones)
    """
    if not support:
        return np.ones(records.n_shots)
    qubits = list(support.keys())
    codes = np.array([support[q] for q in qubits])
    match = np.all(records.bases[:, qubits] == codes, axis=1)
    prod = np.prod(records.outcomes[:, qubits], axis=1)
    return (3.0 ** len(support)) * prod * match


def _check_quadrature_pair(rec_re: ShadowRecords, rec_im: ShadowRecords) -> None:
    """Guard against swapped or mismatched quadrature records -- a silent-nonsense trap."""
    if not np.isclose(rec_re.phi, PHI_RE) or not np.isclose(rec_im.phi, PHI_IM):
        raise ValueError(f"expected (phi=0, phi=-pi/2), got ({rec_re.phi}, {rec_im.phi})")
    if not np.isclose(rec_re.t, rec_im.t):
        raise ValueError(f"quadrature records at different t: {rec_re.t} vs {rec_im.t}")


# ---------------------------------------------------------------------- 1) ancilla only
def estimate_hadamard_signal(rec_re: ShadowRecords, rec_im: ShadowRecords):
    """chi(t) = Tr[U(t) rho] from the ancilla marginal.  Returns (chi, sem_re, sem_im)."""
    _check_quadrature_pair(rec_re, rec_im)
    re, im = np.mean(rec_re.ancilla), np.mean(rec_im.ancilla)
    sem_re = np.std(rec_re.ancilla, ddof=1) / np.sqrt(rec_re.n_shots)
    sem_im = np.std(rec_im.ancilla, ddof=1) / np.sqrt(rec_im.n_shots)
    return re + 1j * im, float(sem_re), float(sem_im)


# ------------------------------------------------------- 2) unweighted shadows  ->  rho^(I)
def estimate_system_observable(records_list: Sequence[ShadowRecords], obs: SparsePauliOp):
    """<O> under rho^(I), pooling every record set given.  Returns (estimate, sem)."""
    per_shot = []
    for records in records_list:
        total = np.zeros(records.n_shots)
        for support, coeff in pauli_terms(obs):
            total = total + coeff * pauli_snapshot_values(records, support)
        per_shot.append(total)
    pooled = np.concatenate(per_shot)
    return float(np.mean(pooled)), float(np.std(pooled, ddof=1) / np.sqrt(len(pooled)))


# ------------------------------------------- 3) ancilla-weighted shadows  ->  chi_O(t)
def estimate_joint_observable(rec_re: ShadowRecords, rec_im: ShadowRecords, obs: SparsePauliOp):
    """chi_O(t) = Tr[O U(t) rho] from a-weighted shadows.  Returns (chi_O, sem_re, sem_im)."""
    _check_quadrature_pair(rec_re, rec_im)

    def a_weighted(records: ShadowRecords) -> np.ndarray:
        total = np.zeros(records.n_shots)
        for support, coeff in pauli_terms(obs):
            total = total + coeff * pauli_snapshot_values(records, support)
        return total * records.ancilla

    vals_re, vals_im = a_weighted(rec_re), a_weighted(rec_im)
    re, im = np.mean(vals_re), np.mean(vals_im)
    sem_re = np.std(vals_re, ddof=1) / np.sqrt(rec_re.n_shots)
    sem_im = np.std(vals_im, ddof=1) / np.sqrt(rec_im.n_shots)
    return re + 1j * im, float(sem_re), float(sem_im)'''

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
