# Claims table (generated - do not edit; regenerate instead)
# 180 claims, 127 untagged -> UNSUPPORTED by default

| C## | file:line | tags | claim | verdict |
|---|---|---|---|---|
| C001 | deck/slides_content.md:1 | - | slides_content.md — the presented deck, slide by slide (C6) | |
| C002 | deck/slides_content.md:3 | - | Spine:** the 10-slide arc in `deck_arc.md`, adapted — not reinvented — to the | |
| C003 | deck/slides_content.md:4 | - | Mapping: arc-1 hook → S1–S2; arc-2 | |
| C004 | deck/slides_content.md:5 | - | circuit/estimators → S5–S7; arc-3 validation → S6; arc-4 same-shots punchline → | |
| C005 | deck/slides_content.md:6 | - | S7, S13; arc-5 money plot → S10; arc-6 systematics → S11–S12; arc-7 honest cost | |
| C006 | deck/slides_content.md:7 | - | → S9; arc-8 repo QR → S16; arc-9 limitations → S14; arc-10 team → S17. | |
| C007 | deck/slides_content.md:10 | - | Speaker owners are TBD-C6** (roster + English comfort not supplied). | |
| C008 | deck/slides_content.md:16 | - | S1 — Making the Hadamard test scale | |
| C009 | deck/slides_content.md:17 | R046,R046,R042 | 36× fewer gates with AQC [R046]; a phase trap that would have broken it [R046]; certified from its own garbage [R042] | |
| C010 | deck/slides_content.md:18 | - | Team 8 — Garbage Collectors (fill TBD-NAME ×3 before export) | |
| C011 | deck/slides_content.md:20 | - | speaker: TBD-C6-A | |
| C012 | deck/slides_content.md:22 | - | S2 — The result, up front | |
| C013 | deck/slides_content.md:23 | R046,R046 | 36× (compilation, n=7) [R046] · 1 gate fixes the phase trap, \|Δχ\| 1.33→0.008 [R046] | |
| C014 | deck/slides_content.md:24 | R054 | 2 QPUs, same verdict: measured 0.026/0.033 vs pre-registered 0.315/0.401 [R054] | |
| C015 | deck/slides_content.md:25 | R044 | ⟨Q⟩_W−⟨Q⟩_U ≡ 0 ⇒ a device-error bar at no additional circuits [R044] | |
| C016 | deck/slides_content.md:27 | - | speaker: TBD-C6-A | |
| C017 | deck/slides_content.md:29 | - | S3 — Where this sits: the five tracks in the challenge | |
| C018 | deck/slides_content.md:30 | R019 | All five tracks done; Track A (mandatory): 12/12 seeds, every label correct [R019] | |
| C019 | deck/slides_content.md:31 | - | This deck is Track B — taken past the scaffold, onto 2 QPUs, into compilation [R034, R042, R044] | |
| C020 | deck/slides_content.md:33 | - | speaker: TBD-C6-A | |
| C021 | deck/slides_content.md:35 | - | S4 — You compiled U into something cheaper. | |
| C022 | deck/slides_content.md:36 | - | Every practical simulation runs an approximation W, not U | |
| C023 | deck/slides_content.md:38 | R034 | Track B answers on-device: χ_AB(t) = ⟨ψ\|W†U\|ψ⟩ [R034] | |
| C024 | deck/slides_content.md:40 | - | speaker: TBD-C6-A | |
| C025 | deck/slides_content.md:42 | - | S5 — Anti-control: how the Hadamard test is extended | |
| C026 | deck/slides_content.md:43 | - | X–cW–X sandwich: W fires on \|0⟩, U on \|1⟩ — two dynamics on one ancilla | |
| C027 | deck/slides_content.md:44 | - | Everything downstream unchanged; algebra in appendix A1–A2 | |
| C028 | deck/slides_content.md:46 | - | speaker: TBD-C6-B | |
| C029 | deck/slides_content.md:48 | - | S6 — Track B: anti-controlled Hadamard test (validation) | |
| C030 | deck/slides_content.md:49 | - | New circuit ⇒ own validation: identity to 8.99e-15 (3-site) and 4.56e-15 (2-site) [R034, R042] | |
| C031 | deck/slides_content.md:50 | R042 | This check caught an endianness bug before any QPU time [R042] | |
| C032 | deck/slides_content.md:52 | - | speaker: TBD-C6-B | |
| C033 | deck/slides_content.md:54 | - | S7 — First, what a classical shadow is / delete the final Hadamard | |
| C034 | deck/slides_content.md:55 | R029 | Random basis per shot ⇒ one record estimates every Pauli; variance 3^w [R029] | |
| C035 | deck/slides_content.md:56 | R042 | Deleting the final H splits shadows into (WρW†±UρU†)/2 ⇒ ⟨O⟩_W and ⟨O⟩_U separately [R042] | |
| C036 | deck/slides_content.md:59 | - | speaker: TBD-C6-B | |
| C037 | deck/slides_content.md:61 | - | S8 — We are not the only way to do this — and not the cheapest | |
| C038 | deck/slides_content.md:62 | R043 | Loschmidt echo and Hilbert–Schmidt test implemented and verified first [R043] | |
| C039 | deck/slides_content.md:64 | - | speaker: TBD-C6-B | |
| C040 | deck/slides_content.md:66 | - | S9 — The honest scoreboard | |
| C041 | deck/slides_content.md:67 | R043 | The echo is 4–6× cheaper at every n we measured [R043] | |
| C042 | deck/slides_content.md:68 | - | Our arm is justified by what it returns: phase + per-observable profile [R042, R043] | |
| C043 | deck/slides_content.md:70 | - | speaker: TBD-C6-B | |
| C044 | deck/slides_content.md:72 | - | S10 — AQC makes it scale — crossover at n=4, 36× by n=7 (MONEY PLOT) | |
| C045 | deck/slides_content.md:73 | R046 | Exact block ~4^(n+1); AQC ~linear; crossover measured at n=4 [R046] | |
| C046 | deck/slides_content.md:74 | R049,R051,R052 | Survives 2D (100.8× at n=8) [R049], Fermi–Hubbard (34.7×) [R051], routing widens it [R052] | |
| C047 | deck/slides_content.md:76 | - | speaker: TBD-C6-C | |
| C048 | deck/slides_content.md:78 | - | S11 — The trap: a phase-blind compiler breaks a phase interferometer | |
| C049 | deck/slides_content.md:79 | R046 | State fidelity is a magnitude; a Hadamard test measures phase ⇒ χ wrong by 2.3–3.0 rad [R046] | |
| C050 | deck/slides_content.md:80 | R046 | One ancilla P(−θ): \|Δχ\| 1.33 → 0.008 [R046] | |
| C051 | deck/slides_content.md:81 | R053 | Same magnitude-hides-phase failure seen on ibm_miami data [R053] | |
| C052 | deck/slides_content.md:83 | - | speaker: TBD-C6-C | |
| C053 | deck/slides_content.md:85 | - | S12 — We ran it on a QPU. | |
| C054 | deck/slides_content.md:86 | R054 | Pre-registered 0.315/0.401; measured 0.026/0.033; every arm, both devices: noise [R054] | |
| C055 | deck/slides_content.md:87 | R054 | The dead 8,850-gate arm scores "survival" 1.485 — unphysical (\|χ\|≤1): a T1 floor [R054] | |
| C056 | deck/slides_content.md:88 | R055 | Why n=6 not n=7: control arm dominates cost; arithmetic in appendix A7 [R055] | |
| C057 | deck/slides_content.md:90 | - | speaker: TBD-C6-C | |
| C058 | deck/slides_content.md:92 | - | S13 — First Track B on a QPU / the free error bar | |
| C059 | deck/slides_content.md:93 | R044 | 2-gate echo beats our 136-gate arm 27× on hardware [R044] | |
| C060 | deck/slides_content.md:94 | R044 | ⟨Q⟩_W−⟨Q⟩_U ≡ 0 by conservation ⇒ measured deviation is pure device error, no reference [R044] | |
| C061 | deck/slides_content.md:96 | - | speaker: TBD-C6-C | |
| C062 | deck/slides_content.md:98 | - | S14 — What we claim, and what we do not | |
| C063 | deck/slides_content.md:99 | R046,R042 | Claim: compilation win [R046, R052], trap+fix [R046], Track B completed [R042], QPU tests [R044, R054] | |
| C064 | deck/slides_content.md:100 | R054 | Do NOT claim: the gate-count win reaches hardware [R054]; anything vs classical computation | |
| C065 | deck/slides_content.md:102 | - | speaker: TBD-C6-A | |
| C066 | deck/slides_content.md:104 | - | S15 — Future work: density of states | |
| C067 | deck/slides_content.md:105 | R045 | ρ = 1/d turns the same circuit into a DOS estimator (W=I special case) [R045] | |
| C068 | deck/slides_content.md:107 | - | speaker: TBD-C6-A | |
| C069 | deck/slides_content.md:109 | - | S16 — Reproduce it | |
| C070 | deck/slides_content.md:110 | - | 50+ sourced rows; scripts reproduce every hardware number; bug log incl. retractions | |
| C071 | deck/slides_content.md:112 | - | speaker: TBD-C6-A | |
| C072 | deck/slides_content.md:114 | - | S17 — Team (arc-10) | |
| C073 | deck/slides_content.md:115 | - | TBD-NAME ×3 with who-built-what (must map to who spoke) — human fill before export | |
| C074 | deck/slides_content.md:117 | - | speaker: all | |
| C075 | deck/slides_content.md:119 | - | Backup (never presented, Q&A jumps only): appendix A1–A7 in trackb.pdf; the | |
| C076 | deck/slides_content.md:121 | - | `figures/07_symmetry_resolved_spectrum.png` [R012, R013] if a judge asks for it. | |
| C077 | deck/script.md:1 | - | script.md — per-member speaking blocks (C6) | |
| C078 | deck/script.md:3 | - | Talk length: TBD-C6** (not supplied). | |
| C079 | deck/script.md:4 | - | working assumption of **10:00 with 10% slack ⇒ 9:00 of speech**; if the real | |
| C080 | deck/script.md:6 | - | TBD-C6** — blocks are labelled A/B/C; assign so that the strongest English | |
| C081 | deck/script.md:10 | - | Numbers rule: every number below is grep-verified against RESULTS.md and | |
| C082 | deck/script.md:19 | - | Block A1 — open (S1–S4) — TBD-C6-A — 2:30 | |
| C083 | deck/script.md:21 | - | We are Team 8, the Garbage Collectors. | |
| C084 | deck/script.md:27 | R046 | [R046]. | |
| C085 | deck/script.md:27 | R046 | One single-qubit gate to fix an error larger than the signal [R046]. | |
| C086 | deck/script.md:29 | R054 | twelve times [R054]. | |
| C087 | deck/script.md:29 | - | And one identity that is exactly zero, which hands us a | |
| C088 | deck/script.md:30 | R044 | device-error bar with no extra circuits [R044]. | |
| C089 | deck/script.md:32 | - | We completed all five — the mandatory one at | |
| C090 | deck/script.md:33 | R019 | twelve out of twelve seeds [R019]. | |
| C091 | deck/script.md:36 | - | Every real simulation runs a cheap | |
| C092 | deck/script.md:38 | - | That is exactly what you cannot do | |
| C093 | deck/script.md:41 | - | Block B — the instrument and its rivals (S5–S9) — TBD-C6-B — 3:10 | |
| C094 | deck/script.md:48 | - | fourteen on two models [R034, R042] — and that check caught a real endianness | |
| C095 | deck/script.md:49 | R042 | bug before it ever reached a quantum processor [R042]. | |
| C096 | deck/script.md:52 | - | One record set then estimates every Pauli observable at once, at a | |
| C097 | deck/script.md:53 | - | variance of three to the weight — a model we verified to within two percent | |
| C098 | deck/script.md:54 | R029 | [R029]. | |
| C099 | deck/script.md:56 | - | and subtract — you get every observable under W and under U separately | |
| C100 | deck/script.md:57 | R042 | [R042]. | |
| C101 | deck/script.md:62 | R043 | [R043]. | |
| C102 | deck/script.md:63 | R043 | cheaper at every size we measured [R043]. | |
| C103 | deck/script.md:67 | - | Block C — the win, the trap, the verdict (S10–S13) — TBD-C6-C — 3:20 | |
| C104 | deck/script.md:72 | R046 | times ten to the minus four [R046]. | |
| C105 | deck/script.md:72 | R049 | That survives a 2D lattice [R049], the | |
| C106 | deck/script.md:73 | R051 | Fermi–Hubbard model [R051], and real device routing — which widens the gap | |
| C107 | deck/script.md:74 | R052 | [R052]. | |
| C108 | deck/script.md:77 | - | The compression converges | |
| C109 | deck/script.md:79 | R046 | as the signal [R046]. | |
| C110 | deck/script.md:80 | R046 | point three three down to zero point zero zero eight [R046]. | |
| C111 | deck/script.md:82 | R053 | data [R053], and once, as you will now see, in our own. | |
| C112 | deck/script.md:85 | - | Every arm came back as noise | |
| C113 | deck/script.md:86 | R054 | — ours twelve times below its own prediction [R054]. | |
| C114 | deck/script.md:87 | - | circuit got the best score: survival one point four eight five. | |
| C115 | deck/script.md:89 | R054 | magnitude-only metric crowns it the winner [R054]. | |
| C116 | deck/script.md:89 | - | We know exactly what error | |
| C117 | deck/script.md:90 | R055 | rate changes this verdict; the arithmetic is in appendix A-seven [R055]. | |
| C118 | deck/script.md:93 | R044 | twenty-seven times on hardware [R044]. | |
| C119 | deck/script.md:94 | - | difference that must be exactly zero, so its measured value is pure device | |
| C120 | deck/script.md:95 | R044 | error — an error bar with no reference state and no simulation [R044]. | |
| C121 | deck/script.md:97 | - | Block A2 — close (S14–S17) — TBD-C6-A — 1:20 | |
| C122 | deck/script.md:102 | R054 | not [R054] — and nothing against classical computation; the benchmark is | |
| C123 | deck/script.md:103 | - | small on purpose, so every number is graded against truth. | |
| C124 | deck/script.md:106 | R045 | mixed input becomes a density-of-states estimator [R045]. | |
| C125 | deck/script.md:109 | - | log including our own retractions, and the scripts behind every hardware | |
| C126 | deck/script.md:110 | - | number. [Team slide: each member states their part — TBD-NAME ×3.] | |
| C127 | deck/script.md:115 | - | Timing (assumes 10:00 slot — TBD-C6) | |
| C128 | deck/script.md:119 | - | \| A1 open \| TBD-C6-A \| 2:30 \| 2:30 \| | |
| C129 | deck/script.md:120 | - | \| B instrument \| TBD-C6-B \| 3:10 \| 5:40 \| | |
| C130 | deck/script.md:121 | - | \| C win/trap/verdict \| TBD-C6-C \| 3:20 \| 9:00 \| | |
| C131 | deck/script.md:122 | - | \| A2 close \| TBD-C6-A \| 1:20 \| **10:20** \| | |
| C132 | deck/script.md:124 | - | 10:20 spoken against 10:00 is deliberate: the cut list brings it under with one | |
| C133 | deck/script.md:125 | - | item. **Cuts, in order:** (1) S15 DOS sentence −0:20; (2) shadow primer half of | |
| C134 | deck/script.md:126 | - | S7 −0:40, only for an expert room; (3) merge S8 into S9 −0:30. **Never cut:** | |
| C135 | deck/script.md:127 | - | S11 the trap, S12 the failure, S14 the claims. | |
| C136 | deck/script.md:128 | - | 5:45 or apply cut 1 immediately. | |
| C137 | deck/qa_crib.md:1 | - | qa_crib.md — 10 likely judge questions, 2-line answers (C6) | |
| C138 | deck/qa_crib.md:4 | - | "Every number on our slides carries a ledger row with the producing command — | |
| C139 | deck/qa_crib.md:7 | - | 1. | |
| C140 | deck/qa_crib.md:7 | - | Your headline says n=7 but the hardware ran n=6 — why?** | |
| C141 | deck/qa_crib.md:8 | R046 | n=7 is the last point of the compilation trend [R046]. | |
| C142 | deck/qa_crib.md:9 | - | deliberately-dead 8,850-gate control that dominates cost — ~4× more at n=7 for zero added | |
| C143 | deck/qa_crib.md:10 | R055 | contrast; the full arithmetic is appendix A7 [R055]. | |
| C144 | deck/qa_crib.md:12 | - | 2. | |
| C145 | deck/qa_crib.md:12 | - | How can compilation "succeed" at n=7 if hardware "fails harder" there?** | |
| C146 | deck/qa_crib.md:13 | - | The trend is a ratio (exact ~4^(n+1) over AQC ~linear); hardware survival decays with the | |
| C147 | deck/qa_crib.md:14 | - | Measured effective error is ~6e-3/gate; | |
| C148 | deck/qa_crib.md:15 | - | visibility needs ~2e-3 — one device generation, not a protocol change [R054, R055]. | |
| C149 | deck/qa_crib.md:17 | - | 3. | |
| C150 | deck/qa_crib.md:17 | - | Isn't the Loschmidt echo simply better?** | |
| C151 | deck/qa_crib.md:18 | - | For the scalar overlap, yes — 4–6× cheaper and 27× more accurate on hardware; we say so on | |
| C152 | deck/qa_crib.md:19 | - | the slide [R043, R044]. | |
| C153 | deck/qa_crib.md:19 | - | It returns one magnitude; only our arm returns the phase and the | |
| C154 | deck/qa_crib.md:20 | R042 | per-observable breakdown [R042]. | |
| C155 | deck/qa_crib.md:22 | - | 4. | |
| C156 | deck/qa_crib.md:23 | - | Gate error plus ancilla dephasing predicts 0.186; measured | |
| C157 | deck/qa_crib.md:24 | - | 0.026 — a ~7× residual we label unattributed (candidates: layout edges, crosstalk, coherent | |
| C158 | deck/qa_crib.md:25 | R054 | error) rather than invent a cause [R054]. | |
| C159 | deck/qa_crib.md:27 | - | 5. | |
| C160 | deck/qa_crib.md:27 | - | Why believe the 36× at all, after the hardware negative?** | |
| C161 | deck/qa_crib.md:28 | - | They are different claim types: 36× is a transpiled gate count, deterministic and | |
| C162 | deck/qa_crib.md:29 | - | reproducible from the repo [R046, R052]; the negative is about today's error rates, and we | |
| C163 | deck/qa_crib.md:30 | R054 | pre-registered both predictions so neither claim can quietly absorb the other [R054]. | |
| C164 | deck/qa_crib.md:32 | - | 6. | |
| C165 | deck/qa_crib.md:32 | - | The compressed circuit's process infidelity is 0.96 — isn't that disqualifying?** | |
| C166 | deck/qa_crib.md:33 | - | A Hadamard test's controlled gate acts on exactly one prepared | |
| C167 | deck/qa_crib.md:35 | - | any other input is illegitimate [R046, R051]. | |
| C168 | deck/qa_crib.md:37 | - | 7. | |
| C169 | deck/qa_crib.md:38 | - | No — diagnostic only. | |
| C170 | deck/qa_crib.md:39 | - | rests on uniform random bases; that failure class is documented in our bug log (B04) | |
| C171 | deck/qa_crib.md:40 | - | [R044, R036]. | |
| C172 | deck/qa_crib.md:42 | - | 8. | |
| C173 | deck/qa_crib.md:44 | - | hopping-dominated (Δ/J=0.38, needs 86.6% of the sector); at Δ/J=5 it needs 2.7%, and the | |
| C174 | deck/qa_crib.md:45 | - | same boundary reappears on 2D Fermi–Hubbard in U/t. | |
| C175 | deck/qa_crib.md:46 | - | keep on real shots [R047, R050, R037]. | |
| C176 | deck/qa_crib.md:48 | - | 9. | |
| C177 | deck/qa_crib.md:48 | - | Is this really the first open implementation of the PRL?** | |
| C178 | deck/qa_crib.md:53 | - | 10. | |
| C179 | deck/qa_crib.md:54 | - | The benchmark is 2–7 qubits, diagonalisable on a laptop — deliberately, so every | |
| C180 | deck/qa_crib.md:55 | - | estimate is graded against exact truth; our claims are about measurement protocols and | |
