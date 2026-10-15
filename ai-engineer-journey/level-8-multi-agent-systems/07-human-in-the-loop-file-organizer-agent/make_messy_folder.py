"""Creates workspace/downloads: a messy Downloads folder for the agent to tidy."""
from pathlib import Path

FILES = {
    "IMG_2041.jpg": "fake image bytes", "IMG_2042.jpg": "fake image bytes", "screenshot 2026-09-01.png": "png",
    "invoice_october.pdf": "%PDF invoice", "Invoice_October (1).pdf": "%PDF invoice", "tax_return_2025.pdf": "%PDF tax",
    "resume_final_FINAL_v3.docx": "resume", "notes from lecture 4.txt": "Backprop = chain rule applied backwards.",
    "setup_installer.exe": "MZ...", "song.mp3": "ID3", "data_export.csv": "a,b\n1,2\n", "untitled.txt": "",
    "project_ideas.md": "# Ideas\n- RAG over my notes\n- MNIST drawing app", "old_backup.zip": "PK",
}


def build(root=Path(__file__).parent / "workspace" / "downloads"):
    folder = Path(root)
    folder.mkdir(parents=True, exist_ok=True)
    for name, content in FILES.items():
        (folder / name).write_text(content, encoding="utf-8")
    return folder


if __name__ == "__main__":
    print(f"Created {len(FILES)} messy files in {build()}")
