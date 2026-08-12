"""spectral.py — Advanced-track analyzer for Topic 5.

Consumes measured signals only (never re-derives estimators):
  g1(t) = <psi0|U(t)|psi0>   and   gM(t) = <psi0| M U(t) |psi0>
saved per seed as CSV with header  t,re,im  (schema in CONVENTIONS.md).

Produces the symmetry-resolved spectrum: for each resolved peak,
  E_k   (position),  |c_k|^2  (Hann-gain-corrected height of g1 peak),
  m_k   (Re[S_M/S_1] at the peak — same window factor cancels in the ratio),
each with bootstrap 95% CIs over seed resamples.

Method notes (why, so you can defend it to a judge):
  * dense DTFT on an explicit omega grid instead of FFT: no bin/sign/ordering
    bookkeeping to get wrong under deadline pressure; N is tiny, cost is nil.
  * Hann window: -31 dB sidelobes so small peaks are not fake; a sidelobe guard
    drops "peaks" within a few lobes of a much taller one.
  * bootstrap over SEEDS (the independent unit of repetition), percentile CIs.

CLI:
  python spectral.py --selftest
  python spectral.py 'data/g1_*.csv' 'data/gM_*.csv' [--boot 200] [--json out.json]
"""
from __future__ import annotations

import glob
import json
import sys

import numpy as np


# ------------------------------------------------------------------ core ----

def dtft(g, tgrid, wgrid, window=True):
    h = np.hanning(len(tgrid)) if window else np.ones(len(tgrid))
    ker = np.exp(1j * np.outer(wgrid, tgrid))
    return ker @ (h * g), h


def _refine_quadratic(y, i, wgrid):
    if i == 0 or i == len(y) - 1:
        return wgrid[i], y[i]
    y0, y1, y2 = y[i - 1], y[i], y[i + 1]
    denom = (y0 - 2 * y1 + y2)
    if abs(denom) < 1e-30:
        return wgrid[i], y1
    delta = 0.5 * (y0 - y2) / denom
    return wgrid[i] + delta * (wgrid[1] - wgrid[0]), y1 - 0.25 * (y0 - y2) * delta


def find_peaks(mag, wgrid, rel_thresh, min_sep):
    thr = rel_thresh * mag.max()
    idx = [i for i in range(1, len(mag) - 1)
           if mag[i] >= thr and mag[i] >= mag[i - 1] and mag[i] > mag[i + 1]]
    idx.sort(key=lambda i: -mag[i])
    kept = []
    for i in idx:
        if all(abs(wgrid[i] - wgrid[j]) >= min_sep for j in kept):
            kept.append(i)
    return sorted(kept)


def recover(g1, gM, tgrid, wgrid=None, rel_thresh=0.05):
    """One-shot recovery from a single (e.g. seed-mean) pair of signals."""
    T = tgrid[-1] - tgrid[0]
    lobe = 8 * np.pi / T
    if wgrid is None:
        span = np.pi / (tgrid[1] - tgrid[0])
        wgrid = np.linspace(-span, span, 8192)
    S1, h = dtft(g1, tgrid, wgrid)
    SM, _ = dtft(gM, tgrid, wgrid)
    mag = np.abs(S1)
    idx = find_peaks(mag, wgrid, rel_thresh, min_sep=0.6 * lobe)
    idx = [i for i in idx
           if not any(abs(wgrid[i] - wgrid[j]) < 4 * lobe and mag[i] < 0.05 * mag[j]
                      for j in idx if j != i)]
    out = []
    for i in idx:
        E, amp = _refine_quadratic(mag, i, wgrid)
        j = int(np.argmin(np.abs(wgrid - E)))
        out.append({"E": float(E),
                    "weight": float(amp / h.sum()),
                    "m": float(np.real(SM[j] / S1[j]))})
    return out, lobe


