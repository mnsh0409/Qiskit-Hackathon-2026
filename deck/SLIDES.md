# Slide deck — Topic 5: Shadow-Enhanced Hadamard Test

**Status: DRAFT for human review.** Every number carries its `R###` source from RESULTS.md.
Slide titles ARE the takeaway sentences (per `deck_arc.md`). Max 3 bullets each.

**Before presenting, a human must fill in:** every `TBD-NAME` (team members, speaking
allocation) and confirm the prior-art claim on slide 8. Nothing else is a placeholder.

**Banned language check applied** (rubric.md): no "quantum advantage"; no uncosted
"for free" — the cost is quantified on slide 7 and referenced wherever the shared-record
claim appears; no causal claims from single hardware runs (slide 6 states the caveat).

---

## Slide 1 — "Every Hadamard test throws away half its data. We recycle it."

*Figure: `figures/03_circuit_phi_0_real.png`*

- The standard Hadamard test measures one ancilla qubit and **discards the system register**.
- Measure that "garbage" in random bases instead and it becomes a classical shadow —
  the same shots now also carry the system's observables.
- We implement this end to end, validate every estimate, and characterise where it breaks.

**Speaker:** TBD-NAME

---

## Slide 2 — "One circuit, one set of shots, seven physical quantities."

*Figure: `figures/03_circuit_phi_0_real.png` (circuit) — consider a 3-box schematic overlay*

- Same record set yields: χ(t), χ_Q(t), χ_H(t), χ_Z0(t), ⟨H⟩, ⟨Q⟩, ⟨Z₀⟩ under ρ^(I)(t).
- Three estimator families: ancilla-only, unweighted shadows, ancilla-weighted shadows.
- **3,456 circuits · 256,000 shots** — one shared record set, not seven experiments. [R009]

**Speaker:** TBD-NAME

---

## Slide 3 — "Every estimator agrees with theory, and the error bars are honest."

*Figure: `figures/06_fundamental_validation.png`*

- **56/56 checkpoints pass**, zero hard failures, zero advisory warnings. [run_summary.json]
- χ(t) rms error **0.0290** vs mean predicted sem **0.0277** — ratio 1.05, so the error bars
  neither over- nor under-state. [R010]
- Shot-noise scaling slope **−0.463** (theory −0.5) → unbiased, statistics-limited. [R010]

**Speaker:** TBD-NAME

---

## Slide 4 — "Conserved quantities come out flat in time — from the very same shots."

*Figure: `figures/06_conservation.png`*

- ⟨H⟩ = **+0.0714 ± 0.0082** (exact +0.0739) and ⟨Q⟩ = **+2.2708 ± 0.0052** (exact +2.2675),
  pooled over all 128 settings. [R010]
- Both are extracted from the *discarded* register of the χ(t) experiment — no extra circuits
  (≤2 extra 1-qubit gates per system qubit), at a variance cost quantified on slide 7.
- Per-time ⟨Q⟩ is flat within 5σ at every one of the 64 time points. [R010]

**Speaker:** TBD-NAME

---

## Slide 5 — MONEY PLOT: "We recover the spectrum *and* label each line by symmetry sector."

*Figure: `figures/07_symmetry_resolved_spectrum.png`*

- All 4 populated levels recovered, max energy error **0.033**, max weight error **0.006**,
  **every symmetry label correct**. [R012, R013]
- Reproducible: **12/12 independent seeds** got all four labels right; across-seed CIs
  (95%) E ±0.004–0.025, q ±0.03–0.35. [R019]
- The colour — the symmetry sector — is information the ancilla alone cannot provide.

**Speaker:** TBD-NAME

---

## Slide 6 — "It survives on real hardware once the circuit is shallow enough."

*Figure: `figures/09_noise_comparison.png` + hardware table below*

| circuit | marrakesh | kingston |
|---|---|---|
| Trotter (435 2q gates) | 0.179 | 0.368 |
| **exact (101 2q gates)** | **0.822** | **0.878** |

- Signal survival, complete 2×2 grid; depth is the dominant lever (2.4–4.6×) over device
  choice (1.1–2.1×). [R008, R018]
- A **genuine shadow ensemble on hardware** gives χ survival **0.962** and a valid
  ⟨Q⟩ survival **0.957** — the core claim, on a real QPU. [R023]
- *Caveat, stated plainly:* one run per configuration. An independent run of an identical
  4-site circuit 30 min later differed by >2× — real run-to-run variance. [R026, R031]

**Speaker:** TBD-NAME

---

## Slide 7 — "The honest cost: 13 experiments replaced, for a 1.07× variance premium."

*Figure: none — table is the content*

- Conventional route needs **13 dedicated modified Hadamard tests** (Q=3, H=9, Z₀=1 Pauli
  terms) to obtain the same three joint observables. [R021]
- Shadow route: **0 extra circuits** (≤2 extra 1-qubit gates per system qubit), paying a
  measured **1.07×** variance premium on χ_Q specifically (sem 0.1012 measured vs 0.0949
  for dedicated tests at equal shots). [R021]
