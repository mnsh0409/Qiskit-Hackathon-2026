# In the Shadow of the Hadamard Test — From Garbage to Spectra

A Qiskit hackathon challenge on the **shadow-enhanced Hadamard test**: a single family of
circuits that returns the usual interference signal *and* a symmetry-resolved spectrum,
by keeping the "garbage" system register instead of discarding it.

This repository is the **participant edition** — a guided build with 11 function bodies
left for you to implement, graded by hard `assert` checkpoints as you go.

---

## What this is

The textbook Hadamard test uses one ancilla to control a unitary $U$ on an $n$-qubit
system register, and reads $\chi(t) = \mathrm{Tr}[U(t)\rho]$ off the ancilla. The
system register comes out entangled and scrambled, and is thrown away.

Faehrmann, Eisert and Kueng observed that throwing it away is a waste. Measure the system
register in **random Pauli bases**, keep every shot's record, and the same circuits also
give you:

- the input state's **energy** $\langle H \rangle$ and any **conserved charge** $\langle Q \rangle$;
- the **joint observables** $\chi_O(t) = \mathrm{Tr}[O\,U(t)\rho]$, obtained by
  correlating the ancilla outcome with the system-register classical shadow — the part
  with no classical analogue.

The headline consequence, and what this notebook demonstrates: the ancilla alone tells you
**which energies** a state populates; the ancilla-correlated garbage register tells you
**which symmetry sector each energy lives in**. Two-dimensional spectroscopy out of a
one-dimensional experiment.

