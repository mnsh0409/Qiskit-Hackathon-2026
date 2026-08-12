# CONVENTIONS.md — Topic 5: classical-shadow-enhanced Hadamard test (LAW)

**Status: T0 complete.** Every template slot is filled below. Values that only an execution can
produce are marked `TBD-user(<producing step>)` and become real only when the producing output is
pasted in verbatim. Nothing in this file changes without a BUGLOG entry and a re-run of the
affected checkpoints.

**Authorities, in order of precedence**

1. Frozen base notebook `shadow_hadamard_challenge_PARTICIPANT.ipynb`
   (repo `MatthewPeng57/NTU-IBM-hackthon2026-topic-classical-shadow-enhanced-hardboard-test-`,
   branch `main`). Its conventions are law; we document them, we never fight them.
2. P. Faehrmann, J. Eisert, R. Kueng, *In the Shadow of the Hadamard Test*,
   PRL **135**, 150603 (2025), DOI `10.1103/cqjw-kl8s`. Equation labels `(D1) (D10) (D11) (C1)`
   follow the arXiv version `arXiv:2505.15913`, exactly as the notebook does; published-Letter
   labels are given alongside where they differ.
3. Huang, Kueng, Preskill, Nat. Phys. **16**, 1050 (2020),
   DOI `10.1038/s41567-020-0932-7` ("HKP").
