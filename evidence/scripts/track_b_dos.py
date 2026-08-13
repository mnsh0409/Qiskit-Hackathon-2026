"""PROOF OF CONCEPT: Track B is a density-of-states estimator when you feed it the
maximally mixed state -- which links it directly to Goh & Koczor, arXiv:2407.03414v2.

THE CLAIM, stated before it is tested. Track B's ancilla measures
      chi_AB(t) = Tr[W(t)^dag U(t) rho].
Set rho = I/d. Then
      chi_AB(t) = Tr[W^dag U]/d,
and two things follow:

  (1) W = I  =>  chi_AB(t) = Tr[U(t)]/d, which is exactly the quantity behind that paper's
      Eq. (7), G(t) = (1/sqrt(2pi)) Tr[e^{-iHt}] -- the generating function whose Fourier
      transform is the density of states. So the DOS estimator is the W=I special case of
      Track B, not a separate protocol. (R038 already showed the shadow-Hadamard pipeline
      transfers; this shows the TRACK B circuit contains it.)

  (2) W != I  =>  chi_AB(t) = Tr[W^dag U]/d is the STATE-INDEPENDENT process overlap: the
      same quantity our Hilbert-Schmidt arm measured (R043/R044) -- except the HST returns
      |Tr[W^dag U]/d|^2 on 2n qubits, while this returns the complex number on n+1.

WHETHER THE PHASE IS WORTH ANYTHING DEPENDS ON THE CASE, and section 3 measures which:
for W=I the imaginary part reaches 0.50 and the HST genuinely loses information, but for
W = a SYMMETRIC product formula with real H it is zero to 1e-14 by time-reversal symmetry
(U* = U^dag and, because the Suzuki sequence is palindromic, W* = W^dag). We found this by
checking rather than assuming, and the slide says so.

Because Tr[A] = sum_z <z|A|z>, the maximally mixed input is realised by enumerating the d
computational basis states and averaging -- exhaustive at these sizes, and the deterministic
version of that paper's Statement 2 (a 1-design, e.g. random {I,X}^n bit-flips, suffices).

Nothing here is claimed to be a scaling advantage. It is a proof of concept that the two
protocols are the same circuit, checked numerically.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json
sys.path.insert(0, REPO)
from hardware_run import load_notebook_definitions, get_model

import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator

ns = load_notebook_definitions()
QC, QR, CR = ns["QuantumCircuit"], ns["QuantumRegister"], ns["ClassicalRegister"]
SV, OP = ns["Statevector"], ns["Operator"]
PHI_RE, PHI_IM = ns["PHI_RE"], ns["PHI_IM"]

N2, H2, Q2, PREP2, PSI2, _ = get_model(ns, "2site")
D = 2 ** N2
REPS_W = 1
TIMES = np.linspace(0.0, 3.0, 13)
SHOTS = 4000


def blocks(t):
    """Control is the gate's qubit 0 = LSB, so the |1>-block is the odd sublattice."""
    U = OP(ns["build_controlled_evolution"](H2, t, "exact")).data[1::2, 1::2]
    W = OP(ns["build_controlled_evolution"](H2, t, "trotter", REPS_W)).data[1::2, 1::2]
    return W, U


def build(t, phi, z, w_kind):
    """Track B with the system prepared in computational basis state |z>."""
    sys_reg, anc = QR(N2, "sys"), QR(1, "anc")
    qc = QC(sys_reg, anc)
    for j in range(N2):                                   # prepare |z>
        if (z >> j) & 1:
            qc.x(sys_reg[j])
    qc.h(anc[0])
    if w_kind == "trotter":
        qc.x(anc[0])
        qc.append(ns["build_controlled_evolution"](H2, t, "trotter", REPS_W),
                  [anc[0], *sys_reg])
        qc.x(anc[0])
    qc.append(ns["build_controlled_evolution"](H2, t, "exact"), [anc[0], *sys_reg])
    if phi != 0.0:
        qc.p(phi, anc[0])
    qc.h(anc[0])
    creg = CR(1, "c"); qc.add_register(creg)
    qc.measure(anc[0], creg[0])                           # ancilla only -- this is DOS
    return qc


def exact_target(t, w_kind):
    W, U = blocks(t)
    M = U if w_kind == "identity" else W.conj().T @ U
    return complex(np.trace(M) / D)


# ---------------- 1. statevector check of the claim ----------------
print("=" * 78)
print("1. STATEVECTOR: does the mixed-input Track B circuit equal Tr[W^dag U]/d ?")
print("=" * 78)
worst = 0.0
for w_kind in ("identity", "trotter"):
    for t in (0.0, 0.9, 1.8, 2.7):
        got = []
        for phi in (PHI_RE, PHI_IM):
            acc = 0.0
            for z in range(D):
                qc = build(t, phi, z, w_kind)
                qc.remove_final_measurements(inplace=True)
                p = np.abs(SV(qc).data) ** 2
                acc += float(p[:D].sum() - p[D:].sum())    # <Z_a>, ancilla is highest qubit
            got.append(acc / D)
        dev = abs(complex(*got) - exact_target(t, w_kind))
        worst = max(worst, dev)
    print(f"   W = {w_kind:<9} max deviation so far {worst:.3e}")
