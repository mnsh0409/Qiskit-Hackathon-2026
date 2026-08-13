import nbformat
from nbclient import NotebookClient

PREFIX_PATH = "/tmp/qh26_scratch/prefix_cp5.ipynb"

nb = nbformat.read(PREFIX_PATH, as_version=4)

hw_cell_src = '''
import json
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

with open("/home/martin/Documents/QiskitHackathon/2026/apikey.json") as _f:
    _ibm_key = json.load(_f)["apikey"]

_service = QiskitRuntimeService(channel="ibm_cloud", token=_ibm_key, instance="Martin")
_candidates = [b for b in _service.backends() if b.status().operational]
_backend = min(_candidates, key=lambda b: b.status().pending_jobs)
print("selected backend:", _backend.name, "pending_jobs=", _backend.status().pending_jobs,
      "num_qubits=", _backend.num_qubits)

T_HW = 0.9
BASIS_HW = [0, 1, 2]
SHOTS_HW = 2000
circuits_hw = [build_shadow_hadamard_circuit(HAM, T_HW, phi, basis=BASIS_HW,
                                             method="trotter", reps=1)
              for phi in (PHI_RE, PHI_IM)]
isa_circuits = transpile(circuits_hw, backend=_backend, optimization_level=1,
                         seed_transpiler=sub_seed("hw-transpile"))
print("transpiled depth:", [c.depth() for c in isa_circuits],
      "2q-gate counts:", [c.count_ops() for c in isa_circuits])

sampler = SamplerV2(mode=_backend)
job = sampler.run(isa_circuits, shots=SHOTS_HW)
print("JOB_ID:", job.job_id())
print("BACKEND:", _backend.name)
print("STATUS:", job.status())
print("SHOTS_PER_CIRCUIT:", SHOTS_HW, " N_CIRCUITS:", len(isa_circuits),
      " T:", T_HW, " BASIS:", BASIS_HW, " METHOD: trotter reps=1")
'''

nb.cells.append(nbformat.v4.new_code_cell(source=hw_cell_src))

client = NotebookClient(nb, timeout=1200, kernel_name="qh26-t5")
client.execute()

nbformat.write(nb, "/tmp/qh26_scratch/executed_hw_submit.ipynb")
print("DONE")