4. Challenge spec deck, Topic-5 slide (Advanced tier: reconstruction "under a fixed shot
   budget"); budget constants per spec document §4.3 as quoted by notebook §0.2.

**Provenance tags**: `[nb §x]` frozen-notebook markdown/code · `[derived]` algebra shown here ·
`[PRL Eq. n]` published Letter · `[arXiv (Dn)]` arXiv appendix · `[HKP]` · `[spec]` ·
`TBD-user(...)` awaiting pasted output.

**House rules recap (binding).** Zero fabrication: a number exists only via pasted execution
output, a RESULTS.md row, frozen-notebook markdown, or a derivation displayed here. Estimators
consume measurement data only — exact diagonalisation is evaluation, never estimation
[nb Checkpoint 7.7]. Any statistical claim sits on >= 10 seeds with bootstrap CIs. Banned
phrases: "quantum advantage", uncosted "for free".

---

## 0. Name map (skill/template <-> notebook)

| skill / template name | notebook name | definition |
|---|---|---|
| `g1(t)` | `chi(t)` | `Tr[U(t) rho] = <psi|U(t)|psi>`, `U(t) = exp(-iHt)` |
| `gM(t)` | `chi_Q(t)` | `Tr[Q U(t) rho]` |
| `M` | `Q` | `Z0 + Z1 + Z2` |
| ancilla bit `b in {0,1}`, `(-1)^b` | `a in {+1,-1}` | ancilla Z outcome, `a = (-1)^b` |
| shadow rotation `U_i` | basis code `b_j in {0,1,2}` -> gate | `X:0 -> h` ; `Y:1 -> sdg,h` ; `Z:2 -> (none)` |
| `E[rho_hat] = (rho + U rho U^dag)/2` | `rho^(I)` | `[arXiv (D1)] = [PRL Eq. 5]`; phi-independent |
| `E[(-1)^b rho_hat] = (U rho + rho U^dag)/2` | `rho^(Z)` at `phi = 0` | general phi: `(e^{i phi} U rho + e^{-i phi} rho U^dag)/2` `[arXiv (D10)] = [PRL Eq. 4]` |
| CSVs `g1_*.csv`, `gM_*.csv` | `chi`, `chi_Q` series | schemas.md naming kept verbatim (§7) |

Name-collision warning: the skill's `b` is the **ancilla bit**; the notebook's `b_j` are **shadow
basis codes**. This file always writes `a` for the ancilla outcome and `b_j` for basis codes.

---

## 1. Qubit & register map

- `n_system = 3` (`N_SYS`), ancilla index `= 3` (`= N_SYS`), total wires = 4. Registers are
  created as `QuantumCircuit(sys_reg, anc_reg)`: system qubits 0..2 first, ancilla last — so the
  ancilla is wire 3 and is drawn as the **bottom** wire. [nb §2, §3]
- **Endianness rule 1 (Pauli labels).** In any Qiskit label the **rightmost** character is
  qubit 0. All operators are built with `SparsePauliOp.from_sparse_list` (explicit index lists),
  never from label strings. [nb §2]
- **Endianness rule 2 (counts / memory keys).** Single classical register `c[0..3]`; measurement
  map `sys qubit j -> c[j]`, `ancilla -> c[3]`. In a counts/memory key the **leftmost** character
  is the highest classical bit: key char 0 = `c[3]` = ancilla; key char `(3-j)` = `c[j]` = system
  qubit `j`. Bit `'0' -> +1`, `'1' -> -1`. Parsing the system slice therefore **reverses** it.
  [nb §3.2, §4]
- Generic positional read (template's example, this layout): key `"0110"` -> `q3=0, q2=1, q1=1,
  q0=0`, i.e. ancilla `a = +1`, system `(s0, s1, s2) = (+1, -1, -1)`.
- **Worked example (frozen; notebook Checkpoint 4).** `parse_memory(["0100", "1011"], n=3)`:
  - `"0100"`: chars `[c3,c2,c1,c0] = 0,1,0,0` -> `a = +1`; `s0 = +1` (c0='0'), `s1 = +1`
    (c1='0'), `s2 = -1` (c2='1') -> system row `[+1, +1, -1]`.
  - `"1011"`: `a = -1`; system row `[-1, -1, +1]`.
  - Failure signature of the classic bug (un-reversed system slice): rows come out
    `[-1, +1, +1]` / `[+1, -1, -1]`. Checkpoint 4 asserts against exactly this. [nb Checkpoint 4]
- **Controlled-U qarg law.** `build_controlled_evolution` returns a `Gate` whose **first** qubit
  is the ancilla control; it is appended with qargs `[anc, s0, s1, s2]`. Inside the gate's own
  matrix (little-endian over its qargs) the control is the **lowest** bit:
  `gate_matrix = kron(I_8, |0><0|) + kron(U, |1><1|)`. Embedded in the 4-wire circuit (ancilla =
  qubit 3 = highest bit) the circuit-level operator is `kron(|0><0|, I_8) + kron(|1><1|, U)`.
  Both statements are law; Checkpoint 3a exists to kill the swapped-kron bug. [nb §3.1, Cp 3a]
- **Frozen circuit order** (both quadratures): `prep(sys)` ; `h(anc)` ; `c-U(t)` ;
  `p(phi, anc)` **only if** `phi != 0` ; `h(anc)` ; shadow rotations on the system
  (`X: h` ; `Y: sdg` then `h` ; `Z:` none) ; measure `sys j -> c[j]` for all j, `anc -> c[3]`,
  into the single creg `c`. [nb §3, §4]

---

## 2. Operators

- **Hamiltonian (frozen; 3-qubit open XXZ + site fields; `from_sparse_list` construction):**

  ```
  H = sum_{i=0}^{1} [ 0.65 (X_i X_{i+1} + Y_i Y_{i+1}) + 0.25 Z_i Z_{i+1} ]
      + 0.40 Z_0 - 0.50 Z_1 + 0.15 Z_2                       [nb §2 benchmark_hamiltonian()]
  ```

  In `exact_ref.py` parameter names: `J = 0.65`, `delta = 0.25` (`delta` is the raw ZZ
  coefficient, **not** `J*delta`), and the shipped scalar field `h = 0.31` **must be replaced**
  by the site-dependent `(h_0, h_1, h_2) = (0.40, -0.50, 0.15)` — see §8.2. The nonuniform field
  is what breaks the global spin-flip (`+m/-m`) degeneracy trap.
- **Conserved charge:** `Q = Z_0 + Z_1 + Z_2` [nb §2 `conserved_charge()`]. Why `[H, Q] = 0`:
  the `XX+YY` hop conserves the up-spin count; `ZZ` and `Z_i` are diagonal. `[derived]`
  Numeric verification: notebook Checkpoint 2 asserts `||[H,Q]|| < 1e-12` (SparsePauliOp route);
  Gate 0 prints the dense-matrix norm (`G0.1`, `< 1e-10`). Paste slot: §5.6, `TBD-user(G0)`.
- **Input state:** `state_prep_circuit()` = `Ry(1.3)` on qubit 0, so
  `|psi> = cos(0.65)|000> + sin(0.65)|001>` (rule 1: `|001>` is qubit 0 flipped). [nb §2]
- **Quadrature constants:** `PHI_RE = 0.0`, `PHI_IM = -pi/2`;
  `PAULI_CODES = {"X":0, "Y":1, "Z":2}`, `CODE_TO_PAULI = "XYZ"`. [nb §2]
- **Non-conserved probe:** `Z0_OBS` = `Z` on qubit 0, `[Z0, H] != 0`. Its unweighted-shadow
  reference is `Tr[Z0 rho^(I)(t)] = (Tr[Z0 rho] + Tr[Z0 U rho U^dag]) / 2` — **not**
  `<psi|Z0|psi>`. [nb §2, §6]
- **Closed forms (law; Gate 0 asserts them, `G0.7`)** `[derived]`:
  - `<psi|H|psi> = 0.55 cos^2(0.65) - 0.75 sin^2(0.65)` (~ +0.0739). Two-line evaluation:
    `<000|H|000> = 0.25 + 0.25 + 0.40 - 0.50 + 0.15 = 0.55`;
    `<001|H|001> = -0.25 + 0.25 - 0.40 - 0.50 + 0.15 = -0.75`; the cross term vanishes because
    H conserves Q and the two basis states live in different sectors (q=3 vs q=1).
  - `<psi|Q|psi> = 3 cos^2(0.65) + 1 sin^2(0.65) = 1 + 2 cos^2(0.65)` (~ +2.2675).
  - `chi(0) = 1` ; `chi_Q(0) = <psi|Q|psi>`.
- **Spectrum commitments** [nb §0.2, §1.4, §2, §7.1]: exactly **4 populated lines**; populated
  sectors `{+1, +3}`; `|000>` is an exact eigenstate at `E = 0.55` with weight `cos^2(0.65)`
  (~0.63); the `q = +1` triplet sits near `E ~ -1.9, -0.48, +1.95`, weakest weight `p ~ 0.05`;
  smallest **populated** spacing `1.03`; **full** spectral radius `2.64`; an **unpopulated**
  near-degenerate cross-sector pair near `E ~ 0.45` sets the full-spectrum minimum gap.
  Exact table `(E_k, w_k, m_k)`: `TBD-user(G0 paste §5.6 / Checkpoint 2 print)`.
- **Degeneracy law + fallback ladder** (walk top to bottom after Gate 0):
  - `D1` — `||[H,Q]|| >= 1e-10`: conventions broken (operator build or endianness). Stop; fix
    §1/§2; nothing downstream is valid.
  - `D2` — full-spectrum min gap `> 1e-3` **and** populated lines separated at the `~1` scale:
    proceed. All resolution margins are judged against the **populated** spacing, never the
    full-spectrum gap.
  - `D3` — full gap `< 1e-3` but every close pair is unpopulated (each member `w < 1e-6`):
    proceed; the analyzer is unaffected; log a note; feed the **populated** gap to
    `suggest_grid` (§8.2).
  - `D4` — a **populated** line is (quasi-)degenerate with a different-`q` partner within the
    achievable resolution: the ratio estimator returns the population-weighted mean over the
    merged peak, `q_bar = sum_k p_k q_k / sum_k p_k` `[derived from the chi/chi_Q forms, §3]`.
    Handling: report the merged peak with `q_bar` + CI and flag it non-integer, **or** obtain
    mentor sign-off for a small symmetry-breaking field term (H is supplied — no unilateral
    edits). Decide before Gate 1.
  - `D5` — all `h_i = 0` (the spin-flip trap; **not** our case): `+m/-m` sectors exactly
    degenerate and symmetry resolution is impossible as posed; escalate. [skill; nb §1.4]
- **U(t) construction law:** `U(t) = exp(-iHt)`.
  - `method="exact"`: 8x8 matrix exponential wrapped as a `UnitaryGate`, then `.control(1)` —
    used for all clean/validation runs.
  - `method="trotter"`: 2nd-order Suzuki (`PauliEvolutionGate` + `SuzukiTrotter(order=2, reps)`),
    **synthesize the uncontrolled step first, then `.control(1)`**. Trotterising a controlled
    generator is the forbidden trap. [nb §3.1]
  - Pooling precondition: `Q` commutes with every Trotter step, so `<Q>` pooling is valid on both
    paths; `H` does not, so `<H>` pooling is **exact-path only** (measured pooled-`<H>` bias at
    `reps = 1`: ~ `-0.02`, ~2.6 sigma [nb]).

---

## 3. Sign table (derived, not asserted)

**Circuit chain** (pure input shown; mixed `rho` by linearity). `P(phi) = diag(1, e^{i phi})`,
so `P(-pi/2) = Sdg`: the "S-dagger variant" for the imaginary part is literally the
`phi = -pi/2` phase gate placed between `c-U` and the final `h(anc)`.

```
|0>_a |psi>  --h(a)-->    (|0> + |1>) |psi> / sqrt2
             --c-U-->     (|0>|psi> + |1> U|psi>) / sqrt2
             --p(phi,a)-> (|0>|psi> + e^{i phi} |1> U|psi>) / sqrt2      [gate omitted at phi = 0]
             --h(a)-->    (1/2) [ |0> (I + e^{i phi} U)|psi> + |1> (I - e^{i phi} U)|psi> ]

rho_out = (1/4) sum_{b,b'} |b><b'| (x) (I + (-1)^b e^{i phi} U) rho (I + (-1)^{b'} e^{i phi} U)^dag
                                                                              [PRL Eq. 3]
```

**E1 — scalar signal (ancilla only)** `[derived; = PRL Eqs. 1-2, 6]`:

```
E[a] = <Z_a> = (1/4) tr[(I + e^{i phi}U) rho (.)^dag]  -  (1/4) tr[(I - e^{i phi}U) rho (.)^dag]
             = (1/4) tr[ 2 e^{i phi} U rho + 2 e^{-i phi} rho U^dag ]   (I- and UrhoU^dag-terms cancel)
             = Re[ e^{i phi} tr(U rho) ]
```

`phi = 0 -> +Re chi(t)` ; `phi = -pi/2 -> Re[-i chi] = +Im chi(t)`.

**E2 — unweighted shadow target** `[derived; arXiv (D1) = PRL Eq. 5]`:

```
rho^(I) = tr_a[rho_out] = (1/4)[ (I + e^{i phi}U) rho (.)^dag + (I - e^{i phi}U) rho (.)^dag ]
        = (1/2) (rho + U rho U^dag)              (cross terms cancel between the two branches)
```

`phi`-independent -> quadratures pool. If `[O, U_impl(t)] = 0` then
`tr[O rho^(I)(t)] = tr[O rho]` at every `t` -> pool all `2 N_t` settings.

**E3 — a-weighted shadow target** `[derived; arXiv (D10) = PRL Eq. 4; joint identity
arXiv (D11), (C1) = PRL Eq. 7]`:

```
rho^(Z) = tr_a[(Z (x) I) rho_out] = (1/2) ( e^{i phi} U rho + e^{-i phi} rho U^dag )
tr[O rho^(Z)] = Re[ e^{i phi} tr(O U rho) ]
```

`phi = 0`: `rho^(Z) = (U rho + rho U^dag)/2 -> +Re chi_O` ; `phi = -pi/2 -> +Im chi_O` ;
`chi_O(t) := tr[O U(t) rho] = <psi| O U(t) |psi>` — operator order **O·U**, matching the
notebook's `exact_chi_O`. For `O in {H, Q}` order is immaterial (`[O, U] = 0`); for `Z0` it is
not — keep `tr(O U rho)`.

**Sign table:**

| ancilla line | phi | per-shot estimator | expectation equals |
|---|---|---|---|
| `h - cU - h` | `0` | `a` | `+Re chi(t)` |
| `h - cU - p(-pi/2) - h` | `-pi/2` | `a` | `+Im chi(t)` |
| `h - cU - h` + shadows | `0` | `a * Phat_O` | `+Re chi_O(t)` |
| `h - cU - p(-pi/2) - h` + shadows | `-pi/2` | `a * Phat_O` | `+Im chi_O(t)` |
| either, ancilla ignored | any | `Phat_O` | `tr[O rho^(I)(t)]` |

**Record slots read by each deliverable** (one record = `ShadowRecords(t, phi, bases, outcomes,
ancilla, n_circuits)`):

| deliverable | slots read | pooling law |
|---|---|---|
| `chi(t)` | `ancilla` of `(rec_re, rec_im)` at that `t` | per-`t`; quadratures are separate estimates combined as `Re + i Im` |
| `<Q>` | `bases, outcomes` of **all** records | pool `2 x N_t` settings — exact **and** trotter paths |
| `<H>` | `bases, outcomes` of **all** records | pool `2 x N_t` settings — **exact path only** |
| `<Z0>` on `rho^(I)(t)` | `bases, outcomes` of the two records at `t` | pool quadratures at fixed `t` only |
| `chi_Q(t)`, `chi_Z0(t)` | `ancilla x snapshot`, per `(t, phi)` | per-`t`, per-quadrature; **never** pooled over `t` |

**Known paper sign typo — never debug against it.** Boxed law:
`<Z_a>_phi = Re[ e^{+i phi} tr(U rho) ]` with `P(phi)|1> = e^{i phi}|1>`, `U(t) = exp(-iHt)`.
The published main text agrees (below Eq. (2): `phi = -pi/2` estimates the imaginary part). The
published **Fig. 1 caption** instead says `pi/2`, and the **arXiv Appendix A, Eqs. (A7)-(A9)**
carry `e^{-i phi}` — a documented internal inconsistency of Ref. 2 [nb §1.1]. The convention
above is pinned deterministically by notebook **Checkpoint 3b** (statevector test on the exact
frozen layout); that checkpoint, not the paper's appendix, is the arbiter.

---

## 4. Shadow protocol

- **Ensemble.** Per shot, per **system** qubit `j`, draw basis code `b_j` uniform on
  `{0,1,2} = {X,Y,Z}`. Pre-measurement rotation: `X: h` ; `Y: sdg` then `h` ; `Z:` none
  (matrices `V_X = H`, `V_Y = H*Sdg`; both satisfy `V W V^dag = Z` `[derived]`). The **ancilla
  is never rotated and never shadowed** — it is read directly in Z. [nb §4]
- **Channel + inversion** `[derived; HKP Eq. 2 specialised to random-Pauli / single-qubit
  Clifford measurements — Nat. Phys. 16, 1050 (2020)]`:

  ```
  M1(sigma) = E_{W,b}[ <b|V sigma V^dag|b> * V^dag|b><b|V ] = sigma/3 + tr(sigma) I/3
     (decompose sigma over {I,X,Y,Z}: the I part always survives; each traceless part survives
      only when its own basis is drawn, probability 1/3)
  =>  M1^{-1}(A) = 3A - tr(A) I
  =>  rho_hat = kron_j ( 3 V_j^dag |b_j><b_j| V_j - I ),   E[rho_hat] = rho_measured     [HKP]
  ```

- **Pauli-string estimator** `[derived]`: for a string `P` with support `s`, per snapshot

  ```
  tr[P_j rho_hat_j] = 1 (P_j = I) ;  3 s_j (P_j = W_j, since V_j P_j V_j^dag = Z) ;
                      0 (P_j != W_j, both non-identity)
  =>  Phat = 3^{w(P)} * prod_{j in s} s_j * 1[b_j = P_j] ;    identity string -> Phat = 1
  ```

  Single-shot second moment `E[Phat^2] = 3^{2w} * 3^{-w} = 3^{w(P)}` **exactly** -> the weight-1
  `<Q>` converges ~1.6x faster than the weight-2-dominated `<H>` [nb]. General observables
  extend by linearity through `pauli_terms(obs)`.
- **Joint ancilla-system strings** (`Z_anc (x) P`): because `a` is read exactly, the estimator
  is `a * Phat` — **not** a shadowed `3 a * 1[b_anc = Z]`:

  ```
  E[a * Phat] = tr[(Z (x) P) rho_out] = tr[P rho^(Z)] = Re[ e^{i phi} tr(P U rho) ]
                                                        [arXiv (C1), (D11) = PRL Eq. 7]
  ```

  The variance factor stays `3^{w(P)}` (`a^2 = 1`). Shadowing the ancilla instead would remain
  unbiased but with 3x the second moment and 2/3 of shots discarded; the frozen design forbids
  it. `[derived; nb §4-§5]`
- **Grouping / execution.** Draw all `N` basis rows up front; group identical rows — at most
  `3^3 = 27` distinct circuits per `(t, phi)`; execute with `memory=True` at
  `shots = max(group counts)` and truncate each circuit's memory to its own multinomial count;
  concatenate in draw order (unbiased). Measured Aer cost ~1.25x the raw shot count at
  2000/setting. [nb §4]
- Track-B ancilla quadratures `rho^(X), rho^(Y)` (modified ancilla readout) are out of T0 scope;
  noted only so nobody "fixes away" the final `h(anc)`. [PRL; nb]

---

## 5. Budget & grid

- **Frozen budget** (official; spec §4.3 as quoted by nb §0.2): `N_TIMES = 64`, `DT = 0.2`,
  `SHOTS = 2000` per `(t, phi)`; quadratures `phi in {0, -pi/2}`; `TS = arange(64) * 0.2`,
  `T_MAX = 12.6`.

  **Total kept shots = 64 x 2 x 2000 = 256,000.** Distinct circuits `<= 128 x 27 = 3456`;
  actual count: `TBD-user(run_summary.json)`.

  Declaration line for slides/README (Advanced rubric, Topic-5 slide: "under a fixed shot
  budget"): *"All Part-A and Part-B numbers derive from one shared record set: 128 settings x
  2000 shots = 256,000 total shots (exact evolution path; every draw seeded from SEED = 2026)."*
- The `"fast"` grid (`32, 0.4, 2000`; `T_max = 12.4`; half the total) is debug-only;
  `budget_sensitive` checkpoints go advisory there; **nothing measured at `"fast"` is
  reportable**. [nb §0.2]
- **Re-allocation rule:** shots may be re-allocated or the grid re-spaced **only** at the same
  total (256,000) and the same `T_MAX`. [nb §0.2]
- **Nyquist margin (shown, not eyeballed)** `[derived]`: the two quadratures form a complex
  series, so the alias-free band is `|E| < pi/DT = 15.708`.
  - A priori triangle bound (no ED needed):
    `||H||_2 <= 2*(2*0.65 + 0.25) + (0.40 + 0.50 + 0.15) = 4.15` -> margin
    `>= 15.708 / 4.15 = 3.8x`.
  - With the notebook-stated full spectral radius `2.64` [nb §0.2]: margin `~ 5.9x`.
    Checkpoint 2 asserts `max|E| < pi/DT`; Gate 0 re-prints the radius (`G0.8`):
    `TBD-user(G0 paste §5.6)`.
- **Resolution margin** `[derived on nb numbers]`: Rayleigh `2 pi / T_MAX = 0.499` vs smallest
  populated spacing `1.03` -> factor `~ 2.1x` (Checkpoint 2 asserts spacing `> 2 pi / T_MAX`).
  Hann-window center-to-first-null is `4 pi / T_MAX ~ 0.997` — right at the `1.03` spacing
  between the `E ~ -0.48` line and the dominant (`p ~ 0.63`) `E = 0.55` line, so the
  windowed-DFT **baseline is expected to bury the `-0.48` line** at this budget [nb §7.1]. That
  is a known systematic of the baseline, not a bug; the deliverable analyzer is matrix pencil +
  shared-energy least squares (§9), which is not lobe-limited. **Do not retune `DT`/`N_TIMES`
  in response.**
- **Per-point shot-noise law** `[derived]`: `sem[Re chi] <= 1/sqrt(2000) = 0.0224` (`a = +-1`).
  For `chi_Q`: `E[(a Qhat)^2] = E[Qhat^2] = sum_i E[Zhat_i^2] + sum_{i != j} E[Zhat_i Zhat_j]
  <= 3*3 + 6*1 = 15` -> `sem[Re chi_Q] <= sqrt(15/2000) ~ 0.087` per point per quadrature.
  Measured sems go to RESULTS rows: `TBD-user(RESULTS)`.
- **Pooling gains** `[nb §1.2 + derived]`: `<Q>` pools all 128 settings -> `sqrt(128) ~ 11x`
  sem reduction vs a single setting (both evolution paths); `<H>` gets the same on the exact
  path only.
- **Calibration anchors at the frozen budget** [nb Checkpoint 6, SEED 2026]: `chi` rms error
  ~ `0.026` (vs the `0.0224` single-point floor above); `<H>` within `+-0.01`; `<Q>` within
  `+-0.006`; sem-vs-shots log-log slope ~ `-0.52`. Re-measured values: `TBD-user(RESULTS)`.

### 5.6 Gate-0 output (verbatim paste slot)

```
TBD-user( run `python gate0_benchmark.py` per §8.2 and paste EVERY printed line here, unedited:
          the [check], [bench], [grid], [xchk], [recov] lines and the final GATE0 verdict.
          Checkpoint 2's all-PASS block from the notebook is pasted below it. )
```

---

## 6. Environment

- Pins (frozen repo `requirements.txt` / `environment.yml`): `python 3.12` (env: `3.12.13`),
  `qiskit==2.5.1`, `qiskit-aer==0.17.2`, `numpy==2.5.2`, `scipy==1.18.0`,
  `matplotlib==3.11.1`, `pylatexenc==2.11`. The notebook additionally asserts `qiskit >= 2.1`.
- Randomness: master `SEED = 2026`; every draw derives from it. Per-purpose seeds via
  `sub_seed(tag, index)` = `SeedSequence([SEED, zlib.crc32(tag.encode()) % 2**31, index])` —
  `zlib.crc32`, never `hash()` (per-process randomised). Sweep settings are seeded via
  `SeedSequence.spawn`. [nb §0.2, §6]
- `STRICT_CHECKS = True`. `check()` semantics: deterministic convention checks are hard at every
  budget; `budget_sensitive` checks go advisory when `BUDGET != "full"`; `soft` checks (Krylov
  GEVP, noise sanity) never fail the notebook. Acceptance test throughout: `sigma_gate`,
  `|est - ref| < 5 sigma`. [nb §0.2]
- Execution route: Aer with `memory=True` (per-shot bitstrings are required by `parse_memory`);
  a `SamplerV2`-equivalent route is allowed on the **ideal** simulator only. [nb §4]

---

## 7. File schemas (see `schemas.md`; reconciliation here)

- `RESULTS.md` — one row per reported number:
  `R### | quantity | value | 95% CI | shots x seeds | producing cell/file | timestamp`.
- `BUGLOG.md` — `B## | symptom | root cause | fix | prevention rule`.
- Signal CSVs (consumed by `spectral.py`): header **exactly** `t,re,im`; one file per seed per
  signal; naming `data/g1_dt{dt}_N{N}_s{shots}_seed{k}.csv` and the same pattern for `gM`.
  Frozen instantiation: `data/g1_dt0.2_N64_s2000_seed{k}.csv` and
  `data/gM_dt0.2_N64_s2000_seed{k}.csv` — write `dt` as the literal `0.2` (no trailing-zero
  drift). All seeds share an identical `t` column (the loader enforces this).
- Column semantics: `g1 == chi = Tr[U rho]`, `gM == chi_Q = Tr[Q U rho]` (§0); `re, im` are the
  `phi = 0` and `phi = -pi/2` estimates respectively (§3 sign table).
- CI convention (T0 decision): the bootstrap returns `sigma_boot` via `np.nanstd`; RESULTS rows
  report `95% CI = +-1.96 * sigma_boot` unless a percentile CI is pasted instead; every
  statistical claim sits on `>= 10 seeds` (house law).
- Freeze schedule (binding): Aug 12 ~20:30 Gate 0 (exact_ref green) | Aug 12 24:00 Gate 1
  (estimators match statevector) | Aug 13 13:00 hardware go/no-go | Aug 13 21:00 code+repo
  freeze | Aug 14 09:30 audit+judge | Aug 14 10:30 upload (11:00 hard deadline).

---

## 8. Gate 0 — `exact_ref.py`: spec, required adaptation, asserts

### 8.1 Shipped-script contract (pure numpy; little-endian, qubit `i` at kron slot `n-1-i`)

| function | contract |
|---|---|
| `build_xxz(n=3, J=1.0, delta=0.5, h=0.31)` | `H = sum_i [J(XX+YY) + delta ZZ] + h*M`, `M = sum_i Z_i`. **Defaults are NOT the benchmark** — see §8.2. |
| `convention_checks(H, M) -> (comm_norm, min_gap, evals)` | `comm_norm = ||[H,M]||`; `min_gap` over the **full** spectrum. |
| `spectral_data(H, M, psi0) -> (evals, w, m)` | `w_k = |<k|psi0>|^2`, `m_k = <k|M|k>` (joint eigenbasis is automatic: `[H,M] = 0` with distinct `E_k`). |
| `g_signals(tgrid, evals, w, m)` | spectral sums `g1 = sum_k w_k e^{-i E_k t}`, `gM = sum_k w_k m_k e^{-i E_k t}`. |
| `rk4_g1_gM(H, M, psi0, tgrid)` | independent RK4 time integration; cross-checks both signals. |
| `dtft(g, tgrid, wgrid, window=True)` | Hann-windowed DTFT with `e^{+i w t}` kernel, normalised by `sum(hann)`. Sign law `[derived]`: for `g = e^{-iEt}` the kernel cancels the phase, so the magnitude peaks at `w = +E`. A raw `np.fft.fft` (kernel `e^{-i...}`) would place the peak at `f = -E/2pi` — the explicit `+` kernel removes that mirror trap. |
| `find_peaks(mag, wgrid, rel_thresh=0.03, min_sep=None)` | local maxima + quadratic refinement; `min_sep` defaults to the Hann-lobe scale (sidelobe guard). |
| `recover(g1, gM, tgrid, wgrid=None, rel_thresh=0.005) -> peaks` | per peak dict: `E`; `weight` (amplitude normalised by the window sum); `m = Re[S_M(w*) / S_1(w*)]` at the peak. |
| `suggest_grid(evals, min_gap, nyquist_margin=4.0, lobe_factor=2.0)` | `dt = pi/(4 * Emax)`; `N = ceil(T/dt)` with `T = 2 * 8pi / min_gap` (Hann full null-to-null lobe is `8pi/T`). |
| `_selftest()` | runs the whole chain on the shipped defaults with `psi0 = |+++>`, clips `N = min(N, 4096)`, prints `SELFTEST PASS/FAIL`. |

### 8.2 Required benchmark adaptation (the only site-specific code T0 authorises)

The shipped `_selftest` uses the `build_xxz` defaults and `|+++>`. The benchmark needs the frozen
`(H, Q, psi)` of §2, and `suggest_grid` fed with the **populated** gap (§2 D2/D3: the
unpopulated pair near `E ~ 0.45` sets the full-spectrum gap; seeding the grid with it inflates
`N` to the 4096 clip and makes the printed `Hann lobe < gap` line compare against an irrelevant
gap — cosmetic, but we spec it away). Save as `gate0_benchmark.py` next to `exact_ref.py`; run
`python gate0_benchmark.py`; paste all output into §5.6.

```python
# gate0_benchmark.py -- T0-approved Gate-0 driver (the ONLY site-specific code authorised by
# CONVENTIONS.md §8). Builds the FROZEN benchmark of §2 and reruns the shipped exact_ref
# self-test sequence on it, plus the §8.3 benchmark asserts.   Run:  python gate0_benchmark.py
import numpy as np
import exact_ref as er

def build_benchmark(n=3, J=0.65, dzz=0.25, h=(0.40, -0.50, 0.15)):
    d = 2 ** n
    H = np.zeros((d, d), dtype=complex)
    for i in range(n - 1):
        H += J * (er.two_site(er.PX, i, er.PX, i + 1, n)
                  + er.two_site(er.PY, i, er.PY, i + 1, n))
        H += dzz * er.two_site(er.PZ, i, er.PZ, i + 1, n)
    for i, hi in enumerate(h):
        H += hi * er.op_on(er.PZ, i, n)
    M = sum(er.op_on(er.PZ, i, n) for i in range(n))        # Q = Z0 + Z1 + Z2
    return H, M

def psi_benchmark(n=3, theta=1.3):
    v = np.zeros(2 ** n, dtype=complex)
    v[0], v[1] = np.cos(theta / 2), np.sin(theta / 2)       # cos(0.65)|000> + sin(0.65)|001>
    return v

def main():
    ok = True
    n = 3
    H, M = build_benchmark(n=n)
    comm, gap_full, evals = er.convention_checks(H, M)
    print(f"[check] ||[H,Q]|| = {comm:.2e}   (G0.1 want < 1e-10)")
    print(f"[check] min spectral gap (FULL) = {gap_full:.4f}   (G0.2 want > 1e-3; expected small,"
          f" set by the unpopulated pair near E~0.45, nb §1.4)")
    ok &= comm < 1e-10 and gap_full > 1e-3

    psi = psi_benchmark(n=n)
    evals_d, w, m = er.spectral_data(H, M, psi)
    m_round = np.round(m)
    print(f"[check] labels m_k integer to {np.max(np.abs(m - m_round)):.2e}; "
          f"sum w = {w.sum():.6f}   (G0.9)")
    ok &= np.max(np.abs(m - m_round)) < 1e-8 and abs(w.sum() - 1) < 1e-10

    pop = w > 1e-3
    gap_pop = float(np.min(np.diff(np.sort(evals_d[pop]))))
    sectors = sorted({int(x) for x in m_round[pop]})
    print(f"[bench] populated lines = {int(pop.sum())} (G0.5 want 4); sectors = {sectors} "
          f"(G0.6 want [1, 3]); min POPULATED gap = {gap_pop:.4f}")
    for E_k, w_k, m_k in sorted(zip(evals_d[pop], w[pop], m_round[pop])):
        print(f"[bench]   E = {E_k:+.6f}   w = {w_k:.6f}   q = {int(m_k):+d}")
    ok &= int(pop.sum()) == 4 and sectors == [1, 3]

    c2, s2 = np.cos(0.65) ** 2, np.sin(0.65) ** 2
    H_expect, Q_expect = 0.55 * c2 - 0.75 * s2, 1 + 2 * c2      # §2 closed forms
    H_num = float(np.real(psi.conj() @ H @ psi))
    Q_num = float(np.real(psi.conj() @ M @ psi))
    print(f"[bench] <H> = {H_num:+.6f} vs closed form {H_expect:+.6f}; "
          f"<Q> = {Q_num:+.6f} vs {Q_expect:+.6f}   (G0.7 want < 1e-12)")
    ok &= abs(H_num - H_expect) < 1e-12 and abs(Q_num - Q_expect) < 1e-12

    dt, N, Emax = er.suggest_grid(evals_d, gap_pop)             # POPULATED gap (§2 D2/D3)
    N = min(N, 4096)
    tgrid = dt * np.arange(N)
    print(f"[grid ] Emax={Emax:.3f}  dt={dt:.4f} (Nyquist margin 4x)  N={N}  T={dt*N:.1f}  "
          f"Hann lobe={8*np.pi/(dt*N):.4f} < gap {gap_pop:.4f}")
    print(f"[bench] FROZEN grid dt=0.2 N=64 T_max=12.6: Nyquist pi/dt={np.pi/0.2:.3f} vs "
          f"Emax {Emax:.3f}; 2pi/T_max={2*np.pi/12.6:.3f} and Hann half-lobe "
          f"{4*np.pi/12.6:.3f} vs populated gap {gap_pop:.4f}")
    ok &= Emax < np.pi / 0.2                                    # G0.8 no aliasing on frozen grid

    g1, gM = er.g_signals(tgrid, evals_d, w, m)
    ok &= abs(g1[0] - 1.0) < 1e-12 and abs(gM[0] - Q_expect) < 1e-12    # G0.7 at t = 0
    coarse = tgrid[:: max(1, N // 64)][:64]
    g1_rk, gM_rk = er.rk4_g1_gM(H, M, psi, coarse)
    g1_sp, gM_sp = er.g_signals(coarse, evals_d, w, m)
    e1 = float(np.max(np.abs(g1_rk - g1_sp)))
    eM = float(np.max(np.abs(gM_rk - gM_sp)))
    print(f"[xchk ] spectral-sum vs RK4:  max|dg1|={e1:.2e}  max|dgM|={eM:.2e}   "
          f"(G0.3 want < 1e-6)")
    ok &= e1 < 1e-6 and eM < 1e-6

    peaks = er.recover(g1, gM, tgrid)
    truth = sorted(zip(evals_d[pop], w[pop], m_round[pop]))
    err_E = err_w = err_m = 0.0
    matched = 0
    for E_t, w_t, m_t in truth:
        cand = min(peaks, key=lambda p: abs(p["E"] - E_t))
        if abs(cand["E"] - E_t) > 0.1:
            continue
        matched += 1
        err_E = max(err_E, abs(cand["E"] - E_t))
        err_w = max(err_w, abs(cand["weight"] - w_t))
        err_m = max(err_m, abs(cand["m"] - m_t))
    print(f"[recov] matched {matched}/{len(truth)}  max|dE|={err_E:.2e}  "
          f"max|dw|={err_w:.2e}  max|dm|={err_m:.2e}   (G0.4)")
    ok &= matched == len(truth) and err_E < 5e-3 and err_w < 2e-2 and err_m < 0.1

    print("GATE0", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
```

### 8.3 Gate-0 assert list (all must hold; driver prints `GATE0 PASS`)

- `G0.1` `||[H, Q]|| < 1e-10` (dense route; in-notebook twin: Checkpoint 2, `< 1e-12` on the
  `SparsePauliOp` route).
- `G0.2` full-spectrum `min_gap > 1e-3`; anything below routes to the §2 fallback ladder
  (D3-D5).
- `G0.3` spectral-sum vs independent RK4: `max|dg1|, max|dgM| < 1e-6`.
- `G0.4` recovery on the exact signals: matched = **all** populated lines (`w > 1e-3`), with
  `|dE| < 5e-3`, `|dw| < 2e-2`, `|dm| < 0.1`.
- `G0.5` exactly 4 populated lines.  `G0.6` populated sectors `== {+1, +3}`.
- `G0.7` closed forms of §2: `|<H> - (0.55 cos^2 0.65 - 0.75 sin^2 0.65)| < 1e-12`,
  `|<Q> - (1 + 2 cos^2 0.65)| < 1e-12`, and `g1(0) = 1`, `gM(0) = <Q>` to `1e-12`.
- `G0.8` frozen-grid aliasing guard, re-verified numerically: `Emax < pi/0.2` (§5 margin).
- `G0.9` labels integer to `< 1e-8`; `sum_k w_k = 1 +- 1e-10`.
- Companion in-notebook check: Checkpoint 2 prints all-PASS at `BUDGET = "full"`:
  `TBD-user(Checkpoint 2 paste, §5.6)`.

---

## 9. Frozen API signatures (binding; bodies live in the notebook)

| symbol | signature -> returns | status | law notes |
|---|---|---|---|
| `parse_memory` | `(memory, n) -> (outcomes (N,n) +-1, ancilla (N,) +-1)` | stub (user) | §1 endianness; pinned by the Checkpoint-4 pair. |
| `build_controlled_evolution` | `(ham, t, method, reps) -> Gate` | stub (user) | control = **first** qubit; `exact` vs `trotter` per §2; synthesize-then-control. |
| `build_shadow_hadamard_circuit` | `(ham, t, phi, basis, prep, method, reps, measure)` | given | frozen circuit order of §1. |
| `run_shadow_hadamard` | `(ham, t, phi, n_shots, seed, prep=None, method="exact", reps=2, backend=None) -> ShadowRecords(t, phi, bases (N,n) codes, outcomes (N,n) +-1, ancilla (N,) +-1, n_circuits)` | stub (user) | grouping law of §4; `memory=True`. |
| `pauli_terms` | `(obs) -> [({qubit: code}, coeff), ...]` | stub (user) | reads labels via `label[::-1]` so string index = qubit (§1 rule 1); identity qubits excluded from support. |
| `pauli_snapshot_values` | `(records, support) -> (N,)` | stub (user) | the `Phat` of §4, per shot. |
| `estimate_hadamard_signal` | `(rec_re, rec_im) -> (chi, sem_re, sem_im)` | **given** | `chi = mean(a_re) + i * mean(a_im)`; sems `std(ddof=1)/sqrt(N)`. |
| `estimate_system_observable` | `(records_list, obs) -> (est, sem)` | stub (user) | pooling legality per the §3 slot table — the **caller** chooses the record list. |
| `estimate_joint_observable` | `(rec_re, rec_im, obs) -> (chi_O, sem_re, sem_im)` | stub (user) | per-`t`; `a * Phat` per quadrature; guarded by `_check_quadrature_pair` (given) enforcing the `(0, -pi/2)` pairing. |
| `SweepResult`, `run_time_sweep` | `(...)` | given | keeps **all** records; per-setting seeds via `SeedSequence.spawn`. |
| `dft_spectrum` | `(ts, y, e_grid)` | given | Hann; `e^{+iEt}` kernel; normalised by the window sum (§8.1 sign law). |
| `dft_peak_labels` | `(...)` | stub (user) | baseline: peaks of `|S_1|`, labels `q = Re[S_Q/S_1]` at each peak; expected to under-resolve `E ~ -0.48` at the frozen budget (§5). |
| `matrix_pencil` | `(y, dt, n_modes=None, sv_threshold=0.06) -> (energies, rank)` | stub (user) | Hankel split `l = n//2`; `z_k = e^{-i E_k dt}` => `E_k = -arg(z_k)/dt` — the minus sign is law (mirror trap). |
| `amplitudes_at` | `(...)` | given | Vandermonde in `e^{-i E t}`; `lstsq`. |
| `reconstruct` | `(ts, chi, chi_q, n_modes=None, weight_threshold=0.02) -> (energies, weights, labels, rank)` | stub (user) | `weights = Re(amps)`, `labels = Re(amps_q / amps)`; drop modes with weight `< weight_threshold`. |
| `bootstrap_uncertainties` | `(...)` | stub (user) | parametric: perturb each point by its sem (both quadratures), re-run `reconstruct`, nearest-neighbour match to the central solution with a rejection radius, `np.nanstd -> sigma_boot`; CI law of §7. |

**Data-diet rule (hard).** Part-B estimators consume only the measured arrays
`(ts, chi, chi_q)`. Exact diagonalisation appears **only** on the evaluation side
(Checkpoint 7.7 tripwire).

— end of CONVENTIONS.md —
