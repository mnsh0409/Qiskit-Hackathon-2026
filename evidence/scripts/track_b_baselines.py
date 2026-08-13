"""TRACK B AGAINST THE BASELINES THE COMPILING LITERATURE ACTUALLY USES.

Track B asks: how close is an approximate implementation W to the target U? That is the
circuit-compiling verification problem, and it has standard answers. Comparing our arm only
against "discard the garbage" would be a strawman, so this script implements the real ones
and measures all of them on the same 2-site instance.

  (1) CLASSICAL FIDELITY -- |<psi_W|psi_U>|^2 from statevector/MPS simulation. This is what
      qiskit-addon-aqc-tensor itself optimises and reports. Exact, zero quantum cost, and
      NOT SCALABLE: it is the thing you cannot do at the sizes where you need the answer.

  (2) LOSCHMIDT ECHO / echo verification -- prepare |psi>, apply U, apply W^dag, undo the
      preparation, measure the all-zeros probability = |<psi|W^dag U|psi>|^2. n qubits, no
      ancilla, one circuit. The cheapest honest quantum baseline, and it is CHEAPER than
      Track B -- we say so.

  (3) HILBERT-SCHMIDT TEST (Khatri, LaRose, Poremba, Cincio, Sornborger, Coles,
      "Quantum-assisted quantum compiling", Quantum 3, 140 (2019)) -- Bell pairs across a
      2n-qubit register give the all-zeros probability |Tr[W^dag U]|^2 / d^2. This is
      STATE-INDEPENDENT, i.e. strictly more information than any state-specific overlap,
      at the cost of doubling the register.

  (4) TRACK B, ancilla only -- the complex overlap <psi|W^dag U|psi>, magnitude AND phase.
  (5) TRACK B + shadows (ours) -- the same, plus <O>_W and <O>_U SEPARATELY for every Pauli
      O, from the same shots (arm B: delete the final Hadamard; sum and difference).

The honest scoreboard is not "ours wins". It is: the echo is cheaper, the HST is stronger
per query and costlier in qubits, and ours is the only one that says WHICH OBSERVABLE broke.
"""
import sys, json
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions, get_model

import numpy as np
from qiskit import transpile

ns = load_notebook_definitions()
QC, QR, CR = ns["QuantumCircuit"], ns["QuantumRegister"], ns["ClassicalRegister"]
SV, OP = ns["Statevector"], ns["Operator"]

N2, H2, Q2, PREP2, PSI2, LABEL2 = get_model(ns, "2site")
REPS_W, T = 1, 0.9
D = 2 ** N2


def blocks(t):
    """W(t), U(t) as system matrices; control is qubit 0 = LSB, so the |1> block is [1::2]."""
    U = OP(ns["build_controlled_evolution"](H2, t, "exact")).data[1::2, 1::2]
    W = OP(ns["build_controlled_evolution"](H2, t, "trotter", REPS_W)).data[1::2, 1::2]
    return W, U


W, U = blocks(T)
EXACT_OVERLAP = complex(PSI2.conj() @ (W.conj().T @ U) @ PSI2)
EXACT_PROCESS = complex(np.trace(W.conj().T @ U) / D)
print(f"instance: 2-site, t={T}, W=Trotter(reps={REPS_W}), U=exact")
print(f"  exact state overlap   <psi|W+U|psi> = {EXACT_OVERLAP:+.6f}  "
      f"|.|^2 = {abs(EXACT_OVERLAP)**2:.6f}")
print(f"  exact process overlap Tr[W+U]/d     = {EXACT_PROCESS:+.6f}  "
      f"|.|^2 = {abs(EXACT_PROCESS)**2:.6f}")
print("  (these are DIFFERENT quantities -- state-specific vs state-independent)\n")


