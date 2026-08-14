# slides_content.md — the presented deck, slide by slide (C6)

**Spine:** the 10-slide arc in `deck_arc.md`, adapted — not reinvented — to the
Track B story the team chose to present. Mapping: arc-1 hook → S1–S2; arc-2
circuit/estimators → S5–S7; arc-3 validation → S6; arc-4 same-shots punchline →
S7, S13; arc-5 money plot → S10; arc-6 systematics → S11–S12; arc-7 honest cost
→ S9; arc-8 repo QR → S16; arc-9 limitations → S14; arc-10 team → S17.
The rendered deck is `trackb.pdf`; humans assembling a .pptx work from THIS file.

**Team size: FIVE (confirmed); names TBD.** Owners below map to the contiguous
blocks M1–M5 in `deck/script.md`; the rubric scores whether everyone speaks.
Strongest English speaker → M4.

---

## S1 — Making the Hadamard test scale
- 36× fewer gates with AQC [R046]; a phase trap that would have broken it [R046]; certified from its own garbage [R042]
- Team 8 — Garbage Collectors: Chao Hsien, Jiwan Kang, Ng Siu Hin, Su Wei-Chang, Tina Tien
- figure: none (title)
- speaker: Chao Hsien (block M1)

## S2 — The result, up front
- 36× (compilation, n=7) [R046] · 1 gate fixes the phase trap, |Δχ| 1.33→0.008 [R046]
- 2 QPUs, same verdict: measured 0.026/0.033 vs pre-registered 0.315/0.401 [R054]
- ⟨Q⟩_W−⟨Q⟩_U ≡ 0 ⇒ a device-error bar at no additional circuits [R044]
- figure: none (big-number scoreboard, layout in trackb.tex)
- speaker: Chao Hsien (block M1)

## S3 — Where this sits: the five tracks in the challenge
- All five tracks done; Track A (mandatory): 12/12 seeds, every label correct [R019]
- This deck is Track B — taken past the scaffold, onto 2 QPUs, into compilation [R034, R042, R044]
- figure: none (table)
- speaker: Chao Hsien (block M1)

## S4 — You compiled U into something cheaper. Is it still right?
- Every practical simulation runs an approximation W, not U
- The question that decides everything: how wrong, and wrong in *what*?
- Track B answers on-device: χ_AB(t) = ⟨ψ|W†U|ψ⟩ [R034]
- figure: none (framed statement)
- speaker: Jiwan Kang (block M2)

## S5 — Anti-control: how the Hadamard test is extended
- X–cW–X sandwich: W fires on |0⟩, U on |1⟩ — two dynamics on one ancilla
- Everything downstream unchanged; algebra in appendix A1–A2
- figure: deck/fig_tb_anticontrol.png
- speaker: Jiwan Kang (block M2)

## S6 — Track B: anti-controlled Hadamard test (validation)
- New circuit ⇒ own validation: identity to 8.99e-15 (3-site) and 4.56e-15 (2-site) [R034, R042]
- This check caught an endianness bug before any QPU time [R042]
- figure: none (validation table)
- speaker: Jiwan Kang (block M2)

## S7 — First, what a classical shadow is / delete the final Hadamard
- Random basis per shot ⇒ one record estimates every Pauli; variance 3^w [R029]
- Deleting the final H splits shadows into (WρW†±UρU†)/2 ⇒ ⟨O⟩_W and ⟨O⟩_U separately [R042]
- The ancilla says how much W is wrong; the garbage says which observable
- figures: deck/fig_shadow.png (shadow explainer slide)
- speaker: Ng Siu Hin (block M3)

## S8 — We are not the only way to do this — and not the cheapest
- Loschmidt echo and Hilbert–Schmidt test implemented and verified first [R043]
- figure: deck/fig_tb_baselines.png
- speaker: Ng Siu Hin (block M3)

## S9 — The honest scoreboard
- The echo is 4–6× cheaper at every n we measured [R043]
- Our arm is justified by what it returns: phase + per-observable profile [R042, R043]
- figure: none (table)
- speaker: Ng Siu Hin (block M3)

