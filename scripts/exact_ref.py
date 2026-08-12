"""exact_ref.py — Gate-0 exact reference for Topic 5 (shadow-enhanced Hadamard test).

Pure numpy. Provides:
  * XXZ chain builder (open boundary) + conserved magnetization M = sum Z_i
  * convention checks: [M,H]=0, spectrum nondegeneracy (min gap)
  * exact signals g1(t) = <psi0|U(t)|psi0>,  gM(t) = <psi0| M U(t) |psi0>
    via spectral sums, cross-checked against an INDEPENDENT RK4 Schrodinger
    integration (different code path, catches eigendecomposition mistakes)
  * dense-DTFT spectral recovery of (E_k, |c_k|^2, m_k) from the signals
  * grid suggestion (Nyquist + Hann-lobe separation margins shown, not eyeballed)

Conventions (document in CONVENTIONS.md; adapt params to the base notebook):
  * qubit i lives at kron slot n-1-i  =>  little-endian, Qiskit-compatible:
    basis index b_{n-1}...b_1 b_0, qubit 0 is the LEAST significant bit.
  * Z|0> = +|0>.  M = sum_i Z_i.
  * H = sum_i [ J (X_i X_{i+1} + Y_i Y_{i+1}) + Delta Z_i Z_{i+1} ] + h * M
    The default h != 0 matters: with h = 0 the XXZ chain has global spin-flip
    symmetry, so the +m and -m sectors are pairwise DEGENERATE and frequency
    peaks cannot be symmetry-resolved. Verify what the supplied model uses.

Self-test: python exact_ref.py   (prints PASS/FAIL with measured errors)
"""
from __future__ import annotations

import numpy as np

I2 = np.eye(2, dtype=complex)
PX = np.array([[0, 1], [1, 0]], dtype=complex)
PY = np.array([[0, -1j], [1j, 0]], dtype=complex)
PZ = np.array([[1, 0], [0, -1]], dtype=complex)


def _kron_all(ops):
    out = np.array([[1.0 + 0j]])
    for op in ops:
        out = np.kron(out, op)
    return out


def op_on(op, i, n):
    """Single-qubit operator `op` on qubit i of n, little-endian (qubit 0 = LSB)."""
    ops = [I2] * n
    ops[n - 1 - i] = op
    return _kron_all(ops)


def two_site(op_a, i, op_b, j, n):
    ops = [I2] * n
    ops[n - 1 - i] = op_a
    ops[n - 1 - j] = op_b
    return _kron_all(ops)


def build_xxz(n=3, J=1.0, delta=0.5, h=0.31):
    """Open-boundary XXZ + longitudinal field. Returns (H, M)."""
    d = 2 ** n
    H = np.zeros((d, d), dtype=complex)
    for i in range(n - 1):
        H += J * (two_site(PX, i, PX, i + 1, n) + two_site(PY, i, PY, i + 1, n))
        H += delta * two_site(PZ, i, PZ, i + 1, n)
    M = sum(op_on(PZ, i, n) for i in range(n))
    H += h * M
    return H, M


def convention_checks(H, M):
    """Return (commutator_norm, min_gap, evals). Degeneracy => min_gap ~ 0."""
    comm = H @ M - M @ H
    comm_norm = np.linalg.norm(comm)
    evals = np.linalg.eigvalsh(H)
    gaps = np.diff(np.sort(evals))
    return comm_norm, float(gaps.min()), evals


def spectral_data(H, M, psi0):
    """Eigen-decompose; return (evals, weights |c_k|^2, labels m_k).

    Requires nondegenerate H so eigenvectors are simultaneously M eigenstates;
    m_k = <k|M|k> then rounds to an integer. Checked by the caller/self-test.
    """
    evals, evecs = np.linalg.eigh(H)
    c = evecs.conj().T @ psi0
    w = np.abs(c) ** 2
    m = np.real(np.einsum("ik,ij,jk->k", evecs.conj(), M, evecs))
    return evals, w, m


