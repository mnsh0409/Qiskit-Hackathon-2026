# Research outline — ancilla-tagged classical shadows

**Status: research proposal, not a manuscript.** Nothing here is a result; the repo
contains the *setting* and the *instruments*, and this outline defines the new work.
Drafted 2026-08-16. Kill criteria are part of the plan — this project should die
cheaply at M0 or M1 if the answers turn out to be trivial or taken.

## One-paragraph problem statement

In the shadow-enhanced Hadamard test, every shot yields a triple
(ancilla outcome *a* = ±1, random basis *b*, system outcomes *s*): a classical shadow
of the garbage register, *tagged* by the interference outcome. Tagged shadows estimate
objects ordinary shadows cannot touch — the difference channel
Tr[O·(WρW† − UρU†)]/2 and the off-diagonal (interference) observables
χ_O = ⟨ψ|W†·O·U|ψ⟩ — but nothing is known about doing this *well*: the estimator in
use (ours, and the PRL's) is the naive one, ±1-weighting the standard 3^w snapshot.
The project: estimator theory, measurement-ensemble optimization, and noise
mitigation, specifically for the tagged estimator class.

## Why us, and why it might be unoccupied

The shadow-improvement literature optimizes *state* shadows: derandomization and
locally-biased ensembles (Huang–Kueng–Preskill PRL 127, 030503 (2021); Hadfield et
al.; Nakaji et al., Quantum 7, 995 (2023)), noise-robust calibration (Chen et al.,
PRX Quantum 2, 030348 (2021); Onorati et al., arXiv:2403.04751; Farias et al.,
arXiv:2405.06022), and symmetry adjustment (Zhao & Miyake, npj QI 10, 57 (2024)).
All of it treats the measured state as *the* object. The tagged setting has a second
classical register — the tag — whose noise channel (the interference contrast) is
distinct from the shadow channel, and whose estimator couples the two. Our repo
already holds: the validated tagged estimators (R042), the measured variance model
and its 1.07× premium (R021/R029), the conservation-law "free error bar" on the
difference channel (R044), and hardware evidence that the *ancilla* is where the
damage concentrates — coherent phase errors (R061-P3) and relaxation floors (R054).
That last fact is the thesis: **in interferometric shadows, the tag is the noisy
part, and no existing shadow-improvement technique targets it.**

## The three research questions

**Q1 — Variance anatomy of tagged estimators.** The ±1 tag inherits the full 3^w
snapshot variance even when the estimand is small: for W ≈ U (the verification
regime!) the difference channel's signal → 0 while its variance stays at
state-shadow scale — an SNR collapse we have observed but never formalized
(it is one mechanism behind the echo beating our arm 27×, R043/R044). Deliverables:
exact second-moment formulas for the tagged difference and off-diagonal estimators
(weight-(w+1) effective observables Z_a⊗O, X_a⊗O, Y_a⊗O with a deterministic ancilla
factor); sample-complexity comparison against the ancilla-free alternative (two
separate state-shadow experiments on W|ψ⟩ and U|ψ⟩, subtracted classically) — making
precise *what the interference circuit buys and what it costs*, per observable.

**Q2 — Ensemble optimization for tagged targets.** Derandomization/locally-biased
ensembles, adapted to the tagged product measure: the ancilla basis is fixed by the
readout (never randomized), the system bases are optimized against a *tagged* target
set {χ_O}. Concrete and mechanical once Q1's cost function exists; the open question
is the size of the win on realistic target sets (our benchmark's 13-observable set,
R021, is the testbed).

**Q3 — Self-calibrating tagged shadows: the error bar becomes error mitigation.**
R044 uses conservation (⟨Q⟩_W − ⟨Q⟩_U ≡ 0) as a *diagnostic*. The proposal: use the
full set of known-zero and known-value identities (conserved differences ≡ 0; the
sum channel of the identity ≡ 1; Im Tr[W†U] ≡ 0 for palindromic Trotter, R045) to
*fit* an effective tag-noise model — interference contrast λ and tag-flip/dephasing
parameters — then invert it on the non-conserved estimates:
χ̃_O = λ·χ_O + noise → χ̂_O = χ̃_O/λ̂. This is the tagged-setting analogue of
symmetry-adjusted shadows (Zhao–Miyake correct the *shadow* channel; we correct the
*tag* channel — the positioning claim to verify at M0), with bias–variance bounds
for the calibrated estimator as the theory deliverable.

## First three experiments (cheap, machinery exists in the repo)

**E1 (simulator, extends R021/R029 code):** measure Var of the tagged difference and
off-diagonal estimators across the benchmark observable set and across
‖W−U‖; verify Q1's second-moment formulas term-by-term (the R029 methodology, 2%
agreement bar); locate the SNR-collapse regime quantitatively.

**E2 (simulator):** implement the tagged derandomization cost of Q2; compare
uniform vs optimized ensembles on the 13-observable target set at equal shot budget;
pre-register the win threshold that justifies continuing (≥2× variance reduction on
the worst-case observable, else Q2 is an appendix, not a section).

**E3 (Aer noise model, then one hardware job):** implement the Q3 calibration
estimator; validate on the Challenge-11 noise model at 1× and 5× noise; then one
2-site balanced-ensemble hardware job (R023-class, ~20–30 s QPU, free tier)
comparing raw vs calibrated χ_O against exact, success criterion pre-registered
before submission.

## Milestones and kill criteria

- **M0 (2 weeks): literature deep-read.** Read, not skim: Zhao–Miyake, Onorati et
  al., Chen et al., the PRL's appendices, and a fresh search for "tagged"/"weighted"
  /"conditional" shadows and shadow process tomography (arXiv:2110.02965 class).
  **Kill if:** any of them already treats the tagged estimator class, or the
  off-diagonal estimator reduces to an existing process-shadow special case.
- **M1 (4 weeks): Q1 theory + E1.** **Kill if:** the tagged variance is exactly the
  state-shadow variance with no structure to exploit (then there is nothing to
  optimize and Q2/Q3 inherit nothing).
- **M2 (4 weeks): Q2 + E2** — continue/demote per E2's pre-registered threshold.
- **M3 (6 weeks): Q3 + E3** incl. the hardware point.
- **M4 (4 weeks): write-up.** Venue: Quantum or PRA. ~5 months part-time total.

## Constraints and honesty rules (inherited from the project)

Everything graded against exact references on small systems first; every number in
any eventual manuscript traces to a ledger row; no advantage-over-classical claims;
pre-registered success criteria before any hardware submission. Team roles, and
whether this proceeds at all, are decisions for after papers 1–2 ship.
