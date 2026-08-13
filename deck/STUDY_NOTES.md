# Study notes — for teammates new to this topic

Read time ~25 minutes. Goal: after reading, you can follow every slide of
`trackb.pdf`, answer the obvious questions, and know which numbers are
memorable. Nothing here requires prior quantum-information background beyond
"a qubit is a two-level system and circuits apply gates to it."

Companion documents: `EXPLAINER.md` (gentler, non-specialist), `RESULTS.md`
(every number's source row), `deck/SPEAKER_SCRIPT.md` §Q&A (rehearsed answers).

---

## 0. The one-paragraph version

The Hadamard test is a standard circuit that measures one helper qubit (the
*ancilla*) to extract a number χ(t) from a quantum system — and throws the rest
of the qubits away as "garbage." A 2025 paper (Faehrmann, Eisert & Kueng, PRL
135, 150603) pointed out you can measure that garbage in random bases and get
extra information for free. Our project implements that idea, extends it
(Track B: compare *two* dynamics in one circuit), makes the expensive part
cheap with a circuit compiler (AQC), finds and fixes a trap that silently
breaks the whole scheme, and then tests everything on real quantum computers —
including the test that *failed*, which we report with the same prominence as
the wins.

---

## 1. The Hadamard test (slide: "You compiled U…", appendix A1–A2)

**What it computes.** For a state |ψ⟩ and evolution U, the complex number
χ = ⟨ψ|U|ψ⟩. Its magnitude says "how much does U leave ψ alone"; its **phase**
carries the dynamics (energies live in phases: U = e^{−iHt}).

**How.** Put the ancilla in a superposition (Hadamard gate), apply U to the
system *only if* the ancilla is |1⟩ (controlled-U), interfere (second
Hadamard), measure the ancilla. Then ⟨Z_ancilla⟩ = Re χ. Repeat with a small
phase gate (φ = −π/2) to get Im χ.

**The one thing to internalise:** the Hadamard test is an *interferometer*.
Anything blind to phase — a magnitude, a fidelity — is blind to what this
circuit measures. That single sentence explains three separate findings below.

**Memorise:** χ is complex; |χ| ≤ 1 always. If a measurement reports |χ| > 1,
the experiment is broken, full stop (this happens on slide "We ran it on a
QPU" — deliberately shown).

---

## 2. Classical shadows (slide: "First, what a classical shadow is", A4)

**Problem it solves.** Measuring a qubit destroys it, and one measurement basis
gives one kind of information. If you fix a basis in advance, you can only ever
estimate observables diagonal in that basis.

**The trick.** Each shot, pick each qubit's basis (X, Y or Z) *at random*, and
store just `(bases, outcomes)`. A weight-w Pauli observable (one acting
non-trivially on w qubits) matches the drawn bases with probability 3^−w;
multiply matching shots by 3^w and average. The estimator is *unbiased for
every Pauli at once* — you did not have to choose what to measure in advance.

**The price.** Variance = 3^w per shot. Low-weight observables are cheap;
weight-n observables are exponentially expensive. Our project measured this
model to be exact within 2% [R029].

**In this project:** the garbage register of the Hadamard test is measured this
way. Tagging each shadow shot with the ancilla outcome (±1) links the system
information to the interference signal.

---

## 3. Track B: the anti-controlled Hadamard test (slides "Anti-control…",
   "Track B…", "What the shadows add"; A1–A3, A5)

**The question it answers.** You want to run U but can only afford an
approximation W (a Trotterised circuit, a compiled circuit). How wrong is W —
and wrong *in what*?

**The circuit change.** Sandwich the controlled-W between two X gates on the
ancilla. X flips |0⟩↔|1⟩, so the sandwich makes W fire on the |0⟩ branch while
the ordinary controlled-U fires on the |1⟩ branch. The ancilla now interferes
*two dynamics*:  ⟨Z_a⟩_φ = Re[e^{iφ} ⟨ψ|W†U|ψ⟩]. Setting W = identity gives
back the standard test — Track B strictly generalises it.

**Our completion (the part the scaffold left open).** Delete the *final*
Hadamard. Then, of the shadow data: the plain average estimates
(WρW† + UρU†)/2 — the SUM — and the ancilla-weighted average estimates
(WρW† − UρU†)/2 — the DIFFERENCE. Add and subtract: you get every observable
under W and under U *separately*, from one circuit family. Validated to
4×10⁻¹⁵ [R042].

**Slogan (use it in Q&A):** *the ancilla says how much W is wrong; the garbage
says which observable it got wrong.*

**Honest context [R043, R044]:** if you only want the scalar "how close is W to
U", the *Loschmidt echo* (run U forward, W backward, measure the probability of
returning to start — ~2 gates here) is 4–6× cheaper and, on hardware, 27× more
accurate than our arm. The *Hilbert–Schmidt test* answers a state-independent
version on 2n qubits. Our arm earns its keep only through the phase and the
per-observable profile. The deck says this out loud — do not soften it, it is
our credibility.

---

## 4. AQC and the crossover (slide "AQC makes it scale"; R046, R049, R051, R052)

**The bottleneck.** The textbook way to build controlled-U for an arbitrary U
synthesises a (n+1)-qubit unitary: cost ~4^(n+1) two-qubit gates. Doubling from
n=3 to n=6 takes you from 50 to 4,140 gates (8,850 after routing to a real
chip).

**AQC (Approximate Quantum Compiling).** A classical optimiser (tensor-network
based) finds a *shallow* circuit whose action on your state matches the deep
one. Its cost grows roughly linearly in n. Hence a crossover: exact wins below
n=4, AQC wins above — 36× fewer gates by n=7, at state infidelity ~3×10⁻⁴.
The advantage survives 2D lattices, the Fermi–Hubbard model (crossover shifts
to 6 qubits), and real heavy-hex routing — routing actually *widens* the gap,
because the dense exact block routes worse than the shallow local ansatz.

