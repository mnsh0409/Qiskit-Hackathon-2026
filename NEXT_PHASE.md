# NEXT_PHASE.md — project state and continuation brief

Written 2026-08-20, after the hackathon closed and the papers phase began. Purpose:
if this machine reboots or a fresh session starts cold, this file plus the repo is
everything needed to continue. Read this first, then `papers/README.md`, then
`RESULTS.md` for any specific number.

---

## 0. Reboot checklist — volatile state, handled or pending

| item | state |
|---|---|
| Working tree | clean; everything is committed |
| **Unpushed commits** | **⚠️ local `master` is ahead of `origin/master`. `git push` is the single action that makes this repo reboot-proof.** Remote: `github.com/mnsh0409/Qiskit-Hackathon-2026` (public) |
| Pre-rewrite git mirror | was in `/tmp` (lost on reboot) → **rescued to `~/Documents/QiskitHackathon/qh26_backup_pre_rewrite.git`**. Contains the pre-history-rewrite repo incl. deliberately purged files — keep local, never push, delete when no longer wanted |
| Delivery build helpers | were only in the session scratchpad (`/tmp`) → now in `tools/` (`build_pptx.py`, `md2pdf.py`) |
| Python env | `.venv` (Python 3.11, relaxed pins per BUGLOG B01) — rebuildable from README quickstart + `pip install qiskit-ibm-runtime qiskit-addon-aqc-tensor quimb jax markdown python-pptx` |
| IBM credentials | `apikey.json` (gitignored, never commit) + saved account in `~/.qiskit/` — survives reboot, not in repo |
| All hardware jobs | fetched and analysed; no job is pending anywhere |

## 1. Where the project stands

**Phase 1 — hackathon (closed, delivered).** All five challenge tracks done; presented
deck `deck/trackb.pdf` (35 pp incl. appendix A1–A8), master deck `deck/slides.pdf`,
delivery pack in `delivery/` (pptx + PDFs), five team members named throughout
(Chao Hsien, Jiwan Kang, Ng Siu Hin, Su Wei-Chang, Tina Tien; script blocks M1–M5).
Evidence ledger `RESULTS.md` at **62 rows (R001–R063; R015 never existed)** — every
number on every artifact traces to a row, every row to a command. `BUGLOG.md` at B01–B09.

**Phase 2 — papers (active).** Two manuscripts in `papers/`, quantumarticle class,
both building clean (`pdflatex main.tex` ×2; the class + ltxgrid/ltxutil are vendored
per-directory). All bibliography entries verified against primary sources 2026-08-16.

## 2. The papers, precisely

### papers/phase-trap/ — Paper 1 (the priority; near-submittable)
*A phase trap in approximate circuit compilation.* Content: AQC crossover n=3–10
(R046/R056); the phase trap + one-gate fix (R046); immunity of pure AQC → trap is
interferometric-only (R060); on-hardware demonstration on TWO devices with
pre-registered P1/P2/P3 (R061 marrakesh, R063 kingston) incl. the virtual-Z mechanism
paragraph and the "two devices identical by magnitude, 10× apart in phase" finding;
pre-registered n=6 falsification + shots sweep (R054/R055/R058); miami sighting (R053).

**Blocking items (human):**
1. **Author list.** Currently all five members alphabetically as a PLACEHOLDER. The
   user has stated they conceived the ideas and did the implementation. Constraint
   discussed 2026-08-16: **R053 uses a teammate's `ibm_miami` data (R031)** — that
   person gets authorship, a named data-credit acknowledgment, or the R053 exhibit is
   dropped (weakens the three-sightings framing). Decision pending; talk to the team
   before arXiv, and add an AI-assistance disclosure sentence to the acknowledgments
   regardless (much of the implementation/drafting was done in AI-assisted sessions).
2. Affiliations, emails, acknowledgments/funding wording (TODO(team) comments in the .tex).

