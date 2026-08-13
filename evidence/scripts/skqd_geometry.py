"""DOES THE SKQD BOUNDARY MOVE IN 2D? Same Hilbert space, different connectivity.

R047 found that SKQD's advantage on our benchmark is governed by localisation: it needs
2.7% of the charge sector when Delta/J = 5 (Ising-like, localised) and 86.6% at our
benchmark's Delta/J = 0.38 (hopping-dominated, delocalised).

That was measured on a 1D open chain. Connectivity is the other knob on delocalisation, so
the natural question is whether the boundary moves in 2D. This compares:

    1D chain   12 sites, 11 nearest-neighbour bonds
    2D grid    3 x 4 = 12 sites, 17 nearest-neighbour bonds

Same site count, same conserved charge, therefore the SAME sector dimension C(12,6) = 924 --
so any difference is connectivity alone, not Hilbert-space size. More bonds means more
hopping paths, which should delocalise the ground state further and make SKQD worse. Stated
before running so the result can contradict it.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, json
sys.path.insert(0, REPO)

import numpy as np
from itertools import combinations

J = 0.65
FIELDS = [0.40, -0.50, 0.15, 0.20, -0.30, 0.10, 0.25, -0.15,
          0.35, -0.20, 0.05, 0.30, -0.10, 0.22]
RNG = np.random.default_rng(2026)
TIMES = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0)
N, K = 12, 6


def chain_bonds(n):
    return [(i, i + 1) for i in range(n - 1)]


def grid_bonds(rows, cols):
    b = []
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            if c + 1 < cols:
                b.append((i, r * cols + c + 1))
            if r + 1 < rows:
                b.append((i, (r + 1) * cols + c))
    return b


def sector(n, k):
    out = []
    for pos in combinations(range(n), k):
        m = 0
        for p in pos:
            m |= (1 << p)
        out.append(m)
    out.sort()
    return out, {m: i for i, m in enumerate(out)}


def build_H(n, basis, index, bonds, delta):
    """Same XXZ form as the benchmark, but on an arbitrary bond list."""
    d = len(basis)
    H = np.zeros((d, d))
    for a, m in enumerate(basis):
        z = [1 - 2 * ((m >> j) & 1) for j in range(n)]
        H[a, a] = (sum(delta * z[i] * z[j] for i, j in bonds)
                   + sum(FIELDS[i] * z[i] for i in range(n)))
        for i, j in bonds:
            if ((m >> i) & 1) != ((m >> j) & 1):
                H[index[m ^ (1 << i) ^ (1 << j)], a] += 2 * J
    return H


def skqd(n, basis, index, H, shots=3000):
    """Top-M-by-frequency SKQD; returns the premise (ground concentration) and the
    subspace fraction needed for 1% relative energy error.

    REFERENCE: the lowest-diagonal configuration of H itself, i.e. the classical Ising
    ground state on whatever bond list was passed. This is geometry-agnostic and costs no
    diagonalisation (it is the spin-chain analogue of Hartree-Fock). A first version
    hard-coded a 1D Neel pattern, which on a 3x4 grid is NOT the antiferromagnetic
    configuration -- the sampler then never visited the true ground configuration and 2D
    looked catastrophically worse for a reason that was entirely an artefact of the
    reference, not of the geometry."""
    d = len(basis)
    ev, evec = np.linalg.eigh(H)
    e0 = float(ev[0]); g = evec[:, 0]
    w = np.sort(np.abs(g) ** 2)[::-1]
    n90 = int(np.searchsorted(np.cumsum(w), 0.90)) + 1
    ref = int(np.argmin(np.diag(H)))
    psi0 = np.zeros(d); psi0[ref] = 1.0
    counts = np.zeros(d)
    for t in TIMES:
        amp = evec @ (np.exp(-1j * ev * t) * (evec.T @ psi0))
        p = np.abs(amp) ** 2; p /= p.sum()
        i2, c = np.unique(RNG.choice(d, size=shots, p=p), return_counts=True)
        counts[i2] += c
    order = np.argsort(counts)[::-1]; order = order[counts[order] > 0]
    hit = None
    for M in (25, 50, 100, 150, 200, 300, 400, 600, 800):
        if M > len(order):
            break
        sub = np.sort(order[:M])
        if abs(float(np.linalg.eigvalsh(H[np.ix_(sub, sub)])[0]) - e0) / abs(e0) < 1e-2:
            hit = M; break
    return dict(ground_90pct=n90, ground_90pct_frac=n90 / d,
                dim_needed=hit, frac=(hit / d) if hit else None, e0=e0)


BASIS, INDEX = sector(N, K)
D = len(BASIS)
GEOM = {"1D chain (11 bonds)": chain_bonds(N),
        "2D grid 3x4 (17 bonds)": grid_bonds(3, 4)}

print("=" * 78)
print(f"SKQD vs GEOMETRY -- {N} sites, sector C({N},{K}) = {D} in both cases")
print("=" * 78)
print("Same Hilbert space, same charge, same protocol. Only the bond list differs.\n")
print(f"{'Delta/J':>8}  {'geometry':>24}{'90% of ground on':>20}"
      f"{'top-M for 1%':>14}{'fraction':>11}")
print("-" * 78)
OUT = []
for ratio in (0.38, 1.0, 2.0, 5.0):
    for name, bonds in GEOM.items():
        H = build_H(N, BASIS, INDEX, bonds, ratio * J)
        r = skqd(N, BASIS, INDEX, H)
        hs = f"{r['dim_needed']}" if r["dim_needed"] else ">800"
        fs = f"{r['frac']:.1%}" if r["frac"] else "--"
        print(f"{ratio:>8.2f}  {name:>24}{r['ground_90pct']:>14} "
              f"({r['ground_90pct_frac']:>4.0%}){hs:>14}{fs:>11}")
        OUT.append(dict(delta_over_J=float(ratio), geometry=name, bonds=len(bonds), **r))
    print()

print("=" * 78)
print("READING IT")
print("=" * 78)
for ratio in (0.38, 5.0):
    a = next(o for o in OUT if o["delta_over_J"] == ratio and o["geometry"].startswith("1D"))
    b = next(o for o in OUT if o["delta_over_J"] == ratio and o["geometry"].startswith("2D"))
    fa = f"{a['frac']:.1%}" if a["frac"] else ">86.6%"
    fb = f"{b['frac']:.1%}" if b["frac"] else ">86.6%"
    print(f"  Delta/J = {ratio:.2f}:  1D needs {fa}, 2D needs {fb}   "
          f"(ground spread over {a['ground_90pct_frac']:.0%} vs {b['ground_90pct_frac']:.0%})")
print()

with open(os.path.join(REPO, "evidence/skqd_geometry.json"), "w") as fh:
    json.dump(dict(n=N, k=K, sector_dim=D, rows=OUT), fh, indent=2)
print("\nwrote evidence/skqd_geometry.json")
