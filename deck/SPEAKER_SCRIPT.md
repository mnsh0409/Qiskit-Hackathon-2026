# Speaker script — Topic 5

**Written per `deck_arc.md` script rules:** short declarative sentences for non-native
English speakers, phonetic hints on hard terms, per-member allocation, timed with slack.

**Target: 10 minutes of speech + 10% slack.** Times below sum to **9:00**, leaving a
1-minute buffer. If you are running long, cut slide 9's second bullet and backup slides.

**Pronunciation hints**
- *ancilla* — an-SIL-la
- *Hadamard* — HA-da-mar (final "d" is silent in French; "HAD-a-mard" is also accepted)
- *quadrature* — KWOD-ra-cher
- *Trotter* — TROT-ter
- *decoherence* — dee-co-HEER-ence
- *χ (chi)* — say "kai" (rhymes with "sky")
- *ρ (rho)* — say "roe"
- *eigenstate* — EYE-gen-state

**Numbers rule:** every number spoken below appears in RESULTS.md. Do not improvise numbers.
If asked something not on a slide, say "that is in our results file, I can show you after."

---

## Slide 1 — Hook (45 s) — Speaker: TBD-NAME

> Good morning. We work on the Hadamard test.
> The Hadamard test is a standard quantum circuit. It uses one extra qubit, called the
> ancilla.
> You measure the ancilla. You throw away everything else.
> We asked one question. What if we do not throw it away?
> If you measure the discarded qubits in random directions, they become useful data.
> The same shots now tell you much more. That is our project.

---

## Slide 2 — One record, many quantities (55 s) — Speaker: TBD-NAME

> Here is the circuit. It is small: three system qubits, and one ancilla.
> We run it once. We keep every shot.
> From that single record set, we extract seven different physical quantities.
> The signal chi of t. Three joint observables. And three system observables.
> The total cost was three thousand four hundred fifty-six circuits, and two hundred
> fifty-six thousand shots.
> That is one experiment. Not seven.

---

## Slide 3 — Validation (60 s) — Speaker: TBD-NAME

> We do not ask you to trust this. We validated everything.
> The notebook has fifty-six checkpoints. All fifty-six pass. No failures, no warnings.
> Look at the error bars. Our measured error is zero point zero two nine.
> Our predicted error bar is zero point zero two eight.
> The ratio is one point zero five. So our error bars are honest. They are not too small.
> And the error falls with the square root of the number of shots. The slope is minus zero
> point four six. Theory says minus zero point five.
> This means we are limited by statistics, not by a hidden mistake.

---

## Slide 4 — The shared-shot punchline (55 s) — Speaker: TBD-NAME

> Now the interesting part.
> Energy and magnetisation are conserved. So they should be flat in time.
> We measured the energy as zero point zero seven one, plus or minus zero point zero zero
> eight. The exact value is zero point zero seven four.
> We measured the magnetisation as two point two seven one. The exact value is two point
> two six seven.
> And here is the point. These came from the qubits the standard method throws away.
> No extra circuits. There is a cost, and we will quantify it on slide seven.

---

## Slide 5 — MONEY PLOT (75 s) — Speaker: TBD-NAME

> This is our main result.
> The grey curve is what a standard Hadamard test gives you. It is a blur.
> The coloured lines are our reconstruction. We recover all four energy levels.
> Our worst energy error is zero point zero three three.
> But look at the colour. The colour is the symmetry sector of each line.
> That information does not exist in the grey curve. It comes from the recycled data.
> And it is reproducible. We ran twelve independent random seeds.
> All twelve got every symmetry label correct. Twelve out of twelve.

*(Pause here. This is the slide to let land.)*

---

## Slide 6 — Real hardware (70 s) — Speaker: TBD-NAME