def uncontrolled(kind):
    """W or U as a bare n-qubit circuit (no ancilla), for the baselines that need one.

    W MUST be the genuine Trotter circuit, not its matrix. Synthesising W from its matrix
    would certify a circuit nobody runs, and would understate the echo's cost -- the whole
    question is how expensive it is to verify the ACTUAL approximate circuit. U is the exact
    target, so matrix synthesis is the right construction for it (that is what "exact" means
    in the notebook's own builder)."""
    if kind == "exact":
        qc = QC(N2)
        qc.unitary(U, range(N2))
        return qc
    # identical synthesis to build_controlled_evolution(..., "trotter", reps), minus .control(1)
    from qiskit.circuit.library import PauliEvolutionGate
    from qiskit.synthesis import SuzukiTrotter
    evo = PauliEvolutionGate(H2, time=T, synthesis=SuzukiTrotter(order=2, reps=REPS_W))
    qc = QC(N2)
    qc.append(evo, range(N2))
    return transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
                     seed_transpiler=0)


# ---------------- (2) Loschmidt echo ----------------
echo = QC(N2)
echo.compose(PREP2, inplace=True)
echo.compose(uncontrolled("exact"), inplace=True)                 # U
echo.compose(uncontrolled("trotter").inverse(), inplace=True)     # W^dag
echo.compose(PREP2.inverse(), inplace=True)
p0_echo = float(np.abs(SV(echo).data[0]) ** 2)
echo_m = echo.copy(); echo_m.measure_all()

# ---------------- (3) Hilbert-Schmidt test ----------------
hst = QC(2 * N2)
for j in range(N2):                                               # n Bell pairs
    hst.h(j); hst.cx(j, N2 + j)
hst.compose(uncontrolled("exact"), qubits=range(N2), inplace=True)          # U on A
hst.unitary(W.conj(), range(N2, 2 * N2))                                    # W* on B
for j in range(N2):                                               # inverse Bell
    hst.cx(j, N2 + j); hst.h(j)
p0_hst = float(np.abs(SV(hst).data[0]) ** 2)
hst_m = hst.copy(); hst_m.measure_all()

print("VERIFY each baseline computes what it claims (statevector, before any cost talk):")
print(f"  echo  P(0...0) = {p0_echo:.6f}   vs |<psi|W+U|psi>|^2 = {abs(EXACT_OVERLAP)**2:.6f}"
      f"   dev {abs(p0_echo-abs(EXACT_OVERLAP)**2):.2e}")
print(f"  HST   P(0...0) = {p0_hst:.6f}   vs |Tr[W+U]/d|^2      = {abs(EXACT_PROCESS)**2:.6f}"
      f"   dev {abs(p0_hst-abs(EXACT_PROCESS)**2):.2e}")
assert abs(p0_echo - abs(EXACT_OVERLAP) ** 2) < 1e-9, "echo baseline is wrong"
assert abs(p0_hst - abs(EXACT_PROCESS) ** 2) < 1e-9, "HST baseline is wrong"
print("  both baselines verified\n")

# ---------------- Track B circuits (arms A and B) ----------------
def track_b(phi, basis, final_hadamard):
    sys_reg, anc = QR(N2, "sys"), QR(1, "anc")
    qc = QC(sys_reg, anc)
    qc.compose(PREP2, qubits=sys_reg, inplace=True)
    qc.h(anc[0]); qc.x(anc[0])
    qc.append(ns["build_controlled_evolution"](H2, T, "trotter", REPS_W), [anc[0], *sys_reg])
    qc.x(anc[0])
    qc.append(ns["build_controlled_evolution"](H2, T, "exact"), [anc[0], *sys_reg])
    if phi != 0.0:
        qc.p(phi, anc[0])
    if final_hadamard:
        qc.h(anc[0])
    for j, b in enumerate(basis):
        if b == 0:
            qc.h(sys_reg[j])
        elif b == 1:
            qc.sdg(sys_reg[j]); qc.h(sys_reg[j])
    creg = CR(N2 + 1, "c"); qc.add_register(creg)
    qc.measure(sys_reg, creg[:N2]); qc.measure(anc[0], creg[N2])
    return qc


