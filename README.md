# Shadow-Enhanced Hadamard Test — Qiskit Hackathon 2026, Topic 5

A standard Hadamard test measures one ancilla qubit and **throws the system register away**.
This project keeps it. By measuring those discarded qubits in randomly chosen bases they
become a *classical shadow*, so a single set of shots yields not just the interference
signal χ(t) but the system's observables and — the point of the whole exercise — a
**symmetry label for every recovered energy level**. We implement the protocol of
Faehrmann, Eisert & Kueng (PRL **135**, 150603, 2025) end to end on a 3-qubit XXZ benchmark,
validate every estimator against exact references, quantify what the extra information
costs, and characterise where the method breaks — on simulators and on three real IBM
devices.

**Every number in this repository traces to the command that produced it** (see
[`RESULTS.md`](RESULTS.md) and [`EVIDENCE.md`](EVIDENCE.md)). That includes the numbers we
got wrong and retracted.

---

## 5-minute quickstart (reproduces the headline figure from saved data)

No long reruns, no quantum hardware, no IBM account needed.

```bash
git clone <this-repo> && cd 2026
python -m venv .venv && source .venv/bin/activate
pip install "qiskit==2.5.1" "qiskit-aer==0.17.2" "numpy<2.5" "scipy<1.18" \
            matplotlib pylatexenc

# the headline result, recomputed from the 12 saved per-seed CSVs in data/
python -c "
import json; d = json.load(open('data/multiseed_summary.json'))
print(f\"{'exact E':>9} {'recovered':>20} {'exact q':>8} {'recovered q':>16}  seeds OK\")
for r in d['rows']:
    print(f\"{r['E_exact']:+9.4f} {r['E_mean']:+11.4f} +- {r['E_sd']:.4f} \"
          f\"{r['q_exact']:+8d} {r['q_mean']:+11.3f} +- {r['q_sd']:.3f}  {r['labels_ok']}/{r['n_seeds']}\")
"
```

Expected output: four energy levels recovered to ~0.006, and **12/12 seeds label every
level correctly**.

Then open [`figures/07_symmetry_resolved_spectrum.png`](figures/07_symmetry_resolved_spectrum.png)
— the money plot. Grey is what a conventional Hadamard test gives you; the coloured stems
are our reconstruction, coloured by the symmetry sector recovered from the recycled data.

**Full rerun** (~10 min, all 56 checkpoints, regenerates every figure):

```bash
pip install "ipykernel>=6.29,<7" nbconvert==7.17.1 nbclient==0.11.0
python -m ipykernel install --user --name qh26-t5
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=qh26-t5 shadow_hadamard_challenge_PARTICIPANT.ipynb
```

> **Environment note (real, cost us time):** `requirements.txt` pins `numpy==2.5.2` /
> `scipy==1.18.0`, which need **Python 3.12**. On 3.11 the install fails outright. The
> relaxed pins above are verified-good on 3.11 with all 56 checkpoints passing
> (logged as BUGLOG B01).

---

## Figure gallery

| figure | what it shows |
|---|---|
| [`07_symmetry_resolved_spectrum.png`](figures/07_symmetry_resolved_spectrum.png) | **Money plot** — recovered spectrum, colour = symmetry sector from the recycled register |
| [`06_fundamental_validation.png`](figures/06_fundamental_validation.png) | Four-panel validation: χ quadratures, joint observable, N^(−1/2) scaling |
| [`06_conservation.png`](figures/06_conservation.png) | Conserved ⟨Q⟩ flat in time vs non-conserved ⟨Z₀⟩ drifting — the pooling rule, shown |
| [`07_chi_vs_chiQ_spectra.png`](figures/07_chi_vs_chiQ_spectra.png) | χ vs χ_Q side by side — the ratio at each peak *is* the quantum number |
| [`09_noise_comparison.png`](figures/09_noise_comparison.png) | Noise damps amplitude; peak positions survive, weights do not |
| [`08_krylov_regularisation.png`](figures/08_krylov_regularisation.png) | Krylov GEVP instability — an honest look at an ill-conditioned method |
| [`03_circuit_phi_0_real.png`](figures/03_circuit_phi_0_real.png) | The circuit, real quadrature |

---

## What's here

| path | what it is |
|---|---|
| `shadow_hadamard_challenge_PARTICIPANT.ipynb` | The graded notebook — **56/56 checkpoints pass**, outputs embedded |
| `RESULTS.md` | Every reported number, with its producing command |
| `EVIDENCE.md` | Row-to-artifact index — how to verify each result |
| `BUGLOG.md` | Bugs found, root causes, prevention rules — including our own retractions |
| `CONVENTIONS.md` | Frozen conventions (operators, signs, endianness, shot budget) |
| `EXPLAINER.md` | Plain-language description for non-specialists |
| `hardware_run.py` | Submit/fetch hardware jobs on any IBM backend (3 commands) |
| `layout_search.py` | Pick the best-calibrated physical qubit window before submitting |
| `HANDOVER.md` | Instructions for collaborators with hardware we can't reach |
| `evidence/`, `data/`, `real_machine/` | Producing scripts, per-seed CSVs, raw hardware job dumps |
| `deck/` | Slides + speaker script |

---

## Headline results

- **56/56 checkpoints pass** on the graded notebook, zero hard failures.
- **All four energy levels** recovered with **every symmetry label correct**, reproducibly
  across **12/12 independent seeds**. [R012, R013, R019]
- **Honest cost accounting:** the shadow route replaces **13 dedicated experiments** at a
  measured **1.07× variance premium** — and the 3^w variance model predicts the observed
  error bars to within 2%. [R021, R029]
- **Real hardware:** signal survival **0.878** on the frozen benchmark once the circuit is
  shallow enough, and a genuine random-basis shadow ensemble recovering a valid ⟨Q⟩ at
  **0.957 survival**. Depth beats device choice by 2.4–4.6× vs 1.1–2.1×. [R018, R023]
- **A self-validating decoherence witness** that needs no exact diagonalisation, so it
  remains usable where classical verification is impossible. [R033]

---

## Reproducibility and honesty commitments

- All Part A/B results derive from **one shared record set** — 128 settings × 2000 shots =
  **256,000 shots**, seed 2026. Side studies (12-seed reproducibility, scaling, noise,
  ablations, hardware) are declared separately and never mixed into headline numbers.
- Hardware results support **robustness claims only** — never a headline number.
- Statistical claims rest on ≥10 seeds with bootstrap CIs; the bootstrap itself was
  validated against real seed-to-seed spread. [R019, R020]
- We make **no claims of outperforming classical computation.** The system is 3 qubits; a
  laptop diagonalises it instantly. It is small *on purpose*, so every estimate can be
  graded against an exact answer.
- Retracted numbers stay visible with their corrections (see R008 and BUGLOG B04).

## Citing

If this is useful to you, please cite the underlying method:

> P. Faehrmann, J. Eisert, R. Kueng, *In the Shadow of the Hadamard Test*,
> Phys. Rev. Lett. **135**, 150603 (2025). arXiv:2505.15913

and link back to this repository for the implementation and characterisation.

## License

MIT — see [`LICENSE`](LICENSE).

`packing.py` in the repository root is **third-party** (© Jiun-Cheng Jiang, Apache-2.0), is
**not used by any code here**, and is not covered by the MIT license above — see R024.
