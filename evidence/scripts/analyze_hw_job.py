import nbformat
from nbclient import NotebookClient

PREFIX_PATH = "/tmp/qh26_scratch/prefix_cp7.ipynb"

nb = nbformat.read(PREFIX_PATH, as_version=4)

hw_cell_src = '''
from qiskit_ibm_runtime import QiskitRuntimeService

_service = QiskitRuntimeService()
_job = _service.job("d9u95vs98n5s7392iao0")
print("status:", _job.status())
_result = _job.result()

_bits_re = _result[0].data.c.get_bitstrings()
_bits_im = _result[1].data.c.get_bitstrings()
print("shots re/im:", len(_bits_re), len(_bits_im))

_outc_re, _anc_re = parse_memory(_bits_re, N_SYS)
_outc_im, _anc_im = parse_memory(_bits_im, N_SYS)

_rec_re = ShadowRecords(t=0.9, phi=PHI_RE, bases=np.tile([0, 1, 2], (len(_anc_re), 1)),
                        outcomes=_outc_re, ancilla=_anc_re, n_circuits=1)
_rec_im = ShadowRecords(t=0.9, phi=PHI_IM, bases=np.tile([0, 1, 2], (len(_anc_im), 1)),
                        outcomes=_outc_im, ancilla=_anc_im, n_circuits=1)

_chi_hw, _s_re, _s_im = estimate_hadamard_signal(_rec_re, _rec_im)
_chi_ref = exact_chi(HAM, PSI, [0.9])[0]
print(f"HARDWARE  chi(0.9) = {_chi_hw.real:+.4f} + {_chi_hw.imag:+.4f}j   "
      f"(sem_re={_s_re:.4f}, sem_im={_s_im:.4f})")
print(f"EXACT     chi(0.9) = {_chi_ref.real:+.4f} + {_chi_ref.imag:+.4f}j")
print(f"deviation: re {abs(_chi_hw.real - _chi_ref.real)/_s_re:.1f} sigma, "
      f"im {abs(_chi_hw.imag - _chi_ref.imag)/_s_im:.1f} sigma")

# unweighted shadow estimate of Q and Z0 under rho^(I)(0.9) -- for reference, NOT the input <Q>
_q_hw, _q_sem = estimate_system_observable([_rec_re, _rec_im], CHARGE)
_q_ref_marg = exact_system_marginal_expectation(HAM, PSI, CHARGE, 0.9)
print(f"HARDWARE  <Q>_rho^(I)(0.9) = {_q_hw:+.4f} +- {_q_sem:.4f}   (exact marginal {_q_ref_marg:+.4f}, "
      f"{abs(_q_hw - _q_ref_marg)/_q_sem:.1f} sigma)")
'''

nb.cells.append(nbformat.v4.new_code_cell(source=hw_cell_src))

client = NotebookClient(nb, timeout=1200, kernel_name="qh26-t5")
client.execute()

nbformat.write(nb, "/tmp/qh26_scratch/executed_hw_analysis.ipynb")
print("DONE")