def g_signals(tgrid, evals, w, m):
    """Exact g1(t), gM(t) from spectral data."""
    phase = np.exp(-1j * np.outer(tgrid, evals))      # [T, K]
    g1 = phase @ w
    gM = phase @ (w * m)
    return g1, gM


def rk4_g1_gM(H, M, psi0, tgrid):
    """Independent path: integrate i dpsi/dt = H psi with RK4 substeps."""
    def deriv(psi):
        return -1j * (H @ psi)

    g1 = np.empty(len(tgrid), dtype=complex)
    gM = np.empty(len(tgrid), dtype=complex)
    psi = psi0.astype(complex).copy()
    t_prev = 0.0
    bra = psi0.conj()
    braM = (M @ psi0).conj()
    for idx, t in enumerate(tgrid):
        span = t - t_prev
        nsub = max(1, int(np.ceil(span / 0.002)))
        dt = span / nsub if nsub else 0.0
        for _ in range(nsub):
            k1 = deriv(psi)
            k2 = deriv(psi + 0.5 * dt * k1)
            k3 = deriv(psi + 0.5 * dt * k2)
            k4 = deriv(psi + dt * k3)
            psi = psi + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        t_prev = t
        g1[idx] = bra @ psi
        gM[idx] = braM @ psi
    return g1, gM


# ---------------------------------------------------------------- recovery ---

def dtft(g, tgrid, wgrid, window=True):
    """Dense DTFT  S(omega) = sum_j h_j g_j exp(+i omega t_j).

    Peaks of |S| sit at omega = E_k for signals sum_k w_k exp(-i E_k t).
    Explicit omega grid instead of FFT: no bin/sign bookkeeping to get wrong.
    """
    h = np.hanning(len(tgrid)) if window else np.ones(len(tgrid))
    ker = np.exp(1j * np.outer(wgrid, tgrid))          # [W, T]
    return ker @ (h * g), h


def _refine_quadratic(y, i, wgrid):
    if i == 0 or i == len(y) - 1:
        return wgrid[i], y[i]
    y0, y1, y2 = y[i - 1], y[i], y[i + 1]
    denom = (y0 - 2 * y1 + y2)
    if abs(denom) < 1e-30:
        return wgrid[i], y1
    delta = 0.5 * (y0 - y2) / denom
    step = wgrid[1] - wgrid[0]
    return wgrid[i] + delta * step, y1 - 0.25 * (y0 - y2) * delta


def find_peaks(mag, wgrid, rel_thresh=0.03, min_sep=None):
    """Local maxima of |S| above rel_thresh*max, greedy suppression by min_sep."""
    thr = rel_thresh * mag.max()
    idx = [i for i in range(1, len(mag) - 1)
           if mag[i] >= thr and mag[i] >= mag[i - 1] and mag[i] > mag[i + 1]]
    idx.sort(key=lambda i: -mag[i])
    kept = []
    for i in idx:
        if all(abs(wgrid[i] - wgrid[j]) >= (min_sep or 0.0) for j in kept):
            kept.append(i)
    return sorted(kept)


def recover(g1, gM, tgrid, wgrid=None, rel_thresh=0.005):
    """Return list of dicts: {'E','weight','m'} recovered from the two signals."""
    T = tgrid[-1] - tgrid[0]
    lobe = 8 * np.pi / T                               # Hann main-lobe full width
    if wgrid is None:
        span = np.pi / (tgrid[1] - tgrid[0])           # Nyquist range
        wgrid = np.linspace(-span, span, 16384)
    S1, h = dtft(g1, tgrid, wgrid)
    SM, _ = dtft(gM, tgrid, wgrid)
    mag = np.abs(S1)
    idx = find_peaks(mag, wgrid, rel_thresh, min_sep=0.6 * lobe)
    # Hann sidelobe guard: a "peak" within a few lobes of a much taller one is
    # leakage (first Hann sidelobe ~ -31 dB), not a state. 5% guard is generous.
    idx = [i for i in idx
           if not any(abs(wgrid[i] - wgrid[j]) < 4 * lobe and mag[i] < 0.05 * mag[j]
                      for j in idx if j != i)]
    peaks = []
    for i in idx:
        E, amp = _refine_quadratic(mag, i, wgrid)
        j = int(np.argmin(np.abs(wgrid - E)))
        weight = amp / h.sum()
        m_lab = float(np.real(SM[j] / S1[j]))
        peaks.append({"E": float(E), "weight": float(weight), "m": m_lab})
    return peaks