> We also ran this on real IBM hardware.
> Our first attempt failed. The signal survived at only eighteen percent.
> The circuit was too deep. Four hundred thirty-five two-qubit gates.
> So we built a shallower circuit. One hundred one gates. Same physics.
> The signal survived at eighty-two percent. On the better machine, eighty-eight percent.
> And with a full random-basis measurement, we recovered a real system observable on
> hardware. Ninety-six percent survival.
> One honest warning. These are single runs.
> A teammate ran an identical circuit thirty minutes later and got a result two times
> different. Hardware varies. We report that.

---

## Slide 7 — Honest cost (50 s) — Speaker: TBD-NAME

> Nothing is free. Here is the real cost.
> To get the same three observables the conventional way, you need thirteen separate
> experiments.
> We need zero extra circuits.
> But our estimator is noisier. We measured the penalty. It is one point zero seven times.
> Seven percent more noise, to replace thirteen experiments.
> And we can predict that noise from theory, to within two percent.

---

## Slide 8 — Reproducibility (45 s) — Speaker: TBD-NAME

> Everything is public and reproducible.
> Our repository has pinned versions, a summary file you can compare against your own run,
> and thirty-three results rows.
> Every single number maps to the exact command that produced it.
> You can reproduce our main figure in under five minutes, from saved data.
> If you have quantum hardware access, three commands reproduce our hardware results.

---

## Slide 9 — Limitations (50 s) — Speaker: TBD-NAME

> We want to be honest about the limits.
> First. The simple Fourier method never resolves our two closest energy levels. Not at any
> setting we tried. We needed a better estimator, not more shots.
> Second. Our shallow circuit trick only works because our system is small. It gets worse as
> the system grows. It is not a general recipe.
> Third. One of our noise studies came out confounded. We excluded it instead of reporting
> it.

---

## Slide 10 — Team (25 s) — Speaker: TBD-NAME

> Finally, our team.
> TBD-NAME built TBD-CONTRIBUTION.
> TBD-NAME built TBD-CONTRIBUTION.
> TBD-NAME built TBD-CONTRIBUTION.
> Thank you. We are happy to take questions.

---

## Q&A crib sheet

**"Is this faster than a classical computer?"**
> No, and we do not claim that. Our system is three qubits. A laptop solves it instantly.
> It is small on purpose, so we can check every number against the exact answer.

**"What is new here? The paper already exists."**
> The method is from the paper. What is new is the systematic characterisation.
> We measured the cost, found the failure modes, ran a five-way method comparison, and
> tested it on three different real devices.

**"How do you know your error bars are right?"**
> We checked them two ways. The measured scatter matches the predicted error bar, ratio one
> point zero five. And we ran twelve independent seeds and compared the spread to our
> bootstrap. They agree within the noise of the comparison itself.

**"Did anything go wrong?"**
> Yes, twice, and both are documented. We once applied a shadow estimator to fixed-basis
> data. That silently measures a different quantity. It was sixty-five sigma wrong with no
> noise at all. And we once computed an error bar over pairs instead of over shots, which
> faked a signal. An ideal-simulator control caught it.

**"Can this scale?"**
> The measurement idea scales. Our specific shallow-circuit trick does not — we show the
> crossover at four qubits. Beyond that you would need circuit compression, for example
> tensor-network approximate compiling.

**"What about the symmetry labels under noise?"**
> We tested it and the result was confounded, so we are not claiming it. That is honest
> future work.

---

## Timing summary

| slide | time | cumulative |
|---|---|---|
| 1 | 0:45 | 0:45 |
| 2 | 0:55 | 1:40 |
| 3 | 1:00 | 2:40 |
| 4 | 0:55 | 3:35 |
| 5 | 1:15 | 4:50 |
| 6 | 1:10 | 6:00 |
| 7 | 0:50 | 6:50 |
| 8 | 0:45 | 7:35 |
| 9 | 0:50 | 8:25 |
| 10 | 0:25 | 8:50 |

**Total 8:50** — buffer to 10:00. Rehearse once with a timer; non-native speakers should
read slower than feels natural.