- The 3^w variance model predicts the measured error bars to within **2%**. [R029]

**Speaker:** TBD-NAME

---

## Slide 8 — "Reproduce our headline figure in under five minutes."

*Figure: repo QR code + `README.md` quickstart screenshot — TBD-NAME to generate*

- Public repo: pinned environment, `run_summary.json` a judge can diff, 37 sourced results
  rows, and an `EVIDENCE.md` mapping every number to its producing command.
- Quickstart reproduces our headline **table** (the 12-seed spectrum) from saved data — no
  long reruns; the money plot itself ships pre-rendered in `figures/`.
- `hardware_run.py` lets anyone with QPU access reproduce our hardware arm in 3 commands.

**Speaker:** TBD-NAME

> ✅ **Prior-art search RUN 2026-08-13** — see `deck/PRIOR_ART_SEARCH.md` for queries,
> results and limits. No public implementation of the paper's protocol was found; two
> adjacent Qiskit repos exist (classical-shadow-vqe, shadow-tutorial) but neither combines
> the Hadamard test with shadows.
> **Use this exact phrasing, not "the first":** *"We are not aware of a prior open
> implementation; a web search on 2026-08-13 found none."* The search was three queries on
> one index — defensible, but not proof of priority.

---

## Slide 9 — "What we could not do, and where it breaks."

*Figure: `figures/08_krylov_regularisation.png` (an honest instability plot)*

- The windowed DFT baseline **never** resolves the 1.031-spaced pair at any T_max we tested;
  the matrix pencil resolves it from T_max ≥ 7.0. Method choice, not shots. [R011, R022]
- Exact-synthesis shallowness is an **n=3 artefact** — the advantage falls 3.41× → 1.16×
  going to n=4 and is *expected* to invert beyond (measured at n=3,4 only). [R025]
- One noise study (R017) came out **confounded** and we exclude it rather than report it.

**Speaker:** TBD-NAME

---

## Slide 10 — "Team, and who built what."

- TBD-NAME — TBD-CONTRIBUTION
- TBD-NAME — TBD-CONTRIBUTION
- TBD-NAME — TBD-CONTRIBUTION

**Every member must speak** — this is an explicit rubric line. Allocation above must map to
the "Speaker:" fields on slides 1–9.

---

## Optional backup slides (use if asked)

**B1 — Ablation grid.** Protocol × estimator factorise cleanly: estimator choice buys
resolution (3/4 → 4/4 lines), protocol choice buys the labels, and no post-processing
extracts q from χ alone. Standard and shadow Hadamard give *statistically identical* χ
(max 2.10σ, identical mean sem). [R021]

**B2 — QPE comparison.** At matched evolution budget QPE recovers 4/4 lines (max |dE| 0.079)
— better than DFT, worse than pencil — but yields **no symmetry labels at any cost**, since
its ancillas are fully consumed by phase estimation. 8 qubits and 277 CX vs our 4 and 50
(both all-to-all basis, like for like — 5.5x deeper). [R030, R034]

**B3 — Self-validating decoherence witness (Track E).** Tr[(ρ^(I))²] = (1+|χ|²)/2 links the
system channel to the ancilla channel, so their gap detects decoherence with **no exact
diagonalisation** — usable where classical verification is impossible. Validated: null on
ideal sim (−0.1σ), fires under noise (−7.6σ at 1×, −17.2σ at 5×), correct null on our
cleanest hardware run (−1.4σ). [R033]

**B4 — Eigenstate detector (Track C).** Witness calibration from a true eigenstate
(z = 0.42, correctly undetected) to our benchmark state (z = 62.3), with detection power
measured against shot budget. [R032]

**B6 — Future work, already prototyped: density of states.** The DOS is the Fourier
transform of Tr[U(t)] — the *trace*, not a state expectation. Swap our input state for the
maximally mixed one and **the same experiment becomes a DOS estimator**, with one line
changed and the entire analysis chain untouched. Prototyped: peak weights correctly become
degeneracies (isolated levels 0.11–0.13 vs predicted 1/8; a 3-fold merged peak 0.354 vs
predicted 3/8). Verified against arXiv 2407.03414v2, whose Eq. (7), 1-design construction
and W=H / W=S†H quadratures all match what we built independently. **The extension we could
add:** that paper obtains fixed-particle-number DOS with *one experiment per sector*; our
shadow channel measures ⟨Q^k⟩ from the *same* shots, so the charge moments at each peak
recover **all sectors from a single run** (Q², Q³ are 4 Pauli terms each; the moment
inversion has condition number 31). [R038]

**B5 — Bugs we caught, and how.** A fixed-basis shadow estimator silently returns a
*different observable* — 65σ wrong with **zero noise** (B04). A U-statistic error bar
computed over pairs instead of shots faked a 2.2σ signal until an ideal-simulator control
leg exposed it (B06). Both are in `BUGLOG.md` with prevention rules.