## S10 — AQC makes it scale — crossover at n=4, 36× by n=7 (MONEY PLOT)
- Exact block ~4^(n+1); AQC ~linear; crossover measured at n=4 [R046]
- Survives 2D (100.8× at n=8) [R049], Fermi–Hubbard (34.7×) [R051], routing widens it [R052]
- figure: deck/fig_aqc_scaling.png
- speaker: Su Wei-Chang (block M4)

## S11 — The trap: a phase-blind compiler breaks a phase interferometer
- State fidelity is a magnitude; a Hadamard test measures phase ⇒ χ wrong by 2.3–3.0 rad [R046]
- One ancilla P(−θ): |Δχ| 1.33 → 0.008 [R046]
- Same magnitude-hides-phase failure seen on ibm_miami data [R053]
- figure: none (derivation slide; the trap panel is inside deck/fig_aqc_scaling.png)
- speaker: Su Wei-Chang (block M4)

## S12 — We ran it on a QPU. It failed — and the failure is instructive
- Pre-registered 0.315/0.401; measured 0.026/0.033; every arm, both devices: noise [R054]
- The dead 8,850-gate arm scores "survival" 1.485 — unphysical (|χ|≤1): a T1 floor [R054]
- Why n=6 not n=7: control arm dominates cost; arithmetic in appendix A7 [R055]
- figure: deck/fig_aqc_hw.png
- speaker: Su Wei-Chang (block M4)

## S13 — First Track B on a QPU / the free error bar
- 2-gate echo beats our 136-gate arm 27× on hardware, widening to 32× over a 2×-extended time window [R044, R059]
- ⟨Q⟩_W−⟨Q⟩_U ≡ 0 by conservation ⇒ measured deviation is pure device error, no reference, bounded not growing with t [R044, R059]
- figures: deck/fig_tb_hardware.png · deck/fig_tb_symmetry.png (both now extended to t=5.4 on marrakesh)
- speaker: Tina Tien (block M5)

## S14 — What we claim, and what we do not
- Claim: compilation win [R046, R052], trap+fix [R046], Track B completed [R042], QPU tests [R044, R054]
- Do NOT claim: the gate-count win reaches hardware [R054]; anything vs classical computation
- figure: none (two-column list)
- speaker: Tina Tien (block M5)

## S15 — Future work: density of states
- ρ = 1/d turns the same circuit into a DOS estimator (W=I special case) [R045]
- figure: deck/fig_tb_dos.png
- speaker: Tina Tien (block M5)

## S16 — Reproduce it
- 58 sourced rows; scripts reproduce every hardware number; bug log incl. retractions
- figure: deck/qr_slides.png
- speaker: Tina Tien (block M5)

## S16b — Summary — what we contributed, and what we found (LAST main slide; leave up for Q&A)
- Built: 5 tracks, Track B completed [R042], baselines incl. our loss [R043], AQC crossover [R046, R052], 58-row ledger
- Found: the phase trap ×3 [R046, R053, R054], pre-registered hardware falsification [R054], free error bar [R044], SKQD boundary [R047, R050]
- figure: none (two-column list)
- speaker: Tina Tien (block M5) — one closing sentence, then leave on screen

## S17 — Team (arc-10)
- Folded into S16 (Reproduce it) rather than a separate frame — no dedicated Team
  slide is built in `trackb.tex`; the closing line under the QR code carries all
  five names mapped to their block: Chao Hsien (M1) · Jiwan Kang (M2) ·
  Ng Siu Hin (M3) · Su Wei-Chang (M4) · Tina Tien (M5)
- figure: none
- speaker: all five (one line each)

Backup (never presented, Q&A jumps only): appendix A1–A7 in trackb.pdf; the
master deck `slides.pdf` carries the Track A money plot
`figures/07_symmetry_resolved_spectrum.png` [R012, R013] if a judge asks for it.
