# Judge report — C7 panel (2026-08-14, morning of upload)

Materials judged: `deck/trackb.pdf` (32 pp), `deck/slides_content.md`,
`deck/script.md`, `deck/qa_crib.md`, `README.md`, the participant notebook,
`deck/*.png`, `figures/*.png`. Nothing else.

---

## J1 — rubric bureaucrat

| criterion | weight | score | one-line justification |
|---|---|---|---|
| Originality & Uniqueness | 15 | **11** | Track B completion (sum/difference readout), the phase-trap discovery, and pre-registered hardware falsification are genuinely unusual; the core protocol is the PRL's and AQC is an off-the-shelf addon. |
| Usefulness & Complexity | 25 | **19** | Quickstart reproduces the headline table from saved data; scripts re-run every hardware number; but the flagship compilation win is demonstrated NOT to function on present hardware, and the tooling is benchmark-specific. |
| Quantum Community Benefit | 25 | **20** | The ledger discipline (R### on every number), bug log with retractions, study notes and handover are teachable artefacts beyond the result itself; reuse of the Track-B certifier is plausible. |
| Presentation | 35 | **24** | Takeaway-sentence titles, scoreboard opener, negatives given equal billing — strong. Docked hard for: THREE `TBD-NAME`s still on the title and team slides; script timing 10:20 against a stated 10:00 before any cut; speaker roster unassigned so "did every member speak" is UNVERIFIABLE; README quickstart's first line does not run (J3). |
| **Total** | 100 | **74** | |

**Where a median team beats this one:** logistics. A median team has real names
on the title slide, a first command that runs verbatim, and a talk that fits
its slot without a cut list. This team has better science and worse housekeeping;
the rubric weights housekeeping at 35%.

**Banned-language sweep:** no "quantum advantage" found. "free error bar"
(S13/p.21) is costed in caption and script ("no additional circuits",
diagnostic-only, R044) — PASS, borderline; keep the costing sentence adjacent to
the word "free" wherever it appears. No causal single-run device comparisons
found on slides (single-run status is disclosed). "Hardware" language is
consistent with hardware having actually run.

---

## J2 — physics professor

1. **THE weakest claim (see below): ε_eff is presented as measured; it is a
   bound.** A7 extracts ε_eff = −ln(0.026)/576 = 6.3×10⁻³. At 4,000
   shots/quadrature, the per-quadrature σ is 1/√4000 ≈ 0.0158, so a *fully dead*
   circuit yields E|χ| = σ√(π/2) ≈ 0.020 from estimator bias alone. Measured
   0.026–0.033 is 1.3–1.7× the pure-noise mean — consistent with noise floor.
   Hence 6.3×10⁻³ is a LOWER bound on ε_eff, not a measurement; the true error
   may be worse. The conclusion (win invisible on hardware) survives — indeed
   strengthens — but the wording "extracted from data" over-claims.
2. **⟨Q⟩_W−⟨Q⟩_U deviations carry no uncertainties on the slide** (−0.04/−0.39/
   −0.25/−0.34, S13). House rule is "every number an uncertainty"; single-run,
   no bootstrap is disclosed in the ledger but not visible on the slide. A
   judge reading only slides sees naked numbers.
3. The identity ⟨Q⟩_W−⟨Q⟩_U ≡ 0 is correctly argued for Trotter factors (each
   term conserves Q); the slide's "for any W in this family" is right but
   "family" is undefined on-slide — one clause would close it.
4. Conventions, unbiasedness, 3^w variance: internally consistent; the 2%
   variance-model check and the 12/12-seed table are the strongest
   physics-hygiene artefacts here. The non-degenerate-by-design benchmark
   dodges the degeneracy question legitimately (and says so).
5. The miami 22.6σ statement (trap slide) is a single run used to illustrate a
   metric failure, not a device claim — acceptable as framed, fragile if a
   speaker improvises it into a device comparison. Script wording is safe;
   enforce it.

---

## J3 — engineering pragmatist (executed, timed)

Fresh clone, README followed verbatim:

| step | README says | result | time |
|---|---|---|---|
| 1 | `git clone <this-repo> && cd 2026` | **FAILS twice**: `<this-repo>` is a literal placeholder; after substituting the URL, `cd 2026` fails — the directory is `Qiskit-Hackathon-2026` | clone 5.9 s |
| 2 | venv + pinned pip | works | 15.2 s (warm wheel cache; **expect minutes on a judge's cold machine**) |
| 3 | headline table from saved data | works, prints the 12/12 table matching the README | 0.013 s |
| — | notebook evidence without executing | 34/98 cells carry embedded outputs; **56 embedded "PASS" strings visible** without running anything | — |
| — | slide-QR target | HTTP 200 | — |

**What breaks first: the first line of the quickstart.** Everything after it
works and is fast. Total honest time after fixing line 1: **~25 s warm,
plausibly 3–5 min cold.** The "5-minute" claim is defensible only once line 1
is fixed.

---

## 12 questions, ordered by hostility (answer the panel would accept)

1. **"Your ε_eff of 6×10⁻³ — that's just the noise floor of |χ|, isn't it?"**
   Accept: "Correct — 0.026 is near the |·| bias floor at these shots, so
   6×10⁻³ is a lower bound on the effective error and the visibility gap is AT
   LEAST 3×. The verdict is unchanged; the label should say 'bound'."
2. **"Slide 13's charge deviations have no error bars. Why should I trust
   them?"** Accept: single run, disclosed in R044; the per-quadrature sem is
   ~0.016 so −0.39 is many σ from zero; slides should carry that sem.
3. **"Your first README command doesn't run."** Accept: acknowledged; the fix
   is one line; everything downstream executes in seconds (demonstrate).
4. **"Three TBD names on the title slide the morning of judging?"** Accept
   only: the filled slide.
5. **"36× on paper, 12× wrong on hardware — why is the headline not simply
   'we were wrong'?"** Accept: both are pre-registered claim types; slide 2
   leads with the failure at equal size; the compilation number is
   deterministic and reproducible from the repo.
6. **"Why n=6 when your headline is n=7?"** Accept: the A7 arithmetic
   (control-arm cost ×4, contrast saturated) — it is on a slide.
7. **"The echo beats you 27×. Why does your instrument exist?"** Accept: phase
   + per-observable profile, which no scalar test returns; stated with the
   loss, not instead of it.
8. **"Process infidelity 0.96 — your compiled gate is not U at all."** Accept:
   compressed against one input by design; legitimate for a Hadamard test
   only; the slide says exactly this.
9. **"Is the 22.6σ miami number a device comparison from one run?"** Accept:
   no — a metric-failure exhibit; survival ordering across models is shown
   inconsistent, no device ranking claimed.
10. **"Did every member speak?"** Accept only: yes, with named blocks. Script
    has A/B/C blocks but no names attached as of judging morning.
11. **"What's actually new versus the PRL?"** Accept: the sum/difference
    completion, the trap + one-gate fix, pre-registered hardware falsification,
    and the boundary maps; the base protocol is credited to the paper on the
    title slide.
12. **"First open implementation — verified how?"** Accept: date-stamped search
    scope in the repo, plus the rehearsed concession if prior art surfaces.

---

## Singular findings

**THE weakest claim:** A7 / R054 wording that ε_eff ≈ 6×10⁻³ is "extracted from
data." It is a lower bound extracted from a value consistent with the |χ|
noise floor. *30-minute fix (belongs to /c6):* on A7 and in the script, change
"extracted" to "bounded below by"; add one line "measured |χ| ≈ noise floor
0.020 at these shots ⇒ ε_eff ≥ 6×10⁻³, gap to visibility ≥ 3×." Conclusion
unchanged, over-claim removed.

**THE weakest slide:** the Team slide (S17) — three `TBD-NAME`s and no
who-built-what, on a rubric that explicitly scores whether every member spoke,
under the criterion worth 35%. *30-minute fix (belongs to humans + /c6):* fill
three names, one line of ownership each, map to script blocks A/B/C.

**Timing check:** script totals 10:20 against a stated 10:00 slot — DOES NOT
FIT until cut 1 is applied; with cut 1 it is 10:00 with zero slack, violating
the script's own 10% slack rule. **Speaking check:** blocks exist for three
speakers; UNVERIFIABLE against a roster that does not exist in the materials.

No further comment. Fixes belong to /c5 and /c6.
