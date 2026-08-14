# Speaker script — Topic 5

> **SYNC WARNING (2026-08-13).** This document describes the earlier **10-slide** cut.
> `slides.tex` / `slides.pdf` is now the authority: 24 main pages + 5 backup, organised into
> five sections with an outline and section-divider pages. Content slides present in the PDF
> but **not** written up here: *The protocol, in the authors' own picture* (paper Fig. 1),
> *What a classical shadow actually is*, *The benchmark: three spins*, *What each choice
> actually buys*, *Do you even need shadows?*, *What the shadow inversion actually
> contributes*, *Which protocol can rebuild which observable?*.
> Cross-references below use slide **titles**, not numbers, because the numbering has moved.

**Written per `deck_arc.md` script rules:** short declarative sentences for non-native
English speakers, phonetic hints on hard terms, per-member allocation, timed with slack.

**Target: 10 minutes of speech + 10% slack.** Times below sum to **8:50**, leaving a
70-second buffer. If you are running long, cut the second bullet of "What we could not do" and backup slides.

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

## Slide 1 — Hook (45 s) — Speaker: Chao Hsien

> Good morning. We work on the Hadamard test.
> The Hadamard test is a standard quantum circuit. It uses one extra qubit, called the
> ancilla.
> You measure the ancilla. You throw away everything else.
> We asked one question. What if we do not throw it away?
> If you measure the discarded qubits in random directions, they become useful data.
> The same shots now tell you much more. That is our project.

---

## Slide 2 — One record, many quantities (55 s) — Speaker: Jiwan Kang

> Here is the circuit. It is small: three system qubits, and one ancilla.
> We run it once. We keep every shot.
> From that single record set, we extract seven different physical quantities.
> The signal chi of t. Three joint observables. And three system observables.
> The total cost was three thousand four hundred fifty-six circuits, and two hundred
> fifty-six thousand shots.
> That is one experiment. Not seven.

---

## Slide 3 — Validation (60 s) — Speaker: Ng Siu Hin

> We do not ask you to trust this. We validated everything.
> The notebook has fifty-six checkpoints. All fifty-six pass. No failures, no warnings.
> Look at the error bars. Our measured error is zero point zero two nine.
> Our predicted error bar is zero point zero two eight.
> The ratio is one point zero five. So our error bars are honest. They are not too small.
> And the error falls with the square root of the number of shots. The slope is minus zero
> point four six. Theory says minus zero point five.
> This means we are limited by statistics, not by a hidden mistake.

---

## Slide 4 — The shared-shot punchline (55 s) — Speaker: Su Wei-Chang

> Now the interesting part.
> Energy and magnetisation are conserved. So they should be flat in time.
> We measured the energy as zero point zero seven one, plus or minus zero point zero zero
> eight. The exact value is zero point zero seven four.
> We measured the magnetisation as two point two seven one. The exact value is two point
> two six seven.
> And here is the point. These came from the qubits the standard method throws away.
> No extra circuits, just a few extra single-qubit gates. There is a statistical cost too,
> and we quantify it later in the talk.

---

## Slide 5 — MONEY PLOT (75 s) — Speaker: Tina Tien

> This is our main result.
> The grey band is the plain Fourier transform of the ancilla signal. It is a blur.
> A better estimator sharpens it. But no estimator can colour it.
> The coloured lines are our reconstruction. We recover all four energy levels.
> Our worst energy error is zero point zero three three.
> But look at the colour. The colour is the symmetry sector of each line.
> That information does not exist in the grey curve. It comes from the recycled data.
> And it is reproducible. We ran twelve independent random seeds.
> All twelve got every symmetry label correct. Twelve out of twelve.

*(Pause here. This is the slide to let land.)*

---

## Slide 6 — Real hardware (70 s) — Speaker: Chao Hsien

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

## Slide 7 — Honest cost (50 s) — Speaker: Jiwan Kang

> Nothing is free. Here is the real cost.
> To get the same three observables the conventional way, you need thirteen separate
> experiments.
> We need zero extra circuits.
> We do add a few single-qubit gates. And our estimator is noisier on the recycled
> quantity. We measured that penalty. It is one point zero seven times.
> Seven percent more noise, to replace thirteen experiments.
> And we can predict that noise from theory, to within two percent.

---

## Slide 8 — Reproducibility (45 s) — Speaker: Ng Siu Hin

> Everything is public and reproducible.
> Our repository has pinned versions, a summary file you can compare against your own run,
> and thirty-seven results rows.
> Every single number maps to the exact command that produced it.
> You can reproduce our headline numbers in under five minutes, from saved data.
> If you have quantum hardware access, three commands reproduce our hardware results.