> **Reference.** P. K. Faehrmann, J. Eisert, R. Kueng, *In the Shadow of the Hadamard Test:
> Using the Garbage State for Good and Further Modifications*, **Phys. Rev. Lett. 135,
> 150603 (2025)**; extended version [arXiv:2505.15913](https://arxiv.org/abs/2505.15913).
> Equation references throughout the notebook — (D1), (D11), (C1) — point at that paper's
> appendices.

### The benchmark

A 3-qubit open chain plus one ancilla (4 qubits total):

$$H = 0.65\sum_i (X_iX_{i+1} + Y_iY_{i+1}) + 0.25\sum_i Z_iZ_{i+1} + 0.40 Z_0 - 0.50 Z_1 + 0.15 Z_2$$

with conserved charge $Q = Z_0 + Z_1 + Z_2$ (total magnetisation, $[H,Q]=0$) and input
state $|\psi\rangle = R_y(1.3)_0|000\rangle$.

---

## Contents

| | Goal | Output |
|---|---|---|
| **Part A** | Fundamental (mandatory) | $\hat\chi(t)$, $\langle H\rangle$, $\langle Q\rangle$, a non-conserved observable and a complex joint observable $\chi_O(t)$ — all from **one** set of circuits, all agreeing with exact references inside their error bars, error falling as $N^{-1/2}$ |
| **Part B** | Advanced — Track A | Symmetry-resolved spectral analyzer reporting $(E_k, p_k, \hat q_k)$ with bootstrap uncertainties, via matrix-pencil reconstruction |
| **Part C** | Bonus | Krylov energy solver from the same records, and a noise-robustness study |

Three rules hold throughout, and the notebook enforces the first mechanically:

1. **Estimators consume measurement data only.** Exact diagonalisation is for *evaluation*,
   never for estimation (Checkpoint 7, item 7.7 is the tripwire).
2. **Every number carries an uncertainty.** A point estimate with no error bar is not a result.
3. **Resources are reported** — circuits, shots, transpiled 1q/2q gate counts, depth, and
   classical post-processing time.

The notebook is a guided build: numbered 🎯 **Challenges** say what to implement, and most
are followed by a ✅ **Checkpoint** that grades them with hard `assert`s.

---

## Quickstart

### Option A — conda (recommended)

```bash
conda env create -f environment.yml
conda activate ibmhack2026
python -m ipykernel install --user --name ibmhack2026 \
       --display-name "Python (ibmhack2026) - Qiskit"
```

### Option B — venv + pip

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name ibmhack2026 \
       --display-name "Python (ibmhack2026) - Qiskit"
```

**The `ipykernel install` step is not optional.** Creating an environment does not make it
visible to Jupyter or VS Code — the kernel has to be registered. Skipping it is the single
most common reason a notebook "can't find the kernel". See [Troubleshooting](#troubleshooting).

### Run it

Interactively — open the notebook and select the **Python (ibmhack2026) — Qiskit** kernel:

```bash
jupyter lab shadow_hadamard_challenge_PARTICIPANT.ipynb
```

Headless, top to bottom (useful once your implementations are in):

```bash
jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.timeout=1800 \
    --ExecutePreprocessor.kernel_name=ibmhack2026 \
    --output executed.ipynb \
    shadow_hadamard_challenge_PARTICIPANT.ipynb
```

Everything runs on the local Aer simulator. No IBM Quantum account or API token is needed.

### What you implement

The notebook is a guided build. Run it from the top: it executes cleanly until it reaches
the first unimplemented function, then stops with a `NotImplementedError` naming the
challenge. Read that challenge's 🎯 box, fill in the body, re-run, and run the ✅ Checkpoint
below it. The stubs are ordered by dependency, so working straight down always works.

Your worklist is **11 function bodies** across Challenges 1, 3, 4, 7, 8, 9 and 10 — the
notice at the top of the notebook lists them, along with the helpers that are given complete
and should be read rather than rewritten.

---

## Runtime and budget

The budget is set in one place, near the top of the notebook:

```python
BUDGET = "full"    # "full" = official benchmark. "fast" = half the shots, for debugging.
```

| `BUDGET` | Times | `dt` | Shots/(t,φ) | Total shots |
|---|---:|---:|---:|---:|
| `"full"` | 64 | 0.2 | 2000 | 256,000 |
| `"fast"` | 32 | 0.4 | 2000 | 128,000 |

A full-budget pass takes about 3 minutes on a multi-core desktop (2 min 40 s measured on 8
cores, of which the main sweep is ~50 s); Aer parallelises across cores, so wall time varies
with machine. Use `"fast"` while
developing — but note that tolerances calibrated at the official budget become **advisory**
under a reduced budget, so re-run at `"full"` before believing any number you intend to
report.

---

## Reproducibility

- Every random draw derives from a single master seed, `SEED = 2026`.
- `STRICT_CHECKS = True` makes checkpoints raise on failure rather than warn.
- Pinned, verified-working versions are in `requirements.txt` / `environment.yml`
  (Python 3.12, Qiskit 2.5.1, Aer 0.17.2). The notebook itself only asserts Qiskit ≥ 2.1.
- Figures are written to `figures/` as they are drawn; headline numbers land in
  `run_summary.json`. Both are generated locally when you run the notebook, and are not
  tracked here — they are part of *your* submission, not of this repository.

---

## Repository layout

```
.
├── shadow_hadamard_challenge_PARTICIPANT.ipynb   # the guided build — start here
├── environment.yml                               # conda environment
├── requirements.txt                              # pinned pip environment
├── LICENSE
└── README.md
```

Generated when you run the notebook, and deliberately untracked: `figures/` and
`run_summary.json`. `.vscode/` is untracked too — it holds absolute, machine-specific
interpreter paths, and the setup it encodes is documented above.

---

## Troubleshooting

**"Running cells with 'Python 3.x' requires the ipykernel package"**
Your client is pointed at a system Python instead of the project environment. Register the
kernel (see [Quickstart](#quickstart)), then explicitly select
*Python (ibmhack2026) — Qiskit* in the kernel picker. Confirm it is registered with:

```bash
jupyter kernelspec list
```

**VS Code does not list your conda environments at all**
The Python extension only auto-probes conda in standard locations (`~/miniconda3`,
`~/anaconda3`, `~/miniforge3`, `/opt/conda`). If conda lives anywhere else, tell it
explicitly in `.vscode/settings.json`:

```json
{
  "python.condaPath": "/path/to/conda/condabin/conda",
  "python.defaultInterpreterPath": "/path/to/envs/ibmhack2026/bin/python"
}
```

Also check that no machine- or user-level `python.defaultInterpreterPath` is pinning you to
a system interpreter — a stale pin there overrides discovery and is easy to miss.

**Kernel fails to attach after an environment rebuild**
The `ipykernel` 7.x series changed the connection layer (protocol 5.5 in 7.2, CurveZMQ in
7.3). If your Jupyter client
predates it, pin `ipykernel>=6.29,<7` as the environment files here do.

**Sign or ordering results look wrong**
Two different endian conventions are in play: Pauli labels put qubit 0 rightmost, memory
bitstrings put the highest classical bit leftmost. The notebook pins both conventions with
explicit tests — a statevector check for the Pauli/sign conventions (§2 rule #1) and a
hand-worked bitstring example in Checkpoint 4 for the memory layout (§3.2 rule #2) — run those before
debugging anything downstream.

---

## Citation

If you use this code, please cite the paper it implements:

```bibtex
@article{faehrmann2025shadow,
  title   = {In the Shadow of the Hadamard Test:
             Using the Garbage State for Good and Further Modifications},
  author  = {Faehrmann, Paul K. and Eisert, Jens and Kueng, Richard},
  journal = {Physical Review Letters},
  volume  = {135},
  pages   = {150603},
  year    = {2025},
  doi     = {10.1103/cqjw-kl8s},
  eprint  = {2505.15913},
  archivePrefix = {arXiv},
}
```

---

## License

See [LICENSE](LICENSE).