def suggest_grid(evals, min_gap, nyquist_margin=4.0, lobe_factor=2.0):
    """dt from Nyquist with margin; N so the Hann lobe resolves the min gap."""
    Emax = float(np.max(np.abs(evals)))
    dt = np.pi / (nyquist_margin * Emax)
    T_needed = lobe_factor * 8 * np.pi / min_gap
    N = int(np.ceil(T_needed / dt))
    return dt, N, Emax


# ---------------------------------------------------------------- self-test --

def _selftest():
    ok = True
    n = 3
    H, M = build_xxz(n=n)
    comm, min_gap, evals = convention_checks(H, M)
    print(f"[check] ||[H,M]|| = {comm:.2e}   (want ~0)")
    print(f"[check] min spectral gap = {min_gap:.4f}   (want >> 0; "
          f"h=0 would make +m/-m sectors degenerate)")
    ok &= comm < 1e-10 and min_gap > 1e-3

    psi0 = np.ones(2 ** n, dtype=complex) / np.sqrt(2 ** n)   # |+++>
    evals_d, w, m = spectral_data(H, M, psi0)
    m_round = np.round(m)
    print(f"[check] labels m_k integer to {np.max(np.abs(m - m_round)):.2e}; "
          f"sum w = {w.sum():.6f}")
    ok &= np.max(np.abs(m - m_round)) < 1e-8 and abs(w.sum() - 1) < 1e-10

    dt, N, Emax = suggest_grid(evals_d, min_gap)
    N = min(N, 4096)
    tgrid = dt * np.arange(N)
    print(f"[grid ] Emax={Emax:.3f}  dt={dt:.4f} (Nyquist margin 4x)  "
          f"N={N}  T={dt*N:.1f}  Hann lobe={8*np.pi/(dt*N):.4f} < gap {min_gap:.4f}")

    g1, gM = g_signals(tgrid, evals_d, w, m)
    coarse = tgrid[:: max(1, N // 64)][:64]
    g1_rk, gM_rk = rk4_g1_gM(H, M, psi0, coarse)
    g1_sp, gM_sp = g_signals(coarse, evals_d, w, m)
    e1 = np.max(np.abs(g1_rk - g1_sp))
    eM = np.max(np.abs(gM_rk - gM_sp))
    print(f"[xchk ] spectral-sum vs RK4:  max|dg1|={e1:.2e}  max|dgM|={eM:.2e}")
    ok &= e1 < 1e-6 and eM < 1e-6

    peaks = recover(g1, gM, tgrid)
    keep = w > 1e-3
    truth = sorted(zip(evals_d[keep], w[keep], m_round[keep]))
    print(f"[recov] {len(peaks)} peaks found, {keep.sum()} true weights > 1e-3")
    err_E = err_w = err_m = 0.0
    matched = 0
    for E_t, w_t, m_t in truth:
        cand = min(peaks, key=lambda p: abs(p["E"] - E_t))
        if abs(cand["E"] - E_t) > 0.1:
            continue
        matched += 1
        err_E = max(err_E, abs(cand["E"] - E_t))
        err_w = max(err_w, abs(cand["weight"] - w_t))
        err_m = max(err_m, abs(cand["m"] - m_t))
    print(f"[recov] matched {matched}/{len(truth)}  "
          f"max|dE|={err_E:.2e}  max|dw|={err_w:.2e}  max|dm|={err_m:.2e}")
    ok &= matched == len(truth) and err_E < 5e-3 and err_w < 2e-2 and err_m < 0.1

    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
