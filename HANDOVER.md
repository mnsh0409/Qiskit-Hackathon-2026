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

### The run we'd most like from you

```bash
python hardware_run.py --submit --backend ibm_nighthawk --model 2site --shadow
```

That is the **reduced 2-site instance with a full balanced basis ensemble** — 18 circuits,
36 000 shots, ~30 s of QPU. It is worth more than the default single-point run for two
reasons:

1. **It is only 15 two-qubit gates** (depth 64), against 101 for the 3-qubit exact path and
   435 for the Trotter circuit that failed on our hardware. On a device with 2e-3 two-qubit
   error that predicts ~97% signal survival, i.e. an actually *usable* result.
2. **It can report a valid system observable.** At n=2 the whole shadow ensemble is just
   3²=9 bases, so ⟨Q⟩ comes out unbiased. Every fixed-basis job — including all our χ-only
   jobs — can only legitimately report χ (see below). This is genuinely the one result we
   have on only ONE device so far (our own 2-site job returned at chi survival 0.962 and
   a valid ⟨Q⟩ at 0.957 — see §3), so it's not "give us something we already have" on a *third* device tier.

If you have QPU time for exactly one thing, run that.

### ⚠️ Fixed basis vs shadow ensemble (BUGLOG B04 — we got this wrong once)

The shadow estimator `3^w ∏s_j 1[b_j = P_j]` is unbiased **only** for i.i.d.-uniform bases;
that random draw is what the 3^w factor compensates for. With a single fixed basis the
indicator becomes deterministic and non-matching Pauli terms contribute structurally zero,
so the estimator silently returns a *different observable*. We reported a ⟨Q⟩ from
fixed-basis hardware data and attributed the discrepancy to noise; on a noiseless simulator
the same code is 65σ off, so it was never a noise effect at all.

`hardware_run.py` now refuses to print system observables unless `--shadow` was used. Please
don't work around that guard.

That's everything. `hardware_run.py` executes the circuit builder, memory parser and
estimators **straight out of the graded notebook**, so it cannot drift from our code — it
reimplements no physics. Defaults reproduce our reference point exactly (t=0.9, both
quadratures, basis [X,Y,Z], 2000 shots, `optimization_level=1`), so your number is directly
comparable to ours.

Sanity check before trusting it — these must print survival `0.179` and `0.878` respectively:

```bash
python hardware_run.py --fetch d9u95vs98n5s7392iao0     # Trotter+marrakesh (the bad one)
python hardware_run.py --fetch d9ujlb0u5hac73ahadu0     # exact+kingston (our best result)
```

## 2b. The Track B ask (newer, and the one we actually want most)

Everything above is the Part A ask. **If you can only run one thing, run this instead.**
Track B (the anti-controlled Hadamard test) has never run on a Nighthawk-class device, and
it is where our only genuinely open question sits.

### Scripts to hand over

Five files, plus the two they read from. All paths inside them are derived from the repo
root, so a clone anywhere works:

| file | role |
|---|---|
| `hardware_run.py` | **required** — provides `load_notebook_definitions()` and `get_model()` |
| `shadow_hadamard_challenge_PARTICIPANT.ipynb` | **required** — the definitions are `exec`'d out of it; no kernel needed |
| `evidence/scripts/track_b_hardware_prep.py` | go/no-go sizing. Run this FIRST |
| `evidence/scripts/track_b_hardware_submit.py` | validates the identity, then submits |
| `evidence/scripts/track_b_hardware_fetch.py` | analysis — produces every number we would quote |
| `evidence/scripts/track_b_baselines.py` | *optional*, classical only, no QPU |
| `CONVENTIONS.md` | *optional* — read §5 if any sign looks wrong |

### Run order

```bash
python evidence/scripts/track_b_hardware_prep.py   ibm_nighthawk   # 1. sizing, no QPU time
python evidence/scripts/track_b_hardware_submit.py --dry-run       # 2. validation only
python evidence/scripts/track_b_hardware_submit.py ibm_nighthawk   # 3. submit
python evidence/scripts/track_b_hardware_fetch.py                  # 4. when it finishes
```

**Budget: 116 circuits × 1000 shots = 116,000 shots**, about a minute of QPU time. The job
carries four arms so the comparison is same-device, same-hour: our Track-B overlap, our
per-observable profile, a Loschmidt echo, and a Hilbert–Schmidt test.

### Three things that will bite you, all of which bit us

