# BUGLOG.md (schema: see skills/0_t5-shadow-core_chat/references/schemas.md)

B## | symptom | root cause | fix | prevention rule

---

B01 | `pip install -r requirements.txt` fails: `numpy==2.5.2` and `scipy==1.18.0` require Python >=3.12, which is not installed on this machine (available: system 3.10, anaconda 3.11). | Environment pin mismatch, not a code/convention bug — this machine never had Python 3.12. | Created `.venv` with anaconda's Python 3.11.5; installed `qiskit==2.5.1` and `qiskit-aer==0.17.2` exactly as pinned (both available for 3.11), but relaxed `numpy` to `2.4.6` (< pinned 2.5.2) and `scipy` to `1.17.1` (< pinned 1.18.0) — nearest available versions compatible with qiskit 2.5.1 on Python 3.11. `matplotlib==3.11.1` and `pylatexenc==2.11` installed exactly as pinned. | Not a CONVENTIONS.md law violation (§6 pins are tooling, not science) but flagged per the zero-improvisation rule since it deviates from the frozen environment doc. If Python 3.12 becomes available, recreate `.venv` with the exact pins and re-run Gate 0 + all checkpoints to confirm no numerical drift from the numpy/scipy delta (none expected — both are patch/minor bumps within the same major series).