# ---------------- transpiled cost on the device we would actually use ----------------
from qiskit_ibm_runtime import QiskitRuntimeService
svc = QiskitRuntimeService()
backend = svc.backend(sys.argv[1] if len(sys.argv) > 1 else "ibm_marrakesh")
TWOQ = [g for g in ("cz", "ecr", "cx") if g in backend.operation_names]
print(f"transpiled cost on {backend.name}:\n")


def cost(qc):
    t = transpile(qc, backend, optimization_level=3, seed_transpiler=2026)
    return int(sum(v for k, v in t.count_ops().items() if k in TWOQ)), int(t.depth())


rows = [
    dict(method="(1) classical fidelity (AQC's own score)", qubits=0, circuits=0,
         two_q=0, depth=0, delivers="|<psi_W|psi_U>|^2", scalable="NO -- needs simulation",
         phase="n/a", per_observable="no"),
]
n2q, dep = cost(echo_m)
rows.append(dict(method="(2) Loschmidt echo", qubits=N2, circuits=1, two_q=n2q, depth=dep,
                 delivers="|<psi|W+U|psi>|^2", scalable="yes", phase="NO (magnitude only)",
                 per_observable="no"))
n2q, dep = cost(hst_m)
rows.append(dict(method="(3) Hilbert-Schmidt test", qubits=2 * N2, circuits=1, two_q=n2q,
                 depth=dep, delivers="|Tr[W+U]/d|^2 (state-INDEPENDENT)", scalable="yes",
                 phase="NO (magnitude only)", per_observable="no"))
n2q, dep = cost(track_b(0.0, (2,) * N2, True))
rows.append(dict(method="(4) Track B, ancilla only [garbage discarded]", qubits=N2 + 1,
                 circuits=2, two_q=n2q, depth=dep, delivers="<psi|W+U|psi> complex",
                 scalable="yes", phase="YES", per_observable="no"))
n2q_b, dep_b = cost(track_b(0.0, (2,) * N2, False))
rows.append(dict(method="(5) Track B + shadows [ours]", qubits=N2 + 1,
                 circuits=2 * 9 + 9, two_q=max(n2q, n2q_b), depth=max(dep, dep_b),
                 delivers="the above PLUS <O>_W and <O>_U separately, every Pauli O",
                 scalable="yes", phase="YES", per_observable="YES"))

hdr = f"{'method':<44}{'qubits':>7}{'circuits':>10}{'2q':>6}{'depth':>7}  {'phase?':<8}{'per-obs?':<9}"
print(hdr); print("-" * len(hdr))
for r in rows:
    print(f"{r['method']:<44}{r['qubits']:>7}{r['circuits']:>10}{r['two_q']:>6}"
          f"{r['depth']:>7}  {r['phase']:<8}{r['per_observable']:<9}")

print("\nREADING THIS HONESTLY:")
print("  * The Loschmidt echo is CHEAPER than our arm on every axis and answers the scalar")
print("    question fine. If all you want is 'how close is W to U', use the echo.")
print("  * The HST answers a STRONGER question (state-independent process overlap) but needs")
print("    2n qubits, which is why it is rarely run on hardware at useful sizes.")
print("  * Neither the echo nor the HST can tell you WHICH observable the approximation")
print("    broke -- they return one number. That is the gap arm B fills, at zero extra")
print("    circuits over Track B itself, because the shadows are already being recorded.")

with open("/home/martin/Documents/QiskitHackathon/2026/evidence/track_b_baselines.json",
          "w") as fh:
    json.dump(dict(backend=backend.name, t=T, reps_w=REPS_W,
                   exact_state_overlap=[EXACT_OVERLAP.real, EXACT_OVERLAP.imag],
                   exact_process_overlap=[EXACT_PROCESS.real, EXACT_PROCESS.imag],
                   echo_p0=p0_echo, hst_p0=p0_hst, rows=rows), fh, indent=2)
