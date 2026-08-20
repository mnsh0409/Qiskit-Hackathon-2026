import sys, subprocess, markdown, os

CSS = """body{font-family:'DejaVu Sans',sans-serif;font-size:10.5pt;color:#111;max-width:18cm;margin:0 auto}
h1{font-size:17pt;border-bottom:2px solid #2a78d6;padding-bottom:4px}h2{font-size:13.5pt;color:#1a4e8a}
code,pre{font-family:'DejaVu Sans Mono',monospace;font-size:9pt;background:#f4f4f0}
pre{padding:8px;border:1px solid #ddd;white-space:pre-wrap}table{border-collapse:collapse;font-size:9.5pt}
td,th{border:1px solid #bbb;padding:3px 7px}img{max-width:100%}"""

def convert(md_path, pdf_path):
    title = os.path.splitext(os.path.basename(md_path))[0]
    text = open(md_path, encoding="utf-8").read()
    html_body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title><style>{CSS}</style></head><body>{html_body}</body></html>"
    html_path = f"/tmp/_md2pdf_{title}.html"
    open(html_path, "w", encoding="utf-8").write(html)
    subprocess.run([
        "google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", f"file://{html_path}",
    ], check=True, capture_output=True)
    print(pdf_path)

if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
