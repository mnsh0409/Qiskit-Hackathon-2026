import json, sys

src = "/home/martin/Documents/QiskitHackathon/2026/shadow_hadamard_challenge_PARTICIPANT.ipynb"
dst = sys.argv[1]
upto = int(sys.argv[2])  # inclusive cell index

nb = json.load(open(src, encoding="utf-8"))
nb["cells"] = nb["cells"][: upto + 1]
with open(dst, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print(f"wrote {dst} with {len(nb['cells'])} cells (0..{upto})")