---

## Slide 9 — Limitations (50 s) — Speaker: Su Wei-Chang

> We want to be honest about the limits.
> First. The simple Fourier method never resolves our two closest energy levels. Not at any
> setting we tried. We needed a better estimator, not more shots.
> Second. Our shallow circuit trick only works because our system is small. It gets worse as
> the system grows. It is not a general recipe.
> Third. One of our noise studies came out confounded. We excluded it instead of reporting
> it.

---

## Slide 10 — Team (25 s) — Speaker: Tina Tien

> Finally, our team.
> Chao Hsien opened with the headline scoreboard and the five completed tracks.
> Jiwan Kang covered the question, the anti-control circuit, and Track B validation.
> Ng Siu Hin covered classical shadows and the baselines against the echo and HST.
> Su Wei-Chang covered the AQC compilation win, the phase trap and its fix, and the
> hardware falsification test.
> Tina Tien covered Track B on hardware, our claims and scope, and reproducibility.
> Thank you. We are happy to take questions.

---

## Q&A crib sheet

**"How can the compilation trend succeed at n=7 if hardware fails harder there?"**
> They measure different things. The trend is a *ratio* — exact grows like 4^(n+1), AQC
> roughly linearly, so the relative advantage grows. Hardware survival depends on the
> *absolute* depth of the AQC circuit, which still deepens with n: survival ~ exp(-eps ×
> gates). Both move at once: relative advantage up, absolute feasibility down. From our own
> data the effective error is ~6e-3 per gate at 576 gates; the win becomes visible when
> that reaches ~2e-3 — a factor ~3, which is a device-generation step (Nighthawk's target
> regime), not a protocol fix. [R046, R054]

**"Your AQC headline is n=7 but the hardware run is n=6 — why?"**
> Different questions. n=7 is the last point of the compilation *scaling trend* (gate
> counts only). The hardware test needs the 8,850-gate exact arm alongside as the doomed
> *control*, and that arm dominates QPU time — 602 µs per shot, about 4× more at n=7 on an
> open-plan quota. The contrast was already saturated at n=6 (predicted 3.6e-7 vs 0.32),
> so n=7 would spend 4× the quantum time making a dead arm deader. And since AQC failed at
> n=6, it would only fail harder at n=7 — the choice of n doesn't soften the negative. [R046, R054]


**"Is this faster than a classical computer?"**
> No, and we do not claim that. Our system is three qubits. A laptop solves it instantly.
> It is small on purpose, so we can check every number against the exact answer.

**"What is new here? The paper already exists."**
> The method is from the paper. What is new is the systematic characterisation.
> We measured the cost, found the failure modes, compared four spectral estimators --
> Fourier, matrix pencil, phase estimation, and Krylov -- plus a protocol ablation, and
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

**"Is this the first implementation?"**
> We are not aware of a prior open implementation. We searched on the thirteenth of August
> and found none. But we scoped that search narrowly, so we would not claim priority on it.
> The method is from the paper. What is ours is the characterisation.

**"What would you do next?"**
> Density of states. The same circuit, with the input state swapped for a maximally mixed
> one, measures the density of states instead of one state's spectrum. We prototyped it and
> it works — the peak heights correctly become degeneracies.
> There is a recent paper doing exactly this for fermions. It gets one particle-number
> sector per experiment. Our recycled data could get every sector from a single run,
> because the same shots give us every observable we need. We have checked that is
> feasible. We have not built it yet.

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

### The 8:50 above is STALE and will overrun — re-time before rehearsing

That table covers 10 content slides. The PDF now has **15** content slides plus an outline
and 5 section dividers. The seven not timed above are: *paper Fig. 1*, *what a classical
shadow is*, *the benchmark model*, *what each choice buys*, *four ways to treat the garbage*,
*what the inversion contributes*, *which protocol rebuilds which observable*.

At the script's own pace that is roughly **+3:30 to +4:00**, i.e. a ~12:30 talk against a
10:00 limit. **Someone must decide what to cut**, not discover it on stage. Cheapest cuts,
in order:

1. Drop the section-divider pages (they are `\AtBeginSection`; deleting that block removes
   all five at once) — saves ~25 s and 5 pages.
2. Move *what the inversion contributes* and *four ways to treat the garbage* to backup —
   the observable table already carries the conclusion.
3. Show the paper Fig. 1 slide silently while speaking the hook, rather than narrating it.

Do **not** cut the benchmark-model slide: the observable table on
*which protocol rebuilds which observable* refers back to its hopping term.
