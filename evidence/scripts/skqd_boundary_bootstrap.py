"""FOLLOW-UP TO R047: is the Delta/J localisation boundary a real trend, or single-seed noise?

R047's control sweep (skqd_scaling.py sec.3) measured "top-M subspace needed for 1% error"
at 5 Delta/J values, n=12 sector (dim 924), from ONE seed (RNG 2026). The row says so itself:
"single-seed (RNG 2026), no bootstrap -- the qualitative trend is monotone across ... 5
Delta/J values" -- honest about the gap, not a fix for it. House rule wants >=10 seeds and
bootstrap 95% CIs on stats claims.

The sector Hamiltonian and its eigendecomposition are DETERMINISTIC (no RNG) -- diagonalised
once per Delta/J point, exactly as in skqd_scaling.py. Only the sampling step (which
configurations the sampler happens to observe from the time-evolved reference state) is
stochastic, so that is what gets repeated across seeds. Same protocol, same sector, same
target (1% relative energy error at n=12), same 5 Delta/J values as R047's control -- only
the number of independent draws changes.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json
sys.path.insert(0, REPO)

import numpy as np
from itertools import combinations

J, DELTA = 0.65, 0.25
FIELDS = [0.40, -0.50, 0.15, 0.20, -0.30, 0.10, 0.25, -0.15,
          0.35, -0.20, 0.05, 0.30, -0.10, 0.22]        # identical to skqd_scaling.py
N_SEEDS = 20
BOOT = 10000
N_C, K_C = 12, 6
RATIOS = (DELTA / J, 1.0, 2.0, 5.0, 10.0)
M_GRID = (25, 50, 100, 150, 200, 300, 400, 600, 800)


def sector(n, k):
    out = []
    for pos in combinations(range(n), k):
        m = 0
        for p in pos:
            m |= (1 << p)
        out.append(m)
    out.sort()
    return out, {m: i for i, m in enumerate(out)}


basis_c, index_c = sector(N_C, K_C)
d_c = len(basis_c)


def build_Hc(ratio):
    dlt = ratio * J
    Hc = np.zeros((d_c, d_c))
    for a, m in enumerate(basis_c):
        z = [1 - 2 * ((m >> j) & 1) for j in range(N_C)]
        Hc[a, a] = (sum(dlt * z[i] * z[i + 1] for i in range(N_C - 1))
                    + sum(FIELDS[i] * z[i] for i in range(N_C)))
        for i in range(N_C - 1):
            if ((m >> i) & 1) != ((m >> (i + 1)) & 1):
                Hc[index_c[m ^ (1 << i) ^ (1 << (i + 1))], a] += 2 * J
    return Hc


def dim_needed_one_draw(rng, ev, evec, e0, p):
    counts = np.zeros(d_c)
    for t in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0):
        amp = evec @ (np.exp(-1j * ev * t) * (evec.T @ p["psi0"]))
        pr = np.abs(amp) ** 2
        pr /= pr.sum()
        i2, c = np.unique(rng.choice(d_c, size=3000, p=pr), return_counts=True)
        counts[i2] += c
    order = np.argsort(counts)[::-1]
    order = order[counts[order] > 0]
    Hc = p["Hc"]
    for M in M_GRID:
        if M > len(order):
            return None
        sub = np.sort(order[:M])
        if abs(float(np.linalg.eigvalsh(Hc[np.ix_(sub, sub)])[0]) - e0) / abs(e0) < 1e-2:
            return M
    return None


def bootstrap_ci(samples, boot=BOOT, seed=2026):
    rng = np.random.default_rng(seed)
    arr = np.array([s for s in samples if s is not None], dtype=float)
    if len(arr) == 0:
        return None
    means = np.array([rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(boot)])
    lo, hi = np.percentile(means, [2.5, 97.5])
    return dict(mean=float(arr.mean()), std=float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
                ci95=[float(lo), float(hi)], n_valid=int(len(arr)), n_seeds=N_SEEDS)


neel = 0
for j in range(0, N_C, 2):
    neel |= (1 << j)

print("=" * 78)
print(f"Delta/J boundary, n=12 sector (dim {d_c}), {N_SEEDS} seeds per point, "
      f"{BOOT}x bootstrap on the mean")
print("=" * 78)
print(f"{'Delta/J':>8}{'mean dim':>12}{'std':>8}{'95% CI':>20}{'frac (mean)':>13}")
print("-" * 78)

ROWS = []
for ratio in RATIOS:
    Hc = build_Hc(ratio)
    ev, evec = np.linalg.eigh(Hc)
    e0 = float(ev[0])
    g = evec[:, 0]
    w = np.sort(np.abs(g) ** 2)[::-1]
    n90 = int(np.searchsorted(np.cumsum(w), 0.90)) + 1
    psi0 = np.zeros(d_c)
    psi0[index_c[neel]] = 1.0
    p = dict(Hc=Hc, psi0=psi0)

    draws = []
    for seed in range(N_SEEDS):
        rng = np.random.default_rng(1000 + seed)
        draws.append(dim_needed_one_draw(rng, ev, evec, e0, p))

    stats = bootstrap_ci(draws)
    ci_str = f"[{stats['ci95'][0]:.1f}, {stats['ci95'][1]:.1f}]" if stats else "n/a"
    print(f"{ratio:>8.2f}{stats['mean']:>12.1f}{stats['std']:>8.1f}{ci_str:>20}"
          f"{stats['mean']/d_c:>13.3f}")
    ROWS.append(dict(delta_over_J=float(ratio), ground_90pct=n90, ground_90pct_frac=n90 / d_c,
                      draws=draws, stats=stats))

print()
print("R047's single-seed point estimates (for comparison): Delta/J=0.38 -> 86.6%; "
      "1.00 -> 43.3%; 2.00 -> 16.2%; 5.00 -> 2.7%; 10.00 -> 2.7%")
means_frac = [r["stats"]["mean"] / d_c for r in ROWS]
monotone = all(means_frac[i] >= means_frac[i + 1] - 1e-9 for i in range(len(means_frac) - 1))
print(f"20-seed means monotone decreasing in Delta/J: {monotone}")

with open(os.path.join(REPO, "evidence/skqd_boundary_bootstrap.json"), "w") as fh:
    json.dump(dict(n_seeds=N_SEEDS, boot=BOOT, n_sector=N_C, k_sector=K_C, dim=d_c,
                    rows=ROWS), fh, indent=2)
print("wrote evidence/skqd_boundary_bootstrap.json")
