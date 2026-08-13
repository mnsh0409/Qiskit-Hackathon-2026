# Hardware handover — running this on Nighthawk (or any backend we can't reach)

**What we need from you:** one shadow-Hadamard data point on better hardware than we
have access to. Our account is on the IBM open plan and can only reach `ibm_fez`,
`ibm_marrakesh` and `ibm_kingston` (all 156-qubit Heron-class). If you can reach a
Nighthawk device, you can close the one genuinely open question in this project.

Budget: **2 circuits × 2000 shots ≈ 3 seconds of QPU time.** That is the whole ask.

---

## 1. Setup (~5 minutes)

```bash
git clone <this repo> && cd 2026
python -m venv .venv && source .venv/bin/activate
pip install "qiskit==2.5.1" "qiskit-aer==0.17.2" "numpy<2.5" "scipy<1.18" \
            matplotlib pylatexenc qiskit-ibm-runtime
```

Two environment gotchas, both real:

- `requirements.txt` pins `numpy==2.5.2` / `scipy==1.18.0`, which **require Python 3.12**.
  On 3.11 those resolve to nothing and the install fails. We ran on Python 3.11 with the
  relaxed pins above and every checkpoint passed (logged as BUGLOG B01). Use 3.12 with the
  exact pins if you have it; otherwise the above is verified-good.
- `qiskit-ibm-runtime` is **not** in `requirements.txt` — the notebook itself never needs it.
  Install it separately, as above.

Save your own credentials once:

```bash
python -c "from qiskit_ibm_runtime import QiskitRuntimeService as S; \
           S.save_account(channel='ibm_cloud', token='YOUR_TOKEN', overwrite=True)"
```

## 2. Run it

```bash
python hardware_run.py --list                            # confirm the exact backend name
python hardware_run.py --submit --backend ibm_nighthawk  # ~3 s QPU, prints a JOB_ID
python hardware_run.py --fetch <JOB_ID>                  # after it completes
```

That's everything. `hardware_run.py` executes the circuit builder, memory parser and
estimators **straight out of the graded notebook**, so it cannot drift from our code — it
reimplements no physics. Defaults reproduce our reference point exactly (t=0.9, both
quadratures, basis [X,Y,Z], 2000 shots, `optimization_level=1`), so your number is directly
comparable to ours.

Sanity check before trusting it — this must print survival `0.179`:

```bash
python hardware_run.py --fetch d9u95vs98n5s7392iao0     # our marrakesh run
```

## 3. What we already know (please don't re-derive this)

The single most important finding: **circuit depth dominates device quality, by a lot.**

| circuit | two-qubit gates | depth |
|---|---|---|
| Trotter reps=1 | 435 | 1729 |
| **exact path** | **101** | **375** |

Measured 2-qubit error rates: kingston 1.99e-3, fez 2.73e-3, marrakesh 3.23e-3. Naive
survival `(1-p)^n_2q` then predicts changing *machine* buys ~1.7×, changing *circuit* buys
~4.3×. Our one completed run (Trotter on marrakesh, the worst device — we picked it on queue
length before checking fidelity, which was a mistake) came back at **0.179 signal survival**,
i.e. 35σ from the exact answer. Effectively no signal.

**So please use `--method exact` (the default).** `--method trotter` is available if you want
the deep-circuit arm for comparison, but expect it to be mostly noise.

We have three more jobs queued on our own hardware to measure the depth-vs-device split
directly (RESULTS.md R018, predictions recorded before submission). If those return in time
we'll have the 2×2; a Nighthawk point would extend it to a third device tier.

## 4. What to send back

Just the console output of `--fetch`. The line that matters is:

```
SIGNAL SURVIVAL |chi_hw|/|chi_exact| = 0.XXX
```

Plus the backend name and its median 2q error from `--list`, so we can place it on the
depth-vs-fidelity curve. If you want to be maximally helpful, run **both** `--method exact`
and `--method trotter` — that gives us the depth axis on your device too.

## 5. Rules we're holding ourselves to

Please keep these if you report anything publicly:

- **Robustness claims only.** No advantage claims. The system is 3 qubits and a laptop
  diagonalises it instantly — it is small *on purpose* so every estimate can be graded
  against an exact answer.
- **The exact path is not a method recommendation.** It is shallower only because n=3 is
  tiny (exact synthesis costs O(4ⁿ)); the advantage inverts as n grows. It is legitimate as
  a robustness demonstration, never as an algorithmic claim.
- **Every number traces to a command.** If you report a figure, say which invocation produced
  it — that's the rule the whole repo runs on (see RESULTS.md).

## 6. Background, if you want it

- `EXPLAINER.md` — plain-language description of what the project does
- `RESULTS.md` — every number, with the command that produced it (R008 and R018 are hardware)
- `BUGLOG.md` — B03 is the hardware failure analysis
- `CONVENTIONS.md` — the frozen conventions; §2 has the Hamiltonian, §5 the shot budget
- `figures/07_symmetry_resolved_spectrum.png` — the headline result the hardware run is
  ultimately trying to support
