"""Ablation #4 (the one item from the original 5-item ablation request that was never
built): standard textbook Quantum Phase Estimation, as a genuinely different algorithm
to compare against the shadow-Hadamard + {DFT, matrix pencil} results already in
RESULTS.md (R011/R012/R021).

Design, chosen to make the comparison FAIR rather than favourable to either side:
  - m=5 counting qubits, t0 = T_MAX / 2^m = 12.6/32 = 0.39375. This makes QPE's total
    evolved time (2^m - 1)*t0 ~ T_MAX -- the SAME total-evolution budget the DFT/pencil
    analysis gets from the 64-point, T_max=12.6 time grid. Neither method is handed an
    artificially larger resolution budget than the other.
  - No-aliasing check: |E|_max < pi/t0 required. pi/t0 = 7.98; our populated spectrum's
    max |E| is 1.9463 (E_EXACT) and even the FULL spectral radius is 2.635 -- comfortably
    inside the aliasing-free window.
  - controlled-U(2^k * t0) is built directly via the graded build_controlled_evolution at
    time 2^k*t0 (method="exact"), NOT by literally repeating a base circuit 2^k times --
    this is the standard, efficient way to do QPE simulation and reuses the ALREADY
    VALIDATED controlled-evolution code rather than reimplementing anything.
  - QPE gives energies + weights (from the measured histogram) but, unlike the shadow
    protocol, gives NO symmetry label -- there is no "garbage register" to read. That
    absence is itself part of the comparison.

Validated on the ideal simulator (this file's own __main__ IS the validation -- there is
no separate hardware claim here, this is a Part-B-style simulator ablation matching
R011/R012's own methodology).
"""
import sys
sys.path.insert(0, "/home/martin/Documents/QiskitHackathon/2026")
from hardware_run import load_notebook_definitions

import json
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit.circuit.library import QFTGate
from qiskit_aer import AerSimulator
from scipy.signal import find_peaks

ns = load_notebook_definitions()
HAM, PSI = ns["HAM"], ns["PSI"]
N_SYS = ns["N_SYS"]
E_EXACT, Q_EXACT_LABELS, P_EXACT = ns["E_EXACT"], ns["Q_EXACT_LABELS"], ns["P_EXACT"]
T_MAX = ns["T_MAX"]
build_controlled_evolution = ns["build_controlled_evolution"]
state_prep_circuit = ns["state_prep_circuit"]

M = 5                          # counting qubits
T0 = T_MAX / 2 ** M
print(f"QPE design: m={M} counting qubits, t0={T0:.5f}, total evolved time "
      f"(2^m-1)*t0={(2**M-1)*T0:.2f} (budget target T_max={T_MAX:.2f})")
print(f"no-aliasing check: pi/t0={np.pi/T0:.3f} vs populated |E|_max="
      f"{np.max(np.abs(E_EXACT)):.3f}, full spectral radius="
      f"{np.max(np.abs(np.linalg.eigvalsh(HAM.to_matrix()))):.3f} -- both well inside\n")


def build_qpe_circuit():
    sys_reg = QuantumRegister(N_SYS, "sys")
    cnt_reg = QuantumRegister(M, "cnt")
    creg = ClassicalRegister(M, "c")
    qc = QuantumCircuit(sys_reg, cnt_reg, creg)

    qc.compose(state_prep_circuit(), qubits=sys_reg, inplace=True)
    qc.h(cnt_reg)

    for k in range(M):
        gate = build_controlled_evolution(HAM, (2 ** k) * T0, method="exact")
        qc.append(gate, [cnt_reg[k], *sys_reg])

    qc.append(QFTGate(M).inverse(), cnt_reg)
    qc.measure(cnt_reg, creg)
    return qc


