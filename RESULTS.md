# RESULTS.md — one row per reported number (schema: see skills/0_t5-shadow-core_chat/references/schemas.md)

R### | quantity | value | 95% CI | shots x seeds | producing cell/file | timestamp

---

R001 | Gate 0 benchmark (`python scripts/gate0_benchmark.py`) | GATE0 PASS (all asserts G0.1-G0.9 true) | n/a | n/a (exact diagonalisation, no shots) | scripts/gate0_benchmark.py, run via .venv (2026-08-12) | 2026-08-12
R002 | Checkpoint 2 (model matches spec) | all 8 asserts PASS: [H,Q]=0.00e+00; 4 populated levels, sectors {+1,+3}; \|000> eigenstate at E=0.55; Q=3 weight 0.633749; no aliasing (radius 2.64<15.71); resolvable (spacing 1.03>0.50) | n/a (deterministic/exact) | n/a | notebook cell 16, executed headlessly via nbconvert prefix run (.venv, kernel qh26-t5) | 2026-08-12
R003 | Checkpoint 3a (`build_controlled_evolution`, Challenge 1) | exact path max\|c-U - block\|=6.87e-16 (PASS, <1e-10); Trotter error reps=1/2/8: 8.22e-01/1.68e-01/9.67e-03, monotonically decreasing (PASS), reps=8 accurate (PASS, <2e-2) | n/a (deterministic operator identity) | n/a | notebook cell 24, executed headlessly via nbconvert prefix run | 2026-08-12
R004 | Checkpoint 3b (sign convention, all 4 conventions at once) | max deviation over 3 times x 2 quadratures x 5 observables = 1.33e-15 (PASS, <1e-10); D1 marginal \|\|diff\|\|=3.50e-16 (PASS); ancilla-marginal-undisturbed-by-shadow-rotation (PASS) | n/a (deterministic) | n/a | notebook cell 26, executed headlessly via nbconvert prefix run | 2026-08-12
