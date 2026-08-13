"""deck/qr_slides.png -- QR code for the master deck, embedded on slides.tex's
'Reproduce it' frame and trackb.tex's closing frame.

Points at the raw GitHub URL for deck/slides.pdf on the public repo, so scanning it opens
the PDF directly (no repo browsing needed). Rerun after any push where the branch name or
repo path changes -- the URL below is not derived automatically, it is the actual pushed
location, checked with `curl -sI` before this file was generated.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import qrcode

URL = "https://raw.githubusercontent.com/mnsh0409/Qiskit-Hackathon-2026/master/deck/slides.pdf"

img = qrcode.make(URL, error_correction=qrcode.constants.ERROR_CORRECT_M, border=2)
img = img.resize((600, 600))
img.save(os.path.join(REPO, "deck/qr_slides.png"))
print(f"wrote deck/qr_slides.png for {URL}")
