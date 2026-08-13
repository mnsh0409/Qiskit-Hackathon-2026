"""DOES THE 2D LATTICE BREAK OUR HEADLINE? Re-run the AQC crossover and the Track B
baseline costs on a 2D grid, against the matched 1D chain.

WHY THIS COULD GO BADLY FOR US, stated before running:
  * AQC-Tensor is an MPS method. MPS is native to 1D; on a 2D grid mapped to a linear qubit
    order the entanglement across a cut grows with the perimeter, so the compression could
    need a much larger bond dimension or simply converge worse. Our 36x headline (R046) was
    measured on a chain.
  * A 2D grid has more bonds than a chain at the same site count (e.g. 10 vs 7 at n=8), so
    every Trotter-derived circuit -- the AQC seed included -- gets longer.
  * The exact controlled block, by contrast, is GEOMETRY-BLIND: it synthesises an arbitrary
    (n+1)-qubit unitary at ~4^(n+1) regardless of the bond list. So 2D shifts our side of
    the comparison and not the baseline's. If the crossover moves right, we say so.

Also re-checks the phase trap (R046) in 2D: it should persist, being a property of the
objective rather than of the lattice.

Track B baselines (R043) are re-costed on the same geometries in the second half.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json, time
sys.path.insert(0, REPO)
from hardware_run import load_notebook_definitions

import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator, Statevector

from qiskit_addon_aqc_tensor.ansatz_generation import generate_ansatz_from_circuit
from qiskit_addon_aqc_tensor.objective import OneMinusFidelity
from qiskit_addon_aqc_tensor.simulation import tensornetwork_from_circuit
from qiskit_addon_aqc_tensor.simulation.quimb import QuimbSimulator
import quimb.tensor

ns = load_notebook_definitions()
SPO = ns["SparsePauliOp"]
J, DELTA, T = 0.65, 0.25, 0.9
FIELDS = [0.40, -0.50, 0.15, 0.20, -0.30, 0.10, 0.25, -0.15, 0.35]
simulator = QuimbSimulator(quimb.tensor.CircuitMPS, autodiff_backend="jax")

GEOMS = {  # n -> (chain bonds, grid bonds, grid label)
    4: ([(0, 1), (1, 2), (2, 3)], [(0, 1), (2, 3), (0, 2), (1, 3)], "2x2"),
    6: ([(i, i + 1) for i in range(5)],
        [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)], "2x3"),
    8: ([(i, i + 1) for i in range(7)],
        [(0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7),
         (0, 4), (1, 5), (2, 6), (3, 7)], "2x4"),
}


def ham(n, bonds):
    terms = []
    for i, j in bonds:
        terms += [("XX", [i, j], J), ("YY", [i, j], J), ("ZZ", [i, j], DELTA)]
    terms += [("Z", [i], FIELDS[i]) for i in range(n)]
    return SPO.from_sparse_list(terms, num_qubits=n).simplify()


def cx_of(qc):
    t = transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
                  seed_transpiler=0)
    return int(t.count_ops().get("cx", 0))


def trotter(H, n, reps):
    qc = QuantumCircuit(n)
    qc.append(ns["PauliEvolutionGate"](H, time=T,
              synthesis=ns["SuzukiTrotter"](order=2, reps=reps)), range(n))
    return transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1,
                     seed_transpiler=0)


print("=" * 82)
print("PART 1 -- does the AQC crossover survive in 2D?")
print("=" * 82)
print(f"{'n':>3} {'geometry':>10}{'bonds':>7}{'exact':>8}{'Trotter':>9}{'AQC':>7}"
      f"{'AQC vs exact':>14}{'state infid':>13}{'|dchi| fixed':>13}")
print("-" * 82)
ROWS = []
for n, (cb, gb, glabel) in GEOMS.items():
    for gname, bonds in (("1D chain", cb), (f"2D {glabel}", gb)):
        H = ham(n, bonds)
        prep = QuantumCircuit(n); prep.ry(1.3, 0)
        psi = np.asarray(Statevector(prep).data)
        U = ns["exact_unitary"](H, T)

        cq = QuantumCircuit(n + 1)
        cq.append(ns["build_controlled_evolution"](H, T, "exact"), [n, *range(n)])
        cex = cx_of(cq)

        tr = trotter(H, n, 2)
        ctq = QuantumCircuit(n + 1)
        ctq.append(tr.to_gate().control(1), [n, *range(n)])
        ctr = cx_of(ctq)

        ansatz, init = generate_ansatz_from_circuit(trotter(H, n, 1),
                                                    qubits_initially_zero=True)
        ft = QuantumCircuit(n); ft.compose(prep, inplace=True)
        ft.compose(trotter(H, n, 3), inplace=True)
        fa = QuantumCircuit(n); fa.compose(prep, inplace=True); fa.compose(ansatz, inplace=True)
        res = minimize(OneMinusFidelity(tensornetwork_from_circuit(ft, simulator), fa,
                                        simulator), np.array(init), jac=True,
                       method="L-BFGS-B", options={"maxiter": 400})
        bound = ansatz.assign_parameters(res.x)
        caq = QuantumCircuit(n + 1)
        caq.append(bound.to_gate().control(1), [n, *range(n)])
        caqc = cx_of(caq)

        W = Operator(bound).data
        infid = 1 - abs(np.vdot(np.asarray(Statevector(fa.assign_parameters(res.x)).data),
                                U @ psi))
        chi_u = complex(psi.conj() @ U @ psi); chi_w = complex(psi.conj() @ W @ psi)
        theta = float(np.angle(np.vdot(U @ psi, W @ psi)))
        err_naive = abs(chi_w - chi_u)
        err_fixed = abs(np.exp(-1j * theta) * chi_w - chi_u)
        ratio = cex / caqc
        tag = f"{ratio:.2f}x " + ("WIN" if ratio > 1 else "loss")
        print(f"{n:>3} {gname:>10}{len(bonds):>7}{cex:>8}{ctr:>9}{caqc:>7}"
              f"{tag:>14}{infid:>13.2e}{err_fixed:>13.4f}")
        ROWS.append(dict(n=n, geometry=gname, bonds=len(bonds), exact_cx=cex,
                         trotter_cx=ctr, aqc_cx=caqc, aqc_vs_exact=float(ratio),
                         state_infidelity=float(infid),
                         chi_err_naive=float(err_naive), chi_err_fixed=float(err_fixed)))
    print()

print("=" * 82)
print("PART 2 -- Track B baseline costs on the same geometries")
print("=" * 82)
print(f"{'n':>3} {'geometry':>10}{'echo':>8}{'HST':>8}{'Track B':>10}"
      f"{'echo advantage':>17}")
print("-" * 82)
BASE = []
for n, (cb, gb, glabel) in GEOMS.items():
    for gname, bonds in (("1D chain", cb), (f"2D {glabel}", gb)):
        H = ham(n, bonds)
        prep = QuantumCircuit(n); prep.ry(1.3, 0)
        U = ns["exact_unitary"](H, T)
        tr = trotter(H, n, 1)

        echo = QuantumCircuit(n)
        echo.compose(prep, inplace=True)
        echo.unitary(U, range(n))
        echo.compose(tr.inverse(), inplace=True)
        echo.compose(prep.inverse(), inplace=True)
        e_cx = cx_of(echo)

        hst = QuantumCircuit(2 * n)
        for j in range(n):
            hst.h(j); hst.cx(j, n + j)
        hst.unitary(U, range(n))
        hst.unitary(Operator(tr).data.conj(), range(n, 2 * n))
        for j in range(n):
            hst.cx(j, n + j); hst.h(j)
        h_cx = cx_of(hst)

        tb = QuantumCircuit(n + 1)
        tb.compose(prep, qubits=range(n), inplace=True)
        tb.h(n); tb.x(n)
        tb.append(ns["build_controlled_evolution"](H, T, "trotter", 1), [n, *range(n)])
        tb.x(n)
        tb.append(ns["build_controlled_evolution"](H, T, "exact"), [n, *range(n)])
        tb.h(n)
        t_cx = cx_of(tb)
        print(f"{n:>3} {gname:>10}{e_cx:>8}{h_cx:>8}{t_cx:>10}"
              f"{t_cx/max(e_cx,1):>16.1f}x")
        BASE.append(dict(n=n, geometry=gname, bonds=len(bonds), echo_cx=e_cx,
                         hst_cx=h_cx, track_b_cx=t_cx,
                         echo_advantage=t_cx / max(e_cx, 1)))
    print()

with open(os.path.join(REPO, "evidence/geometry_2d.json"), "w") as fh:
    json.dump(dict(aqc=ROWS, baselines=BASE), fh, indent=2)
print("wrote evidence/geometry_2d.json")
