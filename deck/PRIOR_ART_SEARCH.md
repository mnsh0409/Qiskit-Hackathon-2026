# Prior-art search — record of scope and result

Required by `t5-shadow-ship` before any "first open implementation" phrasing is used.
**A claim is only as good as the search behind it, so the scope is recorded here in full,
including its limits.**

## Date

**2026-08-13**, ~19:50 local.

## The claim being tested

> "First open Qiskit implementation of Faehrmann, Eisert & Kueng, *In the Shadow of the
> Hadamard Test*, PRL **135**, 150603 (2025) / arXiv:2505.15913."

## Queries run (web search, US-region index)

1. `"In the Shadow of the Hadamard Test" Faehrmann Eisert Kueng implementation code`
2. `github shadow Hadamard test classical shadows qiskit implementation "2505.15913"`
3. `"garbage state" Hadamard test classical shadows symmetry-resolved spectrum open source repository 2026`

## Result

**No public implementation of the paper's protocol was found.** All three queries returned
the paper itself (arXiv, PRL, FU-Berlin repository, ResearchGate) and no accompanying code.

Two adjacent Qiskit repositories exist and are worth citing as *related but different work* —
neither implements the shadow-Hadamard combination:

- [`renatawong/classical-shadow-vqe`](https://github.com/renatawong/classical-shadow-vqe) —
  classical shadows + VQE for molecular ground-state energies.
- [`ryanlevy/shadow-tutorial`](https://github.com/ryanlevy/shadow-tutorial) — ShadowQPT
  tutorial in Qiskit.

## Limits of this search — read before relying on it

1. **Three queries on one general web index.** Not searched: GitHub code search directly,
   Zenodo, the authors' group pages, PRL supplementary material, or any non-English source.
2. **Absence of evidence is weak evidence of absence.** An unindexed, unreleased, or
   recently-published repository would not appear here.
3. **Not checked with the authors.** The most reliable disconfirmation would be asking them.

## Decision (2026-08-13): advisor authorised the "first" claim

The project advisor judged the claim supportable and instructed us to state it. That is
consistent with `t5-shadow-ship`'s own rule, which reads: *"None found → state the claim with
a date-stamped note of search scope."* The search below found none, so the rule's condition
is met and the claim is stated on slide 9 **with the scope note attached**.

**The scope note is not optional.** It is what makes the claim defensible rather than
merely asserted, and it is the difference between a claim that survives a challenge from
someone in the room and one that does not. Do not strip it when exporting slides.

## Phrasing actually used on slide 9

> "First open implementation of PRL **135**, 150603. Prior-art search 2026-08-13; scope and
> limits recorded in `deck/PRIOR_ART_SEARCH.md`."

## Fallback if challenged in the room

If someone says they know of an existing implementation, do not defend priority — concede
cleanly and fall back to the claim that does not depend on it:

> "Then we'll correct that — thank you. The method is from the paper either way; what's ours
> is the characterisation: the measured cost, the failure boundary, and the hardware study."

That fallback is strong on its own, which is precisely why the priority claim is not worth
fighting over.

If a judge asks directly: *"We searched and found none, but we scoped the search narrowly
and would not claim priority on that basis."*