def analyze(tgrid, G1, GM, n_boot=200, rel_thresh=0.05, seed=0):
    """G1, GM: complex arrays [n_seeds, n_t]. Returns list of peak dicts with CIs."""
    rng = np.random.default_rng(seed)
    point, lobe = recover(G1.mean(axis=0), GM.mean(axis=0), tgrid,
                          rel_thresh=rel_thresh)
    samples = [{"E": [], "weight": [], "m": []} for _ in point]
    S = G1.shape[0]
    for _ in range(n_boot):
        pick = rng.integers(0, S, S)
        pk, _ = recover(G1[pick].mean(axis=0), GM[pick].mean(axis=0), tgrid,
                        rel_thresh=rel_thresh)
        for k, p in enumerate(point):
            near = [q for q in pk if abs(q["E"] - p["E"]) < 1.5 * lobe]
            if near:
                q = min(near, key=lambda q: abs(q["E"] - p["E"]))
                for key in ("E", "weight", "m"):
                    samples[k][key].append(q[key])
    results = []
    for p, s in zip(point, samples):
        row = dict(p)
        row["presence"] = len(s["E"]) / n_boot
        for key in ("E", "weight", "m"):
            if s[key]:
                lo, hi = np.percentile(s[key], [2.5, 97.5])
                row[f"{key}_ci"] = (float(lo), float(hi))
            else:
                row[f"{key}_ci"] = (float("nan"), float("nan"))
        row["m_label"] = int(round(row["m"]))
        results.append(row)
    return results


# ------------------------------------------------------------------- I/O ----

def save_signal_csv(path, tgrid, g):
    np.savetxt(path, np.column_stack([tgrid, g.real, g.imag]),
               delimiter=",", header="t,re,im", comments="")


def load_signal_csvs(pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"no files match {pattern!r}")
    tgrid = None
    rows = []
    for f in files:
        arr = np.loadtxt(f, delimiter=",", skiprows=1)
        if tgrid is None:
            tgrid = arr[:, 0]
        elif not np.allclose(tgrid, arr[:, 0]):
            raise ValueError(f"time grid mismatch in {f}")
        rows.append(arr[:, 1] + 1j * arr[:, 2])
    return tgrid, np.array(rows)


def print_table(results):
    print(f"{'E':>10} {'95% CI':>22} {'weight':>8} {'95% CI':>18} "
          f"{'m':>7} {'label':>5} {'presence':>8}")
    for r in results:
        print(f"{r['E']:>10.4f} [{r['E_ci'][0]:>9.4f},{r['E_ci'][1]:>9.4f}] "
              f"{r['weight']:>8.4f} [{r['weight_ci'][0]:>7.4f},{r['weight_ci'][1]:>7.4f}] "
              f"{r['m']:>7.3f} {r['m_label']:>5d} {r['presence']:>8.2f}")
        if r["presence"] < 0.6:
            print("           ^ presence < 60% of bootstrap resamples: "
                  "report as unresolved, not as a state")


# -------------------------------------------------------------- self-test ---

def _selftest():
    rng = np.random.default_rng(7)
    E_true = np.array([-1.3, 0.4, 2.1])
    w_true = np.array([0.5, 0.3, 0.2])
    m_true = np.array([-1, 1, 3])
    dt, N, S = 0.25, 96, 12
    tgrid = dt * np.arange(N)
    phase = np.exp(-1j * np.outer(tgrid, E_true))
    g1 = phase @ w_true
    gM = phase @ (w_true * m_true)
    sig = 0.02
    G1 = g1 + sig * (rng.standard_normal((S, N)) + 1j * rng.standard_normal((S, N)))
    GM = gM + 3 * sig * (rng.standard_normal((S, N)) + 1j * rng.standard_normal((S, N)))

    res = analyze(tgrid, G1, GM, n_boot=200)
    print_table(res)
    ok = len(res) == len(E_true)
    for E_t, w_t, m_t in zip(E_true, w_true, m_true):
        r = min(res, key=lambda r: abs(r["E"] - E_t))
        eE, ew = abs(r["E"] - E_t), abs(r["weight"] - w_t)
        in_ci = r["E_ci"][0] - 0.02 <= E_t <= r["E_ci"][1] + 0.02
        print(f"[check] E={E_t:+.2f}: |dE|={eE:.3f} |dw|={ew:.3f} "
              f"label {r['m_label']} (true {m_t}) trueE-in-CI={in_ci} "
              f"presence={r['presence']:.2f}")
        ok &= eE < 0.05 and ew < 0.05 and r["m_label"] == m_t and in_ci
        ok &= r["presence"] > 0.9
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv):
    if not argv or argv[0] == "--selftest":
        return _selftest()
    g1_pat, gM_pat = argv[0], argv[1]
    n_boot = int(argv[argv.index("--boot") + 1]) if "--boot" in argv else 200
    tgrid, G1 = load_signal_csvs(g1_pat)
    _, GM = load_signal_csvs(gM_pat)
    res = analyze(tgrid, G1, GM, n_boot=n_boot)
    print_table(res)
    if "--json" in argv:
        with open(argv[argv.index("--json") + 1], "w") as f:
            json.dump(res, f, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