### papers/skqd-boundary/ — Paper 2 (draft complete; NOT submittable yet)
*Where sample-based Krylov diagonalisation works.* Δ/J boundary w/ 20-seed bootstrap
(R047/R057); premise-vs-success separation (R047); geometry (R048); Hubbard U/t
(R050); on-hardware boundary test with the noise-attribution control (R062: ordering
survives, 24× inflation from charge-conserving corruption). Its own Sec. "Work
required before submission" is the work-list: (1) seeds everywhere, (2) larger
sectors, (3) reference-state study, (4) production-SQD comparison, (5) a chemistry
system, (6) hardware repeats + mitigation. Paper 2 contains no teammate data.

### papers/tagged-shadows-outline.md — research proposal (PARKED)
The honest home of "improving classical shadows": ancilla-tagged estimator theory,
ensemble optimization, tag-noise calibration. Kill criteria start at M0 (2-week
literature deep-read). Explicitly parked until papers 1–2 ship.

## 3. Hardware record (all jobs DONE and analysed)

| job | device | what | row |
|---|---|---|---|
| `d9uv5h50vrcc73boj8a0` / `d9uvhdob1g9c73a7vrl0` | marrakesh / kingston | n=6 AQC falsification | R054 |
| `d9v95ufo3ppc73ak01o0` / `d9v9640b1g9c73a8b660` | marrakesh | shots sweep 2000/8000 | R058 |
| `d9uss4f2sl0c73bl4em0` / `d9uss5n2sl0c73bl4eog` | marrakesh / kingston | Track B 4-arm | R044 |
| `d9v9djf2sl0c73bljm8g` | marrakesh | Track B extended time t≤5.4 | R059 |
| `da0a75ob1g9c73a9jsi0` / `da0arj7o3ppc73al9eog` | marrakesh / kingston | fix-A/B trap demo | R061 / R063 |
| `da0aabv2sl0c73bms1g0` | marrakesh | SKQD boundary sampling n=12 | R062 |
| `d9uk99k98n5s7392vhsg` | kingston | 2-site shadow ensemble (cleanest positive) | R023 |

Decisions already made: **miami/Nighthawk is NOT needed** (calibration no better than
kingston; P1/P2 are virtual-Z-guaranteed platform facts; the P3 question was answered
free on kingston). HANDOVER.md §2d = optional teammate follow-up only. Open-plan QPU
budget: 10 min/28 days — we have spent a substantial fraction this cycle; check before
new submissions.

## 4. How to rebuild anything

```bash
# decks (from deck/): pdflatex -interaction=nonstopmode trackb.tex   # run twice
# papers (from papers/<name>/): pdflatex main.tex                    # run twice
# delivery pptx:  python tools/build_pptx.py deck/trackb.pdf delivery/slides/Team_8.pptx
# delivery doc PDFs: python tools/md2pdf.py <file>.md <out>.pdf      # needs google-chrome
# paper-2 figure: python papers/skqd-boundary/make_paper_figs.py
# re-fetch any hardware job: the matching evidence/scripts/*_fetch.py (or --fetch flag)
```

House rules that survive the hackathon: every number traces to a RESULTS.md row (row
ids ride as comments in the .tex sources — do not edit numbers without the ledger);
banned language ("quantum advantage", uncosted "for free", causal claims from single
runs); pre-registered predictions before any hardware submission; statevector
pre-flight gates every submit script — leave them in.

## 5. Suggested next actions, in order

1. `git push` (after reviewing; makes everything reboot-proof).
2. Author-list decision for paper 1 (Sec. 2 above) + one message to the team.
3. Fill affiliations/emails/acknowledgments in both papers; add AI-assistance sentence.
4. Submit paper 1 to arXiv (quantumarticle doubles as the preprint format), then Quantum.
5. Start paper 2's work-list item (1) — seeds everywhere — it is pure compute, no QPU.
6. Revisit the tagged-shadows outline only after 4–5.