**One scope caveat to remember:** AQC compresses the action on *one input
state* (process infidelity ~0.96!). Fine for a Hadamard test — the controlled
gate only ever sees that state. Illegal anywhere else.

---

## 5. The phase trap — the intellectual heart of the deck (slide "The trap";
   R046, R053, R054)

AQC maximises **state fidelity** |⟨ψ_target|ψ_ansatz⟩| — a *magnitude*. The
Hadamard test measures a *phase* (§1). So a compression can converge perfectly
by its own metric and return W|ψ⟩ = e^{iθ}U|ψ⟩ with θ up to ~3 radians: χ comes
out wrong by ~1.3 on a quantity bounded by 1. **The error is as large as the
signal, and no fidelity number warns you.**

**The fix:** θ is computable for free during compilation; apply P(−θ) — one
single-qubit phase gate — on the ancilla. Error drops 1.33 → 0.008.

**Why we call it a pattern, not an incident — three independent sightings:**
1. The compiler's objective (above) [R046].
2. A summary statistic: "survival" = |χ_measured|/|χ_exact| looked near-perfect
   (0.988) on a teammate's `ibm_miami` run whose *complex* χ was 22.6σ wrong
   [R053].
3. Our own hardware run: the deadest circuit (8,850 gates, ancilla fully
   relaxed) got the *best* survival score, 1.485 — unphysical, since |χ| ≤ 1
   [R054].

**Q&A soundbite:** *a Hadamard test is an interferometer; any magnitude-only
figure of merit is structurally blind to what it measures.*

---

## 6. The hardware reality check (slides "We ran it on a QPU", "First Track B
   on a QPU", "free error bar"; R044, R054, R055)

**Design.** Same Hadamard test at n=6, three ways to build the controlled
evolution (exact 8,850 routed gates / Trotter 2,119 / AQC 576), one job per
device, survival predictions written down *before* submission — so failure
would be undeniable, and it was: every arm on both `ibm_marrakesh` and
`ibm_kingston` returned noise; the AQC arm hit 0.026/0.033 against predicted
0.315/0.401 — 12× short on both.

**The post-mortem number to remember:** effective error per two-qubit gate,
bounded from data: ε_eff ≥ −ln(S)/N ≈ 6×10⁻³ (a lower bound — the measured |χ| sits
near the estimator's noise floor ~0.020 at these shots) — about 3–4× the *calibrated*
gate error. Ancilla dephasing (T₂) explains part; a ~7× residual is honestly
labelled unattributed. The win becomes visible when ε_eff ≲ 2×10⁻³ — roughly
one device generation away (Nighthawk's target regime). Full arithmetic:
appendix A7.

**Why n=6 and not n=7:** the deliberately-dead exact *control* arm dominates
cost (602 µs/shot; ~4× more at n=7) and the contrast was already saturated.
"Doubles the headline, halves the signal, quadruples the bill." [R055]

**The one clean hardware win:** ⟨Q⟩_W − ⟨Q⟩_U ≡ 0 exactly (charge conservation
survives Trotterisation), so its measured deviation is pure device error —
an error bar with no reference state, no simulation. [R044]

---

## 7. Numbers worth memorising (all sourced)

| number | what it is | row |
|---|---|---|
| 36× | AQC gate reduction at n=7 (compilation) | R046 |
| n=4 | AQC/exact crossover | R046 |
| 1.33 → 0.008 | χ error before/after the one-gate phase fix | R046 |
| 0.026 / 0.033 vs 0.315 / 0.401 | measured vs pre-registered AQC survival, two QPUs | R054 |
| 1.485 | the unphysical "survival" of a dead circuit | R054 |
| ~6×10⁻³ vs ≲2×10⁻³ | effective error today vs what visibility needs | R054/A7 |
| 27× | how much the 2-gate echo beats our arm on hardware | R044 |
| 4×10⁻¹⁵ | Track B identity validation | R042 |
| 12/12 | seeds correct on the Track A deliverable | R019 |
| 56/56 | notebook checkpoints passing | — (README) |

## 8. Glossary (30 seconds each)

- **ancilla** — the helper qubit whose measurement carries the interference.
- **χ (chi)** — ⟨ψ|U|ψ⟩; complex; |χ| ≤ 1.
- **quadrature** — the φ=0 / φ=−π/2 runs giving Re χ and Im χ.
- **Pauli weight w** — number of qubits an observable touches; shadows pay 3^w.
- **Trotterisation** — approximating e^{−iHt} by products of small steps.
- **routing / transpiling** — mapping a circuit onto a chip's actual layout;
  inserts SWAPs, increases gate count.
- **T₁ / T₂** — decay times: energy relaxation / phase coherence. Circuit time
  beyond these ⇒ the qubit forgets.
- **survival** — |χ_measured|/|χ_exact|. Useful, but magnitude-only: treat any
  survival quoted *without* the complex χ with suspicion (that is our own
  lesson, thrice).
- **pre-registered** — prediction recorded before the experiment ran, so the
  outcome can falsify it.
- **effective error ε_eff** — −ln(survival)/gate-count: the per-gate error the
  device *behaved* as having, all noise sources folded in.

## 9. If a judge asks you and you don't know

Say: "That's in our results ledger — every number on the slides has a row tag,
and the row lists the command that produced it. I can pull it up." That answer
is always true, always safe, and demonstrates the project's core discipline.
The rehearsed answers for the hard questions (n=6 vs n=7, ratio vs absolute,
the priority claim, "did you try SKQD?") are in `SPEAKER_SCRIPT.md` §Q&A.
