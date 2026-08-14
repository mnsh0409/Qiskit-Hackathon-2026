# qa_crib.md — 10 likely judge questions, 2-line answers (C6)

Longer rehearsed versions: `SPEAKER_SCRIPT.md` §Q&A. Universal fallback:
"Every number on our slides carries a ledger row with the producing command —
I can pull it up." Always true; buys ten seconds.

**1. Your headline says n=7 but the hardware ran n=6 — why?**
n=7 is the last point of the compilation trend [R046]. The hardware job carries a
deliberately-dead 8,850-gate control that dominates cost — ~4× more at n=7 for zero added
contrast; the full arithmetic is appendix A7 [R055].

**2. How can compilation "succeed" at n=7 if hardware "fails harder" there?**
The trend is a ratio (exact ~4^(n+1) over AQC ~linear); hardware survival decays with the
AQC circuit's absolute depth, which still grows. Measured effective error is ~6e-3/gate;
visibility needs ~2e-3 — one device generation, not a protocol change [R054, R055].

**3. Isn't the Loschmidt echo simply better?**
For the scalar overlap, yes — 4–6× cheaper and 27–32× more accurate on hardware (the gap
widens over a 2×-extended time window); we say so on the slide [R043, R044, R059]. It
returns one magnitude; only our arm returns the phase and the per-observable breakdown [R042].

**4. Do you actually know why the AQC arm failed on hardware?**
Partially, and we say which part. Gate error plus ancilla dephasing predicts 0.186; measured
0.026 — a ~7× residual we label unattributed (candidates: layout edges, crosstalk, coherent
error) rather than invent a cause [R054].

**5. Why believe the 36× at all, after the hardware negative?**
They are different claim types: 36× is a transpiled gate count, deterministic and
reproducible from the repo [R046, R052]; the negative is about today's error rates, and we
pre-registered both predictions so neither claim can quietly absorb the other [R054].

**6. The compressed circuit's process infidelity is 0.96 — isn't that disqualifying?**
It would be anywhere else. A Hadamard test's controlled gate acts on exactly one prepared
state, and AQC is compressed against that state; we state on the slide that reusing it on
any other input is illegitimate [R046, R051].

**7. Can the ⟨Q⟩ error bar be used to correct the data?**
No — diagnostic only. Post-selecting on it biases the shadow estimator, whose unbiasedness
rests on uniform random bases; that failure class is documented in our bug log (B04)
[R044, R036].

**8. Did you try SKQD / sample-based diagonalisation?**
Yes — and mapped where it works: it needs a localised ground state. Our benchmark is
hopping-dominated (Δ/J=0.38, needs 86.6% of the sector); at Δ/J=5 it needs 2.7%, and the
same boundary reappears on 2D Fermi–Hubbard in U/t. Configuration recovery did earn its
keep on real shots [R047, R050, R037].

**9. Is this really the first open implementation of the PRL?**
We searched and found none, with the scope recorded and date-stamped in the repo; we would
not defend priority if challenged — the characterisation (costs, failure boundaries,
hardware) is ours either way [PRIOR_ART_SEARCH.md, SRCH].

**10. Do you claim any speedup over classical methods?**
No. The benchmark is 2–7 qubits, diagonalisable on a laptop — deliberately, so every
estimate is graded against exact truth; our claims are about measurement protocols and
circuit costs, not classical intractability.
