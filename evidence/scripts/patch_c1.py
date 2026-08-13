import json

path = "/home/martin/Documents/QiskitHackathon/2026/shadow_hadamard_challenge_PARTICIPANT.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

TARGET_ID = "70a3c675"

new_source = '''def build_controlled_evolution(ham: SparsePauliOp, t: float,
                               method: str = "exact", reps: int = 2) -> Gate:
    """Controlled-U(t) whose FIRST qubit is the ancilla control.

    method="exact"   : the block unitary |0><0| (x) I + |1><1| (x) e^{-iHt}, built numerically.
                       Simulator-only, zero Trotter error -- use this for validation.
    method="trotter" : synthesise the 2nd-order Suzuki-Trotter product formula FIRST, then
                       control the whole synthesised circuit.  Hardware-realistic.

    Append with:  qc.append(gate, [ancilla, sys_0, ..., sys_{n-1}]).
    """
    n = ham.num_qubits

    if method == "exact":
        from scipy.linalg import expm
        u = expm(-1j * ham.to_matrix() * t)
        d = 2 ** n
        p0, p1 = np.diag([1.0, 0.0]), np.diag([0.0, 1.0])
        # qargs = [anc, s0, ..., s_{n-1}] -> ancilla is the LOWEST matrix bit
        cu = np.kron(np.eye(d), p0) + np.kron(u, p1)
        return UnitaryGate(cu, label=f"c-U(exact,t={t:.3g})")

    elif method == "trotter":
        evo = PauliEvolutionGate(ham, time=t, synthesis=SuzukiTrotter(order=2, reps=reps))
        uncontrolled = QuantumCircuit(n)
        uncontrolled.append(evo, range(n))
        uncontrolled = transpile(uncontrolled, basis_gates=["rz", "sx", "x", "cx"],
                                 optimization_level=1, seed_transpiler=0)
        # synthesise FIRST, control SECOND -- controlling the already-synthesised circuit
        # keeps the ancilla branch |0><0|(x)I + |1><1|(x)U_trot exact.
        return uncontrolled.to_gate(label=f"cU_trot(t={t:.3g},r={reps})").control(1)

    else:
        raise ValueError(f"unknown method {method!r}")'''

found = False
for cell in nb["cells"]:
    if cell.get("id") == TARGET_ID:
        assert cell["cell_type"] == "code"
        old_source = "".join(cell["source"])
        assert "raise NotImplementedError" in old_source, "unexpected cell content, aborting"
        lines = new_source.splitlines(keepends=True)
        cell["source"] = lines
        found = True
        break

assert found, "target cell id not found"

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")

print("patched cell", TARGET_ID)
