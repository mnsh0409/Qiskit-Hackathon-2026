import nbformat
from nbclient import NotebookClient

PREFIX = "/tmp/qh26_scratch/prefix_c11_nokrylov.ipynb"

nb = nbformat.read(PREFIX, as_version=4)

cell = r'''
# Going-further (robustness) item 2: does the symmetry label survive noise?
# Claim under test: q_hat is a RATIO of two quantities measured on the SAME shots, so a common
# multiplicative damping should largely cancel -- even though p_hat is biased low by that damping.
# Controlled comparison: ideal-Trotter vs noisy-Trotter, identical seeds and identical circuits.

print(f"grid: {len(TS_N)} times, dt = {TS_N[1]-TS_N[0]:.2f}, T_max = {TS_N[-1]:.1f}, "
      f"{SHOTS_NOISE} shots/quadrature, trotter reps=1")
print(f"measured damping (mean |chi| noisy/ideal) = {damp:.3f}\n")

_res = {}
for _tag, _sw in (("ideal", sweep_ideal_tr), ("noisy", sweep_noisy)):
    try:
        _e, _p, _q, _r = reconstruct(TS_N, _sw.chi, _sw.chi_obs["Q"])
        _res[_tag] = (_e, _p, _q, _r)
        print(f"{_tag:>5}: rank {_r}, {len(_e)} modes surviving")
        for _ee, _pp, _qq in zip(_e, _p, _q):
            print(f"         E = {_ee:+8.4f}   p = {_pp:+7.4f}   q_hat = {_qq:+7.3f} "
                  f"-> {int(np.rint(_qq)):+d}")
    except Exception as _exc:
        print(f"{_tag:>5}: reconstruct FAILED -- {type(_exc).__name__}: {_exc}")
    print()

# Match noisy modes to ideal modes and to the exact truth (evaluation only)
if "ideal" in _res and "noisy" in _res:
    _ei, _pi, _qi, _ = _res["ideal"]
    _en, _pn, _qn, _ = _res["noisy"]
    print(f"{'exact E':>9} {'exact q':>8} | {'E ideal':>9} {'E noisy':>9} | "
          f"{'p ideal':>8} {'p noisy':>8} {'p ratio':>8} | {'q ideal':>8} {'q noisy':>8} {'dq':>7}")
    print("-" * 104)
    _pr, _dq = [], []
    for _e0, _q0 in zip(E_EXACT, Q_EXACT_LABELS):
        _ji = int(np.argmin(np.abs(_ei - _e0)))
        _jn = int(np.argmin(np.abs(_en - _e0)))
        _hit_i = abs(_ei[_ji] - _e0) < 0.35
        _hit_n = abs(_en[_jn] - _e0) < 0.35
        if not (_hit_i and _hit_n):
            print(f"{_e0:+9.4f} {_q0:+8d} |  (unmatched: ideal {'hit' if _hit_i else 'MISS'}, "
                  f"noisy {'hit' if _hit_n else 'MISS'})")
            continue
        _ratio = _pn[_jn] / _pi[_ji]
        _delta = _qn[_jn] - _qi[_ji]
        _pr.append(_ratio); _dq.append(_delta)
        print(f"{_e0:+9.4f} {_q0:+8d} | {_ei[_ji]:+9.4f} {_en[_jn]:+9.4f} | "
              f"{_pi[_ji]:+8.4f} {_pn[_jn]:+8.4f} {_ratio:8.3f} | "
              f"{_qi[_ji]:+8.3f} {_qn[_jn]:+8.3f} {_delta:+7.3f}")

    if _pr:
        print(f"\nWEIGHTS  p_noisy/p_ideal : mean {np.mean(_pr):.3f}, spread {np.std(_pr):.3f}   "
              f"(damping of |chi| was {damp:.3f})")
        print(f"LABELS   q_noisy - q_ideal: mean {np.mean(_dq):+.3f}, "
              f"max |dq| {np.max(np.abs(_dq)):.3f}")
        _lab_ok_i = [int(np.rint(_qi[int(np.argmin(np.abs(_ei-_e0)))])) == _q0
                     for _e0, _q0 in zip(E_EXACT, Q_EXACT_LABELS)
                     if abs(_ei[int(np.argmin(np.abs(_ei-_e0)))] - _e0) < 0.35]
        _lab_ok_n = [int(np.rint(_qn[int(np.argmin(np.abs(_en-_e0)))])) == _q0
                     for _e0, _q0 in zip(E_EXACT, Q_EXACT_LABELS)
                     if abs(_en[int(np.argmin(np.abs(_en-_e0)))] - _e0) < 0.35]
        print(f"labels correct after rounding: ideal {sum(_lab_ok_i)}/{len(_lab_ok_i)}, "
              f"noisy {sum(_lab_ok_n)}/{len(_lab_ok_n)}")
'''

nb.cells.append(nbformat.v4.new_code_cell(source=cell))
NotebookClient(nb, timeout=2400, kernel_name="qh26-t5").execute()
nbformat.write(nb, "/tmp/qh26_scratch/executed_robustness2.ipynb")
print("DONE")
