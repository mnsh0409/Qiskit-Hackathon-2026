# Speaker script — Track B deck (`trackb.pdf`, 35 pages)

**CORRECTION (2026-08-14): the per-beat times below sum to 12:40, not the 9:20
originally claimed — an arithmetic error caught in review. Treat this file as the
EXTENDED narration (study/rehearsal version); the timed five-member performance
script is `script.md` (blocks M1–M5, 10:20 with cuts).**
Slides are referenced by TITLE, not page number — pages have shifted three times
already tonight and titles have not. Divider pages ("The question", "The
instrument", …): say nothing, advance within ~3 seconds; they exist as breathing
room, not content. The appendix (A1–A8) is never presented — it is jumped to in
Q&A only.

**Numbers rule (house law): every number spoken below is in RESULTS.md under the
row cited. Do not improvise numbers.** If asked something not on a slide:
"that's in our results ledger — row so-and-so, I can show you after."

**Pronunciation hints**
- *ancilla* — an-SIL-la
- *Hadamard* — HA-da-mar
- *AQC* — say the letters: ay-cue-see (Approximate Quantum Compiling)
- *Trotter* — TROT-ter
- *χ (chi)* — say "kai"
- *Loschmidt* — LOSH-mit
- *ansatz* — AHN-zahts
- *Fermi–Hubbard* — FER-mee HUB-bard

---

## Title (0:15)
> We are Team 8, the Garbage Collectors. Our topic is the shadow-enhanced
> Hadamard test — and our story is how we made that test scale, found the trap
> that would have silently broken it, and then tested our own claim on real
> hardware. Including the part where the hardware said no.

## Outline (0:15)
> Five sections. One thing to know before we start: every tag like R-forty-six
> on these slides is a row number in our public results ledger — one row per
> number, with the command that produced it.

## The result, up front (1:00)
> Four numbers. Thirty-six times fewer gates for the controlled evolution — as a
> compilation result. One single-qubit gate to fix a trap that otherwise makes
> the answer wrong by more than the signal itself. Two QPUs where we tested the
> gate-count win — and it did not survive; we predicted the numbers before
> submitting, and we were wrong by twelve times. And one identity that is
> exactly zero, which gives us an error bar on hardware for free.
> That is the honest shape of this project: real wins, and real negatives,
> reported with equal weight. [R046, R054, R044]

## Where this sits: the five tracks (0:30)
> The challenge offered five tracks. We completed all five — Track A is the
> mandatory spectral analyser, twelve out of twelve seeds correct. This deck is
> Track B, the one we took furthest: past the scaffold, against real baselines,
> onto two QPUs, and into compilation. [R019, R034]

## You compiled U into something cheaper. Is it still right? (0:45)
> Here is the question everything hangs on. Every practical simulation replaces
> the true evolution U with something cheaper — a Trotter formula, a compiled
> circuit. The question that decides whether your result means anything is: how
> wrong is the cheap version, and wrong in *what*? Classically you answer by
> simulating both — exactly what you cannot do at scale. Track B answers it on
> the device: put both evolutions on one ancilla and let them interfere.

## Anti-control: how the Hadamard test is extended (0:50)
> One structural change to the textbook circuit. The sandwich of two X gates
> around the controlled-W makes W fire when the ancilla is zero, U when it is
> one. So the ancilla no longer compares U against doing nothing — it compares
> two dynamics against each other. Everything downstream is unchanged. The
> algebra is in appendix A-one and A-two if anyone wants it.

## Track B: anti-controlled Hadamard test (0:35)
> Because this is a new circuit, it gets its own validation, not inherited
> trust: the identity holds to ten to the minus fourteen on two models. And this
> check caught a real bug — an endianness mistake in our own reference that
> passes at t equals zero and fails everywhere else. It never reached the QPU.
> [R034, R042]

## First, what a classical shadow is (0:45)
> For anyone new to shadows: measure each qubit in a random basis each shot,
> keep the record. The randomness is the whole trick — one record set becomes an
> unbiased estimator for every Pauli observable at once, at a price of three to
> the weight in variance. The worked table shows the same five shots feeding two
> different observables.

## What the shadows add: delete the final Hadamard (0:45)
> Here is our completion of Track B. Delete one gate — the final Hadamard — and
> the ancilla-tagged shadows split into a sum and a difference of the two
> dynamics. Add and subtract, and you get every observable under W and under U
> *separately*, from the same shots. The ancilla says how much the compiled
> circuit is wrong; the garbage register says *which observable* it got wrong.
> [R042]

## We are not the only way to do this (0:35)
> Due diligence: the compiling literature already has verification methods. The
> Loschmidt echo — apply U, un-apply W, measure. The Hilbert–Schmidt test on
> double the qubits. We implemented both and verified them before comparing.
> [R043]

## The honest scoreboard (0:40)
> And the comparison is not flattering: the echo is cheaper than us at every
> size — four to six times. If all you want is one number, use the echo. Our arm
> is justified by what it returns that nothing else does: the phase, and the
> per-observable breakdown. That is the honest trade. [R043]

## AQC makes it scale — crossover at n=4 (0:55)
> Now the bottleneck. The standard exact construction of the controlled
> evolution costs four to the n-plus-one gates — the orange line. Approximate
> Quantum Compiling grows roughly linearly — the blue line. They cross at four
> qubits, and by seven qubits AQC is thirty-six times cheaper, at infidelity
> three times ten to the minus four. Measured, not extrapolated — and it
> survives a 2D lattice, the Fermi–Hubbard model, and real device routing,
> which actually widens the gap. [R046, R049, R051, R052]

## The trap: a phase-blind compiler (1:00)
> But shipping that compression naively destroys the experiment, and nothing
> warns you. The compiler maximises state fidelity — a magnitude. A Hadamard
> test is an interferometer — it measures phase. So a compression that converges
> beautifully returns chi wrong by up to three radians: the error is as large as
> the signal. We nearly missed it because our own certificate was also a
> magnitude. The fix costs one single-qubit gate on the ancilla — the phase is
> free at compile time — and the error drops from one point three to below one
> percent. We saw the same magnitude-hides-phase failure twice more: once in a
> teammate's hardware run, once in our own. [R046, R053, R054]

## We ran it on a QPU. It failed (1:10)
> Then we did the thing you are supposed to do: we tested our own claim. Three
> versions of the same test, one job, two devices, and the survival predictions
> written down *before* submitting. Every arm on both QPUs came back as noise —
> our compiled arm twelve times below its own prediction. And look at the orange
> arm: its "survival" reads one point four nine — the best score on the slide —
> and it is unphysical. Chi cannot exceed one. That circuit is simply dead, the
> ancilla relaxed to zero, and a magnitude-only metric crowns it the winner.
> So: the gate-count win is real; it does not reach today's hardware at this
> size; and we can tell you exactly why and what error rate would change that —
> the arithmetic is in appendix A-seven. [R054, R055]

## First Track B on a QPU — the cheap baseline beat us (0:40)
> Same discipline on Track B itself: four arms, two devices, one job each. The
> two-gate echo tracked the exact curve within a few percent; our
> hundred-and-thirty-six-gate arm did not. Twenty-seven times more accurate, the
> baseline. It is on the slide because it is true. [R044]

## The garbage also ships a free error bar (0:35)
> One clean hardware win. This difference of charges is exactly zero — by
> conservation, for any Trotterisation. So its measured value is pure device
> error, certified with no reference state and no simulation. It flagged
> precisely the times where everything else degraded. [R044]

## What we claim, and what we do not (0:40)
> The summary, in two honest columns. We claim the compilation result, the trap
> and its fix, the completion of Track B, and the hardware tests themselves. We
> do not claim the gate-count win reaches hardware — we showed it does not — and
> we do not claim any advantage over classical computation: the benchmark is
> small on purpose, so every number could be graded against truth.

## Future work: density of states (0:20)
> One direction, already verified: feed the same circuit the maximally mixed
> state and it becomes a density-of-states estimator — the W-equals-identity
> special case of Track B. [R045]

## Reproduce it (0:25)
> Everything is public: the repo behind this QR, a sixty-one-row results
> ledger, the bug log including our retractions, and scripts that reproduce
> every hardware number in a handful of commands.

## Summary (0:10) — leave this slide up for Q&A
> To summarise: five tracks completed. A thirty-six-times compilation win. A
> trap found — and fixed with one gate. And an honest hardware no, predicted in
> advance. Every line has its source row. Thank you — questions welcome.

---

## Timing summary

| beat | time | cumulative |
|---|---|---|
| Title + Outline | 0:30 | 0:30 |
| Result up front | 1:00 | 1:30 |
| Five tracks | 0:30 | 2:00 |
| The question | 0:45 | 2:45 |
| Anti-control + validation | 1:25 | 4:10 |
| Shadows + delete-H | 1:30 | 5:40 |
| Baselines + scoreboard | 1:15 | 6:55 |
| AQC crossover + trap | 1:55 | 8:50* |
| *running long? see cuts* | | |
| QPU failure | 1:10 | — |
| Track B QPU + free bar | 1:15 | — |
| Claims + future + QR | 1:25 | **9:20** |

*The table double-counts nothing; 8:50 is a checkpoint — if you reach the AQC
trap slide after 8:00, start cutting.*

**Cut list, in order (keep the talk at 10:00):**
1. *Future work / DOS* (−0:20) — say one sentence over the Claims slide instead.
2. *First, what a classical shadow is* (−0:45) — only if the audience is expert;
   never cut it for a mixed room.
3. Compress *Baselines* + *Scoreboard* into one beat (−0:30).
4. Never cut: the trap, the QPU failure, the claims slide. They are the talk.

**Q&A: use the crib in `SPEAKER_SCRIPT.md` (§Q&A crib sheet) — it covers the
n=6-vs-n=7 question, the ratio-vs-absolute question, and the priority-claim
fallback. Appendix map for live jumps: A1/A2 anti-control algebra · A3 the
two readouts · A4 shadow variance · A5 the combined estimator · A6 DOS ·
A7 the n=6/n=7 arithmetic ·
A8 pure AQC, no ancilla.**