- **`prep.py` and `submit.py` both refuse to proceed if the statevector identity fails.**
  That is deliberate — leave it in. It is what caught our own endianness bug (we took the
  `|1>`-control block as the *upper half* of the gate matrix; the notebook builds the ancilla
  as the *lowest* bit, so it is the odd sublattice `[1::2,1::2]`). The wrong version passes
  at `t=0`, where both branches are the identity, and fails at every `t>0`.
- **The 2-qubit basis gate is auto-detected from the backend target**, not hardcoded. If
  Nighthawk uses a gate we have never seen, the scripts will say so and stop rather than
  silently counting zero 2q gates and reporting survival 1.000. If it *does* stop, send us
  the printed operation list — do not patch around it.
- **Do not post-select on the charge `Q`.** It is a diagnostic only; filtering on it biases
  the shadow estimators (our BUGLOG B04 failure class).

### What we predict, so you can falsify it

On `ibm_marrakesh` (2q error ~1.4e-3) we measured, at t = 0.0/0.9/1.8/2.7:

- Loschmidt echo `P0` = 1.0000 / 0.9650 / 0.5420 / 0.1340 against exact 1.0000 / 0.9738 /
  0.5854 / 0.1069 — the 2-gate baseline is excellent.
- Our 136-gate Track-B arm: |chi_AB| survival 0.994 / 0.578 / 0.824 / 1.350. The last point
  is **above 1**, which is unphysical for pure damping — so the errors there are not simple
  depolarising loss.
- `<Q>_W - <Q>_U` must be **exactly zero** by conservation; we measured -0.04 / -0.39 /
  -0.25 / -0.34.

**The interesting question for you:** does a better device move our arm toward the echo, or
is the gap structural (136 gates vs 2) and therefore permanent? Either answer is publishable
for us. If our arm stays bad on good hardware, we will say so on the slide.

---

## 3. What we already know (please don't re-derive this)

**Updated 2026-08-13 — all four arms of the 2×2 have now returned, plus both side-model
jobs. The result is good news.**

The single most important finding: **circuit depth dominates device quality, by a lot** —
and once you fix the depth, real hardware works.

| circuit | two-qubit gates (kingston) | depth | measured survival |
|---|---|---|---|
| Trotter reps=1, marrakesh (worst device) | 435 | 1729 | **0.179** (35σ off — effectively no signal) |
| Trotter reps=1, kingston | 435 | 1729 | **0.368** |
| **exact path, marrakesh** | **101** | 375 | **0.822** (5.8σ, 5.0σ) |
| **exact path, kingston** | **101** | 375 | **0.878** (4.4σ, 0.9σ) — best result we have |
| 2-site side model, kingston (full shadow ensemble) | 15 | 64 | **0.962**, and a valid ⟨Q⟩ at **0.957** |

So: changing only the circuit (Trotter → exact, same device) took survival from 0.18 to
0.82 — roughly 4.6×. Changing only the device on top of that (marrakesh → kingston, exact
path both times) added another ~7% (0.822 → 0.878). Depth dominates; device choice is a
smaller, real, additional effect. (One caveat we're keeping honest: this is a single-run
comparison per arm, not a repeated-trial average — treat the *pattern*, depth >> device, as
solid; treat the exact percentages as one data point each.)

The depth effect is now confirmed on **both** devices: exact/Trotter is 4.59× on marrakesh
and 2.39× on kingston. Device choice at fixed circuit is smaller (1.07× exact, 2.06×
Trotter). Depth dominates throughout.

**So please use `--method exact` (the default) — it's not just theoretically better, it's
now confirmed to work on two real devices.** `--method trotter` is available if you want the
deep-circuit arm for comparison on Nighthawk, but expect it to be mostly noise based on what
we've seen.

Kingston (2q error 1.99e-3) has been our best-calibrated and best-performing device so far.
If Nighthawk's error rates are in the same range or better, we'd expect survival in the
0.85-0.95+ region on the exact path — genuinely comparable to a good simulator result.

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
- `BUGLOG.md` — B03 is the initial hardware finding, B04 is a real mistake we made and fixed
  (reported a hardware ⟨Q⟩ from a fixed-basis job — wrong, since the shadow estimator needs
  random bases; caught it, retracted it, added the `--shadow` guard in this tool)
- `CONVENTIONS.md` — the frozen conventions; §2 has the Hamiltonian, §5 the shot budget
- `figures/07_symmetry_resolved_spectrum.png` — the headline result the hardware run is
  ultimately trying to support
