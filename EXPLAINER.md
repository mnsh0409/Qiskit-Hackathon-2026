# What this project does — a plain-language explanation

*Qiskit Hackathon 2026, Topic 5: "In the Shadow of the Hadamard Test"
(based on Faehrmann, Eisert & Kueng, PRL 135, 150603, 2025).*

*Every number quoted below is traceable to a row in RESULTS.md, which records the
command or notebook cell that produced it.*

---

## The one-sentence version

We ran a standard quantum-computing experiment that normally throws away most of
its measurement data, kept the "garbage" instead, and showed that this garbage
contains enough extra information to label the energy levels of a small magnet —
without running a single extra experiment.

---

## The longer version

### 1. The setup: a tiny quantum magnet

Our test subject is a chain of three quantum spins — think of three tiny magnets
in a row that can each point up or down, and that push and pull on each other.
Simulating how such a system evolves over time is one of the core things quantum
computers are expected to be good at.

Some facts about this little system are known exactly (a laptop can compute them
by brute force, because three spins are small). That is the point: we always
have an exact answer sheet to grade ourselves against. The rule we imposed on
ourselves all week: **an estimate only counts if it agrees with the exact answer
within its own error bars, and every claim traces back to a logged run.**

### 2. The standard tool: the Hadamard test

The "Hadamard test" is a classic quantum circuit. You add one extra helper qubit
(an *ancilla*) to your system, entangle it cleverly with the time evolution, and
then measure it. The ancilla's answers — just +1s and −1s — average out to a
number physicists care about: the *signal* χ(t), which encodes the energy
spectrum of the system the way a chord encodes the notes inside it.

Here's the wasteful part: in the standard protocol, **you only read the helper
qubit. The three system qubits get measured too, but their results are treated
as garbage and discarded.**

### 3. The paper's idea: read the garbage

The 2025 paper this challenge is built on makes a simple, clever observation:
if you measure those three "garbage" qubits in randomly chosen directions (a
technique called *classical shadows*), the discarded data is not garbage at all.
From the **same** experimental runs you can extract:

- the original signal χ(t) (from the ancilla, as always),
- the system's energy ⟨H⟩ and magnetisation ⟨Q⟩ (from the garbage alone),
- and — the star of the show — *joint* quantities that combine ancilla and
  garbage, which normally would require a separate, modified experiment for
  every quantity you want.

One experiment, many answers. The extra cost is not zero — the random
measurement settings add bookkeeping, and the shadow estimates are noisier than
dedicated measurements would be — but no *additional circuits or shots* are
needed beyond the ones the standard protocol already runs.

### 4. What we actually did

**Built and validated the machinery (Challenges 1–6).** We implemented the
circuit, the data parsing, and the three estimators, and validated every piece
against exact references before using it. The full experiment was 256,000
simulated measurement shots spread over 64 time points. Highlights:

- The signal χ(t) matched the exact curve everywhere, with honest error bars
  (the measured scatter was 1.05× what the error bars predicted — meaning the
  error bars tell the truth).
- Energy from the garbage data: measured +0.071 ± 0.008 vs. exact +0.074.
- Magnetisation: measured 2.271 ± 0.005 vs. exact 2.267.
- Errors shrank with more measurements exactly at the textbook rate
  (slope −0.46 vs. the ideal −0.5), which is the signature of an unbiased
  estimator with no hidden systematic error.

**Extracted the spectrum with labels (Challenges 7–9).** This is the advanced
deliverable. The signal χ(t) is like a chord made of four notes; each "note" is
an energy level of the magnet. We first tried the honest textbook method (a
Fourier transform), which — exactly as theory predicts — hears only three of
the four notes: the quietest one sits too close to a much louder neighbour.
Then we used a sharper method (the *matrix pencil*, borrowed from radar signal
processing) that models the signal directly instead of binning it, and
recovered **all four energy levels**, each with:

- its energy (accurate to about 0.03, roughly 1% of the full energy range),
- its loudness/weight (accurate to about 0.006),
- and its **magnetisation label** — the quantum number that says which symmetry
  sector the level lives in. This label is precisely the information that comes
  from the garbage register and that the standard Hadamard test cannot provide
  at all.

Every number carries an uncertainty computed by a bootstrap: we re-ran the whole
analysis 200 times on noise-perturbed copies of the data and reported the
spread. Satisfyingly, the weakest note has the biggest error bar on its label
(±0.19) and the loudest has the smallest (±0.02) — the analysis knows what it
doesn't know.

A detail we're proud of: the notebook includes a "tripwire" test that replaces
every piece of code that knows the exact answer with a boobytrap that explodes
if touched, then re-runs our analysis. It produced identical output — proof the
estimator never peeked at the answer sheet.

**Tried it on a real quantum computer.** We sent a small job (4,000 shots) to
IBM's `ibm_marrakesh` processor overnight. The result came back heavily
degraded: the signal was damped to about 18% of its true size, worse than the
~34% that a generic textbook noise model predicts for a circuit this deep
(about 435 two-qubit gates). We report this as-is. It is a real, quantified
finding about hardware noise at this circuit depth — not a success story, and
we don't dress it up as one.

**Bonus (Challenge 10).** The same recorded data also feeds a completely
different algorithm — a "Krylov" energy solver that estimates the lowest
occupied energy level. It is knowingly ill-conditioned (the notebook treats it
as advisory, not graded); our run landed at −1.53 against a true value of
−1.92, within the method's documented instability band, while our main
matrix-pencil method got −1.918 from the same data.

### 5. Why it matters

Measurements on quantum computers are expensive — shots cost time and money,
and on today's noisy hardware you want every drop of information per shot.
This project demonstrates, end to end and with error bars, that a widely used
protocol has been leaving information on the table: data that is routinely
discarded can label a system's energy levels by symmetry sector, at the cost of
only smarter post-processing of shots you were already taking.

### 6. Honesty notes

- All headline results are from an ideal (noiseless) simulator; the one real
  hardware run is reported separately and did not survive the circuit depth.
- Everything comes from **one** shared dataset of 256,000 shots plus small,
  separately-declared side runs (scaling study, noise study, hardware job).
- Uncertainties are bootstrap-based; validation gates were set at 5σ.
- We make no claims about outperforming classical computers — a laptop solves
  this three-spin system instantly. The system is small *on purpose*, so that
  every estimate could be graded against an exact answer.
