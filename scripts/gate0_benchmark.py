# gate0_benchmark.py -- T0-approved Gate-0 driver (the ONLY site-specific code authorised by
# CONVENTIONS.md §8). Builds the FROZEN benchmark of §2 and reruns the shipped exact_ref
# self-test sequence on it, plus the §8.3 benchmark asserts.   Run:  python gate0_benchmark.py
import numpy as np
import exact_ref as er

def build_benchmark(n=3, J=0.65, dzz=0.25, h=(0.40, -0.50, 0.15)):
    d = 2 ** n
    H = np.zeros((d, d), dtype=complex)
    for i in range(n - 1):
        H += J * (er.two_site(er.PX, i, er.PX, i + 1, n)
                  + er.two_site(er.PY, i, er.PY, i + 1, n))
        H += dzz * er.two_site(er.PZ, i, er.PZ, i + 1, n)
    for i, hi in enumerate(h):
        H += hi * er.op_on(er.PZ, i, n)
    M = sum(er.op_on(er.PZ, i, n) for i in range(n))        # Q = Z0 + Z1 + Z2
    return H, M

def psi_benchmark(n=3, theta=1.3):
    v = np.zeros(2 ** n, dtype=complex)
    v[0], v[1] = np.cos(theta / 2), np.sin(theta / 2)       # cos(0.65)|000> + sin(0.65)|001>
    return v

def main():
    ok = True
    n = 3
    H, M = build_benchmark(n=n)
    comm, gap_full, evals = er.convention_checks(H, M)
    print(f"[check] ||[H,Q]|| = {comm:.2e}   (G0.1 want < 1e-10)")
    print(f"[check] min spectral gap (FULL) = {gap_full:.4f}   (G0.2 want > 1e-3; expected small,"
          f" set by the unpopulated pair near E~0.45, nb §1.4)")
    ok &= comm < 1e-10 and gap_full > 1e-3

    psi = psi_benchmark(n=n)
    evals_d, w, m = er.spectral_data(H, M, psi)
    m_round = np.round(m)
    print(f"[check] labels m_k integer to {np.max(np.abs(m - m_round)):.2e}; "
          f"sum w = {w.sum():.6f}   (G0.9)")
    ok &= np.max(np.abs(m - m_round)) < 1e-8 and abs(w.sum() - 1) < 1e-10

    pop = w > 1e-3
    gap_pop = float(np.min(np.diff(np.sort(evals_d[pop]))))
    sectors = sorted({int(x) for x in m_round[pop]})
    print(f"[bench] populated lines = {int(pop.sum())} (G0.5 want 4); sectors = {sectors} "
          f"(G0.6 want [1, 3]); min POPULATED gap = {gap_pop:.4f}")
    for E_k, w_k, m_k in sorted(zip(evals_d[pop], w[pop], m_round[pop])):
        print(f"[bench]   E = {E_k:+.6f}   w = {w_k:.6f}   q = {int(m_k):+d}")
    ok &= int(pop.sum()) == 4 and sectors == [1, 3]

    c2, s2 = np.cos(0.65) ** 2, np.sin(0.65) ** 2
    H_expect, Q_expect = 0.55 * c2 - 0.75 * s2, 1 + 2 * c2      # §2 closed forms
    H_num = float(np.real(psi.conj() @ H @ psi))
    Q_num = float(np.real(psi.conj() @ M @ psi))
    print(f"[bench] <H> = {H_num:+.6f} vs closed form {H_expect:+.6f}; "
          f"<Q> = {Q_num:+.6f} vs {Q_expect:+.6f}   (G0.7 want < 1e-12)")
    ok &= abs(H_num - H_expect) < 1e-12 and abs(Q_num - Q_expect) < 1e-12

    dt, N, Emax = er.suggest_grid(evals_d, gap_pop)             # POPULATED gap (§2 D2/D3)
    N = min(N, 4096)
    tgrid = dt * np.arange(N)
    print(f"[grid ] Emax={Emax:.3f}  dt={dt:.4f} (Nyquist margin 4x)  N={N}  T={dt*N:.1f}  "
          f"Hann lobe={8*np.pi/(dt*N):.4f} < gap {gap_pop:.4f}")
    print(f"[bench] FROZEN grid dt=0.2 N=64 T_max=12.6: Nyquist pi/dt={np.pi/0.2:.3f} vs "
          f"Emax {Emax:.3f}; 2pi/T_max={2*np.pi/12.6:.3f} and Hann half-lobe "
          f"{4*np.pi/12.6:.3f} vs populated gap {gap_pop:.4f}")
    ok &= Emax < np.pi / 0.2                                    # G0.8 no aliasing on frozen grid

    g1, gM = er.g_signals(tgrid, evals_d, w, m)
    ok &= abs(g1[0] - 1.0) < 1e-12 and abs(gM[0] - Q_expect) < 1e-12    # G0.7 at t = 0
    coarse = tgrid[:: max(1, N // 64)][:64]
    g1_rk, gM_rk = er.rk4_g1_gM(H, M, psi, coarse)
    g1_sp, gM_sp = er.g_signals(coarse, evals_d, w, m)
    e1 = float(np.max(np.abs(g1_rk - g1_sp)))
    eM = float(np.max(np.abs(gM_rk - gM_sp)))
    print(f"[xchk ] spectral-sum vs RK4:  max|dg1|={e1:.2e}  max|dgM|={eM:.2e}   "
          f"(G0.3 want < 1e-6)")
    ok &= e1 < 1e-6 and eM < 1e-6

    peaks = er.recover(g1, gM, tgrid)
    truth = sorted(zip(evals_d[pop], w[pop], m_round[pop]))
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
    print(f"[recov] matched {matched}/{len(truth)}  max|dE|={err_E:.2e}  "
          f"max|dw|={err_w:.2e}  max|dm|={err_m:.2e}   (G0.4)")
    ok &= matched == len(truth) and err_E < 5e-3 and err_w < 2e-2 and err_m < 0.1

    print("GATE0", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