qc = build_qpe_circuit()
backend = AerSimulator()
# basis_gates matches cell 61's resource_row() and R025 -- NOT transpile(qc, backend) alone,
# which left the circuit as opaque multi-qubit blocks (0 CX reported) since Aer doesn't force
# hardware-native decomposition the way a real backend's transpile does. This is the same
# convention every other cost comparison in RESULTS.md uses, so the CX counts are comparable.
tq = transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1, seed_transpiler=0)
print(f"circuit: {N_SYS + M} qubits total ({N_SYS} system + {M} counting), "
      f"depth {tq.depth()}, {tq.count_ops().get('cx', 0)} CX  (single circuit design -- "
      f"no basis variation needed, unlike the shadow protocol)")

SHOTS = 50_000
result = backend.run(tq, shots=SHOTS, seed_simulator=ns["SEED"]).result()
counts = result.get_counts()
print(f"\n{SHOTS:,} shots, {len(counts)} distinct outcomes observed")

# histogram over the M-bit outcome -> phase -> energy, unwrapped to (-pi/t0, pi/t0]
hist = np.zeros(2 ** M)
for bitstring, c in counts.items():
    j = int(bitstring, 2)
    hist[j] = c / SHOTS

j_grid = np.arange(2 ** M)
phase = j_grid / 2 ** M
phase_signed = np.where(phase < 0.5, phase, phase - 1.0)     # wrap to (-0.5, 0.5]
energy_grid = -2 * np.pi * phase_signed / T0                  # U=exp(-iHt0) -> phase=-E*t0/2pi
order = np.argsort(energy_grid)
energy_sorted, hist_sorted = energy_grid[order], hist[order]

print(f"energy bin width (QPE resolution) = 2*pi/((2^m)*t0) = {2*np.pi/(2**M*T0):.4f}  "
      f"(DFT's Rayleigh resolution 2*pi/T_max = {2*np.pi/T_MAX:.4f} -- by design, matched)")

idx, _ = find_peaks(hist_sorted, height=0.02)
peaks = [(float(energy_sorted[i]), float(hist_sorted[i])) for i in idx]
peaks.sort()
print(f"\n{len(peaks)} peaks found in the measured histogram:")
print(f"{'found E':>9} {'weight':>8} | {'nearest exact E':>16} {'exact p':>8} {'exact q':>8}")
matched_lines = set()
matched_errors = []
for e, w in peaks:
    k = int(np.argmin(np.abs(E_EXACT - e)))
    dE = abs(E_EXACT[k] - e)
    hit = dE < 0.35
    print(f"{e:+9.4f} {w:8.4f} | {E_EXACT[k]:+16.4f} {P_EXACT[k]:8.4f} "
          f"{Q_EXACT_LABELS[k]:+8d}" + ("" if hit else "  <-- no nearby exact line"))
    if hit:
        matched_lines.add(k)
        matched_errors.append(dE)

n_lines = len(matched_lines)
max_dE = max(matched_errors) if matched_errors else float("nan")

print(f"\nSUMMARY: {n_lines}/4 populated lines recovered, max|dE| on recovered lines = "
      f"{max_dE:.4f}")
print("Labels: NONE -- QPE has no garbage register to read; symmetry sector is not "
      "accessible from this measurement at all, at any cost.")

result_summary = dict(
    m_counting_qubits=M, t0=T0, shots=SHOTS, circuit_qubits=N_SYS + M,
    circuit_depth=tq.depth(), circuit_cx=int(tq.count_ops().get("cx", 0)),
    n_lines_recovered=n_lines, max_dE=None if np.isnan(max_dE) else float(max_dE),
    resolution_bin_width=float(2 * np.pi / (2 ** M * T0)),
    dft_resolution_for_comparison=float(2 * np.pi / T_MAX),
    peaks=[dict(E=e, weight=w) for e, w in peaks],
    labels_available=False,
)
with open("/home/martin/Documents/QiskitHackathon/2026/evidence/qpe_ablation_result.json", "w") as fh:
    json.dump(result_summary, fh, indent=2)
print("\nwrote evidence/qpe_ablation_result.json")