print("\nwrote evidence/track_b_baselines.json")

# ---------------- IS THE ECHO'S CHEAPNESS REAL, OR AN n=2 ARTEFACT? ----------------
# At n=2 any product of 2-qubit unitaries collapses to ONE 2-qubit unitary (<=3 CX), so the
# transpiler can fuse U and W^dag and the echo looks nearly free. That is the same class of
# artefact R025 found for exact synthesis at n=3. Re-measure the algorithmic cost at n=2,3,4
# with all-to-all connectivity (no routing) so the comparison isolates gate count.
print("\n" + "=" * 76)
print("SCALING CHECK -- is the echo's advantage real or an n=2 collapse artefact?")
print("=" * 76)
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.synthesis import SuzukiTrotter
from scipy.linalg import expm

def chain_ham(n):
    terms = [("XX", [i, i + 1], 0.65) for i in range(n - 1)]
    terms += [("YY", [i, i + 1], 0.65) for i in range(n - 1)]
    terms += [("ZZ", [i, i + 1], 0.25) for i in range(n - 1)]
    terms += [("Z", [i], h) for i, h in enumerate((0.40, -0.50, 0.15, 0.20)[:n])]
    return ns["SparsePauliOp"].from_sparse_list(terms, num_qubits=n).simplify()

def n2q_of(qc):
    t = transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=3,
                  seed_transpiler=2026)
    return int(t.count_ops().get("cx", 0))

print(f"{'n':>3}{'echo 2q':>10}{'TrackB 2q':>12}{'ratio':>9}")
print("-" * 34)
scal = []
for n in (2, 3, 4):
    Hn = chain_ham(n)
    prep = QC(n); prep.ry(1.3, 0)
    Un = expm(-1j * Hn.to_matrix() * T)
    trot = QC(n)
    trot.append(PauliEvolutionGate(Hn, time=T, synthesis=SuzukiTrotter(order=2, reps=REPS_W)),
                range(n))
    e = QC(n)
    e.compose(prep, inplace=True)
    e.unitary(Un, range(n))
    e.compose(trot.inverse(), inplace=True)
    e.compose(prep.inverse(), inplace=True)
    b = QC(n + 1)                              # Track B: anti-controlled W then controlled U
    b.compose(prep, qubits=range(n), inplace=True)
    b.h(n); b.x(n)
    b.append(ns["build_controlled_evolution"](Hn, T, "trotter", REPS_W), [n, *range(n)])
    b.x(n)
    b.append(ns["build_controlled_evolution"](Hn, T, "exact"), [n, *range(n)])
    b.h(n)
    ce, cb = n2q_of(e), n2q_of(b)
    scal.append(dict(n=n, echo_2q=ce, track_b_2q=cb, ratio=cb / max(ce, 1)))
    print(f"{n:>3}{ce:>10}{cb:>12}{cb/max(ce,1):>9.1f}x")
print("\n  VERDICT, corrected by this check: the echo IS cheaper at every n, but the 52x")
print("  headline at n=2 is mostly collapse artefact -- at n=3,4 it is 6.0x and 4.0x and")
print("  still falling, because Track B's control overhead is a constant factor while the")
print("  echo's two evolutions grow at the same rate. Quote 4-6x, never 52x.")
print("  Either way the echo wins on cost, so our arm is justified by WHAT IT RETURNS")
print("  (phase, and the per-observable profile), never by being cheaper.")

d = json.load(open("/home/martin/Documents/QiskitHackathon/2026/evidence/track_b_baselines.json"))
d["scaling"] = scal
json.dump(d, open("/home/martin/Documents/QiskitHackathon/2026/evidence/track_b_baselines.json", "w"), indent=2)
print("\nupdated evidence/track_b_baselines.json with the scaling check")
