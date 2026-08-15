# papers/ — two manuscripts drafted from the project's evidence ledger

Both use the `quantumarticle` class (Quantum journal / clean arXiv preprint).
`quantumarticle.cls`, `ltxgrid.sty`, `ltxutil.sty` are vendored into each directory so
the build needs no extra TeX packages. Build either with:

    cd papers/<name> && pdflatex main.tex && pdflatex main.tex

House rule carried over from the decks: **every number in the manuscripts carries its
RESULTS.md row id as a LaTeX comment** next to the sentence that uses it. Do not edit a
number without the ledger.

## phase-trap/ — Paper 1 (the priority)

*A phase trap in approximate circuit compilation: how a converged compiler silently
breaks interferometric protocols, and a one-gate fix.*

The central finding (R046) with the anti-controlled instrument (R034/R042), the n=3–10
scaling trend (R046/R056), 2D/Hubbard/routing robustness (R049/R051/R052), the
interferometric-only scoping result (R060), the miami sighting (R053), and the
pre-registered two-QPU falsification with the shots sweep (R054/R055/R058).

Status: complete draft, builds clean (6 pp). Before submission (grep `TODO(team)`):
author order + affiliations + emails; acknowledgment/funding wording; verify every
bibliography entry against the actual records.

## skqd-boundary/ — Paper 2 (needs more experiments)

*Where sample-based Krylov diagonalisation works: a localisation boundary on exactly
solvable models.*

The Δ/J boundary with 20-seed bootstrap (R047/R057), premise-vs-success separation
(R047), geometry control (R048), Fermi–Hubbard U/t reproduction (R050), hardware
configuration recovery (R023/R036/R037). `make_paper_figs.py` regenerates the paper's
figure from the audited evidence JSONs.

Status: complete draft, builds clean (4 pp), **but not submittable yet** — the
manuscript's own Sec. "Work required before submission" lists the five experiment/
literature gaps referees will demand (multi-seed everywhere, larger sectors, reference
study, production-SQD comparison, a chemistry system). That section is the work-list;
it shrinks to nothing and gets deleted as items complete.

## Both papers, before any submission

- The SQD/SKQD/AQC bibliography entries were written from memory during drafting and
  are flagged with TODO comments — **verify every citation against the actual papers.**
- Author list is the five team members in alphabetical order as a placeholder.
- Nothing here claims advantage over classical computation; keep it that way.
