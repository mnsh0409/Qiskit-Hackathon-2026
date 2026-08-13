# EVIDENCE.md — row-to-artifact map for the C4 numbers audit

Every `R###` row in RESULTS.md, and where to verify it. C4's brief is to trace each claim
to a RESULTS row **or raw output**; this file is the index that makes that a lookup rather
than a search.

Written because several rows previously cited `scratchpad/...` paths that existed only in a
session-local temp directory and would have audited as UNSUPPORTED. Those artifacts are now
committed under `evidence/`.

## How to verify, in order of preference

1. **Re-execute** — the strongest check. `shadow_hadamard_challenge_PARTICIPANT.ipynb` is
   committed *with its outputs*, and re-running it end to end reproduces every Part A/B
   number (56/56 checkpoints, seed 2026, deterministic).
2. **Read the committed output** — `run_summary.json`, the notebook's own output cells,
   `data/*.csv`, `evidence/*.json`.
3. **Read the executed notebook of the side study** — `evidence/executed/*.ipynb`.
4. **Re-run the producing script** — `evidence/scripts/*.py`.

## Row map

| row | claim | primary evidence | re-runnable by |
|---|---|---|---|
| R001 | Gate 0 PASS | — (run it) | `python scripts/gate0_benchmark.py` |
| R002 | Checkpoint 2, 8 asserts | notebook cell 16 output | notebook re-run |
| R003 | Checkpoint 3a, Challenge 1 | notebook cell 24 output | notebook re-run |
| R004 | Checkpoint 3b, sign conventions | notebook cell 26 output | notebook re-run |
| R005 | Checkpoint 3c, measurement order | notebook cells 29/31 output | notebook re-run |
| R006 | Checkpoint 4, Challenge 3 | notebook cells 34/36 output | notebook re-run |
| R007 | Checkpoint 5, Challenge 4 | notebook cells 41/43 output | notebook re-run |
| R008 | hardware job, survival 0.179 + **withdrawn `<Q>` line (B04)** | `hardware_jobs.json`; `evidence/executed/executed_hw_analysis.ipynb` | `python hardware_run.py --fetch d9u95vs98n5s7392iao0` (live, reproduces 0.179) |
| R009 | full sweep, 3456 circuits / 256,000 shots | `run_summary.json`; notebook cell 48 | notebook re-run |
| R010 | Checkpoint 6, 8/8 | `run_summary.json`; notebook cells 51–59 | notebook re-run |
| R011 | Challenge 7 DFT baseline | notebook cell 65 output | notebook re-run |
| R012 | Challenge 8 matrix pencil | notebook cell 70 output | notebook re-run |
| R013 | Checkpoint 7, 8/8 + bootstrap sds | notebook cells 73–80 output | notebook re-run |
| R014 | Challenge 11 noise, damping 0.342 | notebook cells 91/93 output | notebook re-run |
| R016 | Challenge 10 Krylov, E0 −1.5349 | notebook cells 85/87 output | notebook re-run |
| R017 | **EXPLORATORY/CONFOUNDED** label survival | `evidence/executed/executed_robustness2.ipynb` | `evidence/scripts/robustness_item2.py` |
| R018 | hardware 2×2, exact+marrakesh 0.822 | `hardware_jobs.json`; `evidence/hw_2x2_jobs.json` | `python hardware_run.py --fetch <id>` |
| R019 | 12-seed study | `data/multiseed_summary.json`; `data/*.csv` (24 files); `evidence/executed/executed_seedsweep.ipynb` | `evidence/scripts/seed_sweep.py` |
| R020 | bootstrap validation ratios | same as R019 | recompute from R013 + R019 sds |
| R021 | ablation A: equivalence, 2×2 grid, cost | `evidence/ablation_results.json`; `evidence/executed/executed_ablation_ab.ipynb` | `evidence/scripts/ablation_a_b.py` |
| R022 | ablation B: resolution failure boundary | same as R021 | same |
| R023 | 2-site hardware, **pending** | `hardware_jobs.json`; ideal-sim validation in `evidence/scripts/validate_2site.py` | `python hardware_run.py --fetch d9uk99k98n5s7392vhsg` |
| R024 | `packing.py` unusable, third-party | — | `python -c "import packing"` (fails) |
| R025 | transpile cost n=3 vs n=4, corrected | `evidence/scripts/transpile_cost_n3_n4.py` output (cross-checks itself against R018's 101) | `python evidence/scripts/transpile_cost_n3_n4.py` |
| R026 | 4-site hardware, **pending** | `hardware_jobs.json`; ideal-sim validation in `evidence/scripts/validate_4site.py` | `python hardware_run.py --fetch d9ultm0u5hac73ahd9kg` |
| R027 | rank selection (honest negative result) | `evidence/going_further_trio.json`; `evidence/executed/executed_going_further.ipynb` | `evidence/scripts/going_further_trio.py` |
| R028 | measured chi/chi_Q correlation + correlated bootstrap | same as R027 | same |
| R029 | variance budgeting, 3^w rule vs measured | same as R027 | same |
| R030 | QPE ablation, 4/4 lines, no labels at any cost | `evidence/qpe_ablation_result.json` | `python evidence/scripts/qpe_ablation.py` |
| R031 | teammate's 6 real-hardware jobs (incl. ibm_miami), survival + phase-error finding | `real_machine/*.json` (raw job dumps, credential-checked); `evidence/real_machine_analysis.json` | `python evidence/scripts/load_real_machine_results.py` |
| R032 | Track C eigenstate detective: calibration curve + detection power vs shots | `evidence/track_c_result.json`; `evidence/track_c_console_output.txt` | `python evidence/scripts/track_c_eigenstate_detective.py` (~7 min) |
| R033 | Track E consistency witness (3-leg validation) + product-state fidelity | `evidence/track_e_result.json`; `evidence/track_e_console_output.txt` | `python evidence/scripts/track_e_consistency_witness.py` (~4 min) |

## Derived quantities C4 should independently recompute

C4's brief (b) requires re-deriving ratios and CI widths from raw numbers. The ones that matter:

- **R020 bootstrap ratios** — across-seed sd (R019) ÷ bootstrap sd (R013), per line. Both
  sets of sds are printed in their rows.
- **R018 depth factor** — 0.822 ÷ 0.179 = 4.6× on marrakesh only (kingston's Trotter arm is
  still pending, so this is a single-device comparison so far, not "both devices").
- **R021 variance cost factor** — 0.1012 ÷ 0.0949 = 1.07×. The denominator formula is
  `sqrt(terms² / SHOTS) * sqrt(2)` (evidence/scripts/ablation_a_b.py) — 3 Pauli terms sharing
  2000 shots/quadrature, per-shot variance ≤ 1, **times an explicit sqrt(2) for combining
  both quadratures** (matching how the measured side is computed via `hypot(sem_re, sem_im)`).
  Omitting the sqrt(2) gives ≈0.067, a ~40% miss — C4 audit caught this ambiguity; the
  formula above is the corrected, complete description.
- **R014 vs R008 damping** — 0.342 simulated vs 0.179 measured. Different circuits at
  different budgets; the comparison is qualitative and is labelled as such.
- **95% CIs** — CONVENTIONS §7 fixes these as ±1.96·σ. R019 tabulates both σ and CI; check
  they are consistent.

## Known weak points — flag these before C4 does

1. **R017 is confounded** and marked NOT SLIDE-READY. The ideal-Trotter baseline it compares
   against is itself broken on the reduced grid (misses 2 of 4 lines before any noise).
   Recommendation: do not cite it; either re-run at Part-B fidelity or drop it.
2. **R008's `<Q>` line was withdrawn** (BUGLOG B04) — the number was measuring 3⟨Z₂⟩, not
   ⟨Q⟩. If any draft slide cites a hardware ⟨Q⟩, it is citing a retracted number.
3. **Headline budget vs side studies.** All reported Part A/B numbers come from ONE
   256,000-shot record set (CONVENTIONS §5). The 12-seed study (3,072,000 shots), scaling
   study, noise study and ablation arms are *separately declared*. Any slide saying
   "we used N shots" must say which N it means.
4. **Hardware now spans 8 jobs** across the frozen benchmark, a 2-site side model, and a
   4-site side model (R008, R018 x3, R023, R026 + 2 accidental/incidental submissions in
   BUGLOG B05). All of it supports robustness claims only, never a Part A/B headline — the
   Part A/B numbers are 100% simulator (R009-R022).
5. **Going-further: 4 of 18 items have real, committed results** (R027 rank selection —
   honest negative, the derived criterion does NOT beat the magic number here; R028
   correlation/correlated bootstrap — clean, ~20% tighter q uncertainty; R029 variance
   budgeting — clean, within 2%; and the hardware-instance item, done twice over with 2site
   and 4site). One item (R017, label survival under noise) was attempted and found
   confounded — do not cite it. The remaining ~13 items were not attempted. Any claim of
   "we explored the extensions" must be scoped exactly to R027-R029 plus the hardware items,
   not the full list.

## Banned-language checklist (rubric.md)

- "quantum advantage" — must not appear
- uncosted "for free" — the shadow route costs a measured 1.07× variance premium (R021) and
  ≤2 extra 1q gates per system qubit; say so wherever "no extra circuits" appears
- causal claims from single runs — R008/R018 arms are single runs each
- "hardware" — permitted, since the go/no-go passed with a completed job (R008)
