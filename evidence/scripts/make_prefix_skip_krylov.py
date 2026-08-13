import json

src = "/home/martin/Documents/QiskitHackathon/2026/shadow_hadamard_challenge_PARTICIPANT.ipynb"
dst = "/tmp/qh26_scratch/prefix_c11_nokrylov.ipynb"

nb = json.load(open(src, encoding="utf-8"))
# cells 0..82 (through Checkpoint 7 + Going-further), skip 83..88 (Challenge 10 Krylov bonus,
# post-freeze-only per CLAUDE.md), resume 89..93 (Part C bonus -- noise robustness, Challenge 11)
nb["cells"] = nb["cells"][:83] + nb["cells"][89:94]
with open(dst, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print(f"wrote {dst} with {len(nb['cells'])} cells")