print(f"\n   worst {worst:.3e} -> "
      f"{'CLAIM CONFIRMED' if worst < 1e-10 else 'CLAIM FALSE, stop'}")
assert worst < 1e-10, "mixed-input Track B does not reproduce Tr[W^dag U]/d"
print("   W=I gives Tr[U]/d, i.e. the DOS generating function of arXiv:2407.03414v2 Eq. (7);")
print("   W!=I gives the complex process overlap the Hilbert-Schmidt test returns squared.\n")

# ---------------- 2. shot-based estimate on the simulator ----------------
print("=" * 78)
print(f"2. SHOTS ({SHOTS}/setting, AerSimulator): DOS signal and the error spectrum")
print("=" * 78)
backend = AerSimulator()
out = {"times": TIMES.tolist(), "shots": SHOTS, "curves": {}}
for w_kind in ("identity", "trotter"):
    meas, exact = [], []
    for i, t in enumerate(TIMES):
        quad = []
        for k, phi in enumerate((PHI_RE, PHI_IM)):
            acc = 0.0
            for z in range(D):
                qc = build(t, phi, z, w_kind)
                counts = backend.run(transpile(qc, backend), shots=SHOTS,
                                     seed_simulator=7000 + 97 * i + 13 * k + z
                                     ).result().get_counts()
                n0, n1 = counts.get("0", 0), counts.get("1", 0)
                acc += (n0 - n1) / (n0 + n1)
            quad.append(acc / D)
        meas.append(complex(*quad)); exact.append(exact_target(t, w_kind))
    meas, exact = np.array(meas), np.array(exact)
    rms = float(np.sqrt(np.mean(np.abs(meas - exact) ** 2)))
    out["curves"][w_kind] = dict(measured=[[c.real, c.imag] for c in meas],
                                 exact=[[c.real, c.imag] for c in exact], rms=rms)
    tag = "Tr[U]/d   (the DOS signal, W=I)" if w_kind == "identity" \
        else "Tr[W+U]/d (the Trotter-error signal)"
    print(f"   {tag:<40} rms error {rms:.4f}")
    print(f"      t=0 value {meas[0]:+.4f} (exact {exact[0]:+.4f}) -- must be 1 exactly")

# ---------------- 3. what the DOS route buys over the HST arm ----------------
print("\n" + "=" * 78)
print("3. THE CONCRETE LINK: same quantity, half the register, and we keep the phase")
print("=" * 78)
print(f"   {'method':<34}{'qubits':>8}{'returns':>34}")
print("-" * 78)
print(f"   {'Hilbert-Schmidt test (R043/R044)':<34}{2*N2:>8}{'|Tr[W+U]/d|^2  (magnitude only)':>34}")
print(f"   {'Track B, mixed input (this file)':<34}{N2+1:>8}{'Tr[W+U]/d      (complex)':>34}")
# Where the phase actually matters -- checked, not assumed. It is NOT uniform.
im_u = max(abs(exact_target(t, "identity").imag) for t in np.linspace(0, 3, 61))
im_wu = max(abs(exact_target(t, "trotter").imag) for t in np.linspace(0, 3, 61))
print(f"\n   max |Im Tr[U]/d|   = {im_u:.4f}   <- the DOS signal is genuinely complex")
print(f"   max |Im Tr[W+U]/d| = {im_wu:.2e}   <- the Trotter signal is REAL to machine precision")
print("\n   SO THE 'WE KEEP THE PHASE' ADVANTAGE IS CASE-SPECIFIC, and we say which case:")
print("   * DOS (W=I): the phase carries most of the signal past t~1.5, so the HST's")
print("     magnitude-only answer genuinely loses information. This is the case that links")
print("     to arXiv:2407.03414v2, and the advantage is real.")
print("   * Trotter (W=2nd-order Suzuki): H is real symmetric so U* = U^dag, and a SYMMETRIC")
print("     (palindromic) product formula gives W* = W^dag too, which forces Tr[W^dag U] real.")
print("     Here the HST loses nothing by squaring, and our only edge is n+1 qubits vs 2n.")
print("\n   BONUS, and it costs nothing: Im Tr[W^dag U] = 0 is an identity for this class, so a")
print("   measured nonzero imaginary part is pure device error -- the same reference-free")
print("   diagnostic as the conserved-charge channel, on a different observable.")
out["phase"] = dict(max_im_dos=im_u, max_im_trotter=im_wu)

with open(os.path.join(REPO, "evidence/track_b_dos.json"), "w") as fh:
    json.dump(out, fh, indent=2)
print("\nwrote evidence/track_b_dos.json")
