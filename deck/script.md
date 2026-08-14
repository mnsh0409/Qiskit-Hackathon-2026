# script.md — per-member speaking blocks (C6)

**Talk length: TBD-C6** (not supplied); timed for a working assumption of
**10:00**, with the cut list bringing 10:20 spoken under it. **Team size: FIVE
(confirmed): Chao Hsien, Jiwan Kang, Ng Siu Hin, Su Wei-Chang, Tina Tien.**
Blocks M1–M5 are contiguous and sized 1:45–2:55; every member speaks (rubric
requirement). Assigned in roster order below; M4 (Su Wei-Chang) should be the
strongest English speaker — it carries the AQC win, the trap, and the hardware
failure; swap M4 with another block if that is not Su Wei-Chang. English
comfort per member: TBD-C6. Divider pages: advance silently.

**Numbers rule: every number below is grep-verified against RESULTS.md and
tagged. Do not improvise numbers on stage.**

**Pronunciation:** *ancilla* an-SIL-la · *Hadamard* HA-da-mar · *χ* "kai" ·
*Loschmidt* LOSH-mit · *ansatz* AHN-zahts · *AQC* ay-cue-see · *Trotter*
TROT-ter · *Fermi–Hubbard* FER-mee HUB-bard.

---

## Block M1 — open (S1–S3) — Chao Hsien — 1:50

> We are Team 8, the Garbage Collectors. This is the shadow-enhanced Hadamard
> test — and our story is how we made it scale, found the trap that silently
> breaks it, and then tested our own claim on real hardware. Including the part
> where the hardware said no.

> Four numbers up front. Thirty-six times fewer gates — as a compilation result
> [R046]. One single-qubit gate to fix an error larger than the signal [R046].
> Two quantum processors where our own pre-registered prediction failed by
> twelve times [R054]. And one identity that is exactly zero, which hands us a
> device-error bar with no extra circuits [R044].

> The challenge had five tracks. We completed all five — the mandatory one at
> twelve out of twelve seeds [R019]. This talk is Track B, the one we took
> furthest.

## Block M2 — the question and the instrument (S4–S6) — Jiwan Kang — 2:05

> Here is the question everything hangs on. Every real simulation runs a cheap
> approximation W instead of the true evolution U. How wrong is W — and wrong
> in *what*? Classically you simulate both. That is exactly what you cannot do
> at scale. Track B answers it on the device.

> One change to the textbook circuit. Two X gates around the controlled-W make
> W fire when the ancilla is zero, and U when it is one. The ancilla now
> interferes two dynamics against each other. Nothing downstream changes.

> A new circuit gets its own validation. The identity holds to ten to the minus
> fourteen on two models [R034, R042] — and that check caught a real endianness
> bug before it ever reached a quantum processor [R042].

## Block M3 — shadows and the honest rivals (S7–S9) — Ng Siu Hin — 1:45

> For anyone new to shadows: measure each qubit in a random basis, keep the
> record. One record set then estimates every Pauli observable at once, at a
> variance of three to the weight — a model we verified to within two percent
> [R029]. And here is our completion of Track B: delete the final Hadamard, and
> the shadows split into the sum and the difference of the two dynamics. Add
> and subtract — you get every observable under W and under U separately
> [R042]. The ancilla says how much W is wrong. The garbage says which
> observable.

> Due diligence: the literature already verifies compiled circuits — the
> Loschmidt echo, the Hilbert–Schmidt test. We implemented both, verified both
> [R043]. And the scoreboard is not flattering: the echo is four to six times
> cheaper at every size we measured [R043]. If you want one number, use the
> echo. Our arm exists for what nothing else returns: the phase, and the
> per-observable breakdown.

## Block M4 — the win, the trap, the verdict (S10–S12) — Su Wei-Chang — 2:55

> Now the bottleneck. The standard construction of the controlled evolution
> costs four to the n-plus-one gates. AQC grows roughly linearly. They cross at
> four qubits; by seven, AQC is thirty-six times cheaper at infidelity three
> times ten to the minus four [R046]. That survives a 2D lattice [R049], the
> Fermi–Hubbard model [R051], and real device routing — which widens the gap
> [R052].

> But shipping it naively destroys the experiment. The compiler maximises a
> magnitude; a Hadamard test measures a phase. The compression converges
> beautifully and returns chi wrong by up to three radians — an error as large
> as the signal [R046]. The fix is one phase gate on the ancilla: error one
> point three three down to zero point zero zero eight [R046]. We met the same
> magnitude-hides-phase failure two more times — once in a teammate's hardware
> data [R053], and once, as you will now see, in our own.

> We tested our own claim. Three constructions, one job, two devices, and the
> survival numbers written down before submitting. Every arm came back as noise
> — ours twelve times below its own prediction [R054]. And the deepest, deadest
> circuit got the best score: survival one point four eight five. That is
> unphysical — chi cannot exceed one. It is a relaxation floor, and a
> magnitude-only metric crowns it the winner [R054]. We know exactly what error
> rate changes this verdict; the arithmetic is in appendix A-seven [R055].

## Block M5 — hardware close and claims (S13–S17) — Tina Tien — 1:45

> Track B itself, same discipline: the two-gate echo beat our arm
> twenty-seven times on hardware, and the gap widened to thirty-two times
> when we extended the time window [R044, R059]. One clean win survives: a charge
> difference that must be exactly zero, so its measured value is pure device
> error — an error bar with no reference state and no simulation [R044].

> What we claim: the compilation result, the trap and its one-gate fix, the
> completion of Track B, and the hardware tests themselves. What we do not
> claim: that the gate-count win reaches today's hardware — we showed it does
> not [R054] — and nothing against classical computation; the benchmark is
> small on purpose, so every number is graded against truth.

> One future direction, already verified: the same circuit with a maximally
> mixed input becomes a density-of-states estimator [R045].

> Everything is public behind this QR — a fifty-eight-row results ledger, the bug
> log including our own retractions, and the scripts behind every hardware
> number. [Team slide: each of the FIVE members states their part — Chao Hsien, Jiwan Kang, Ng Siu Hin, Su Wei-Chang, Tina Tien.]

> [Summary slide, ~10 s:] To summarise: five tracks completed. A
> thirty-six-times compilation win. A trap found — and fixed with one gate. And
> an honest hardware no, predicted in advance. Every line here has its source
> row. We leave this up — thank you, questions welcome.

---

## Timing (assumes 10:00 slot — TBD-C6)

| block | speaker | time | cumulative |
|---|---|---|---|
| M1 open (S1–S3) | Chao Hsien | 1:50 | 1:50 |
| M2 question+instrument (S4–S6) | Jiwan Kang | 2:05 | 3:55 |
| M3 shadows+rivals (S7–S9) | Ng Siu Hin | 1:45 | 5:40 |
| M4 win/trap/verdict (S10–S12) | Su Wei-Chang | 2:55 | 8:35 |
| M5 hardware close (S13–S17 + summary) | Tina Tien | 1:55 | **10:30** |

10:30 spoken against 10:00 is deliberate: the cut list brings it under with the
first two items (or cut 1 plus a brisk M1). **Cuts, in order:** (1) S15 DOS sentence −0:20; (2) shadow primer half of
S7 −0:40, only for an expert room; (3) merge S8 into S9 −0:30. **Never cut:**
S11 the trap, S12 the failure, S14 the claims. Checkpoint: start Block M4 by
5:45 or apply cut 1 immediately. All five members also appear on the team slide.
