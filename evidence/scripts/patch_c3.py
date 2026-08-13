import json

path = "/home/martin/Documents/QiskitHackathon/2026/shadow_hadamard_challenge_PARTICIPANT.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

TARGET_ID = "3d3c4ae7"

new_source = '''@dataclass
class ShadowRecords:
    """Every shot of one (t, phi) setting. This schema is the contract for all estimators."""
    t: float
    phi: float
    bases: np.ndarray      # (N, n) ints, 0 = X, 1 = Y, 2 = Z
    outcomes: np.ndarray   # (N, n) +-1 eigenvalue outcomes of the system qubits
    ancilla: np.ndarray    # (N,)   +-1 ancilla outcome  a
    n_circuits: int = 0

    @property
    def n_shots(self) -> int:
        return len(self.ancilla)


def parse_memory(memory: Iterable[str], n: int):
    """Bitstrings -> (+-1 system outcomes (N, n), +-1 ancilla outcomes (N,)).

    Memory string layout (leftmost = highest classical bit):  c[n] c[n-1] ... c[1] c[0]
    so character 0 is the ancilla and character (n - j) is system qubit j.
    """
    signs = np.array([[1 if ch == "0" else -1 for ch in row] for row in memory])
    ancilla = signs[:, 0]
    outcomes = signs[:, 1:][:, ::-1]      # reverse: char (n-j) -> position j (endianness rule #2)
    return outcomes, ancilla


def run_shadow_hadamard(ham, t, phi, n_shots, seed, prep=None,
                        method="exact", reps=2, backend=None) -> ShadowRecords:
    """One (t, phi) setting with per-shot uniformly random local Pauli bases."""
    backend = backend if backend is not None else AerSimulator()
    n = ham.num_qubits

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, 3, size=(n_shots, n))
    uniq_bases, counts = np.unique(draws, axis=0, return_counts=True)

    circuits = [build_shadow_hadamard_circuit(ham, t, phi, list(b), prep=prep,
                                               method=method, reps=reps)
                for b in uniq_bases]
    circuits = transpile(circuits, backend)

    shots = int(counts.max())
    result = backend.run(circuits, shots=shots, memory=True, seed_simulator=seed).result()

    bases_chunks, outcomes_chunks, ancilla_chunks = [], [], []
    for i, (basis_row, c) in enumerate(zip(uniq_bases, counts)):
        mem = result.get_memory(i)[:c]                     # truncate to this basis' own count
        outc, anc = parse_memory(mem, n)
        bases_chunks.append(np.tile(basis_row, (c, 1)))
        outcomes_chunks.append(outc)
        ancilla_chunks.append(anc)

    return ShadowRecords(
        t=t, phi=phi,
        bases=np.concatenate(bases_chunks, axis=0),
        outcomes=np.concatenate(outcomes_chunks, axis=0),
        ancilla=np.concatenate(ancilla_chunks, axis=0),
        n_circuits=len(circuits),
    )'''

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
