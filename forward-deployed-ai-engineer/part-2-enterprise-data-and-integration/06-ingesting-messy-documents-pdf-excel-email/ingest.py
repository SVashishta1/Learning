# ingest.py: turn messy company files (PDF, Excel, email, HTML) into clean text chunks with metadata.
#
#   python ingest.py samples/                         (summary of every file)
#   python ingest.py samples/ --out chunks.jsonl      (also save every chunk, one JSON object per line)
#   python ingest.py samples/ --show 3                (print the first 3 chunks in full)
#
# Every RAG system starts here. The pipeline for each file:
#   load (one loader per format) -> clean -> normalise -> split into chunks -> add metadata -> save
import argparse
import hashlib
import json
import re
import unicodedata
from email import policy
from email.parser import BytesParser
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from pypdf import PdfReader

MAX_CHARS = 800          # a chunk is at most this long (about 200 tokens): small enough to retrieve precisely
OVERLAP_CHARS = 200      # carry a short last paragraph into the next chunk, so context isn't cut mid-thought


# ---------- cleaning helpers ----------

def normalise(text):
    """Make text consistent: one form of each character, single spaces, at most one blank line in a row."""
    text = unicodedata.normalize("NFKC", text)              # 'ﬁ' -> 'fi', non-breaking space -> space, etc.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)                     # many spaces/tabs -> one space
    text = re.sub(r" *\n *", "\n", text)                    # no spaces around line breaks
    text = re.sub(r"\n{3,}", "\n\n", text)                  # at most one empty line
    return text.strip()


def fix_hyphenation(text):
    """'deliv-\\nery' -> 'delivery': PDFs often split words at the end of a line."""
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def file_fingerprint(path):
    """A short hash of the file's bytes: the same file always gets the same value (useful to skip unchanged files)."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


# ---------- one loader per format; each returns a list of {"text": ..., "metadata": {...}} ----------

def load_pdf(path):
    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    # Lines that appear on most pages are headers and footers ("Page 1 of 3" differs only by its number).
    pattern = lambda line: re.sub(r"\d+", "#", line.strip())
    counts = {}
    for page in pages:
        for line in set(pattern(l) for l in page.splitlines() if l.strip()):
            counts[line] = counts.get(line, 0) + 1
    repeated = {line for line, n in counts.items() if len(pages) > 1 and n >= max(2, len(pages) // 2)}
    docs, warnings = [], []
    for number, page in enumerate(pages, start=1):
        kept = [l for l in page.splitlines() if pattern(l) not in repeated]
        text = fix_hyphenation("\n".join(kept))
        # Join lines that are just wrapped text: a line not ending a sentence + a line starting in lower case.
        text = re.sub(r"(?<![.:!?])\n(?=[a-z(])", " ", text)
        if not text.strip():
            warnings.append(f"page {number} has no text layer (scanned image?): needs OCR")
            continue
        docs.append({"text": text, "metadata": {"page": number}})
    return docs, warnings


def load_excel(path):
    docs, warnings = [], []
    for sheet, table in pd.read_excel(path, sheet_name=None, header=None).items():   # every sheet, raw
        table = table.dropna(how="all")                          # drop completely empty rows
        filled = table.notna().sum(axis=1)
        header_row = filled[filled >= 2].index[0]               # first row with 2+ values = the real header
        notes = [str(v) for v in table.loc[:header_row - 1].stack().dropna()]     # title rows above the header
        data = table.loc[header_row + 1:]
        footer = data[data.notna().sum(axis=1) == 1]            # rows with one value under the table = notes
        data = data.drop(footer.index)
        notes += [str(v) for v in footer.stack().dropna()]
        data.columns = [str(c).strip() for c in table.loc[header_row]]
        data.iloc[:, 0] = data.iloc[:, 0].ffill()               # merged cells: copy the value down
        # One line per row, "Column: value", so each row still makes sense on its own after chunking.
        lines = ["; ".join(f"{col}: {fmt(val)}" for col, val in row.items()) for _, row in data.iterrows()]
        text = "\n\n".join(([" ".join(notes)] if notes else []) + lines)
        excel_rows = f"{data.index.min() + 1}-{data.index.max() + 1}"   # pandas counts from 0, Excel from 1
        docs.append({"text": text, "metadata": {"sheet": sheet, "rows": excel_rows, "columns": list(data.columns)}})
    return docs, warnings


def fmt(value):
    """45.0 -> '45', 7.5 -> '7.5': numbers read like a person wrote them."""
    return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)


def load_email(path):
    msg = BytesParser(policy=policy.default).parsebytes(Path(path).read_bytes())
    body = msg.get_body(preferencelist=("plain", "html"))      # prefer the plain-text version
    text = body.get_content() if body else ""
    if body is not None and body.get_content_type() == "text/html":
        text = BeautifulSoup(text, "html.parser").get_text("\n")
    # Cut the quoted reply chain ("On ... wrote:" and lines starting with '>') and the signature ("-- ").
    text = re.split(r"\n(?:On .+ wrote:|-- ?)\n", "\n" + text, maxsplit=1)[0]
    text = "\n".join(line for line in text.splitlines() if not line.startswith(">"))
    meta = {"subject": msg["subject"], "from": msg["from"], "date": msg["date"], "message_id": msg["message-id"]}
    attachments = list(msg.iter_attachments())
    meta["attachments"] = [a.get_filename() for a in attachments]
    docs = [{"text": text, "metadata": meta}]
    for attachment in attachments:                              # small text attachments become their own document
        if attachment.get_content_type() in ("text/csv", "text/plain"):
            docs.append({"text": attachment.get_content(),
                         "metadata": {"attachment": attachment.get_filename(), "subject": msg["subject"]}})
    return docs, []


def load_html(path):
    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser")
    for junk in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        junk.decompose()                                        # remove the element and everything inside
    for banner in soup.select("[id*=cookie], [class*=cookie]"):
        banner.decompose()
    title = soup.title.get_text(strip=True) if soup.title else None
    main = soup.find("main") or soup.find("article") or soup.body
    docs = []
    for heading in main.find_all("h2"):                         # one document per section: question + answer
        parts = [" ".join(heading.get_text(" ").split())]     # .split() + join: any whitespace -> one space
        for sibling in heading.find_next_siblings():
            if sibling.name == "h2":
                break
            parts.append(" ".join(sibling.get_text(" ").split()))
        docs.append({"text": "\n".join(parts), "metadata": {"title": title, "section": parts[0]}})
    if not docs:                                                # no sections: keep the whole main text
        docs.append({"text": main.get_text("\n", strip=True), "metadata": {"title": title}})
    return docs, []


LOADERS = {".pdf": ("pdf", load_pdf), ".xlsx": ("excel", load_excel),
           ".eml": ("email", load_email), ".html": ("html", load_html), ".htm": ("html", load_html)}


# ---------- chunking ----------

def split_units(text, max_chars=MAX_CHARS):
    """Paragraphs, and sentences for paragraphs that are too long on their own."""
    units = []
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= max_chars:
            units.append(paragraph)
        else:
            units += [s for s in re.split(r"(?<=[.!?])\s+", paragraph) if s]
    return units


def chunk_text(text, max_chars=MAX_CHARS, overlap_chars=OVERLAP_CHARS):
    """Pack paragraphs into chunks of at most max_chars. A short last paragraph is repeated at the start of the next."""
    chunks, current = [], []
    for unit in split_units(text, max_chars):
        if current and len("\n".join(current + [unit])) > max_chars:
            chunks.append("\n".join(current))
            last = current[-1]
            current = [last] if len(last) <= overlap_chars and len(last) + len(unit) < max_chars else []
        current.append(unit[:max_chars])                        # a single giant sentence is cut, not lost
    if current:
        chunks.append("\n".join(current))
    return chunks


def ingest_file(path):
    """Load one file and return (chunks, warnings). Each chunk: id, text and metadata."""
    path = Path(path)
    kind, loader = LOADERS[path.suffix.lower()]
    docs, warnings = loader(path)
    fingerprint, chunks = file_fingerprint(path), []
    for doc in docs:
        for text in chunk_text(normalise(doc["text"])):
            index = len(chunks)
            chunk_id = f"{path.name}#{index}-{hashlib.sha1(text.encode()).hexdigest()[:8]}"
            chunks.append({"id": chunk_id, "text": text,
                           "metadata": {"source": path.name, "type": kind, "file_sha256": fingerprint,
                                        "chunk": index, "chars": len(text), **doc["metadata"]}})
    return chunks, warnings


def ingest_folder(folder):
    """Ingest every supported file in a folder. Identical chunk texts are kept once."""
    all_chunks, report, seen = [], [], set()
    for path in sorted(Path(folder).iterdir()):
        if path.suffix.lower() not in LOADERS:
            report.append((path.name, 0, ["skipped: unsupported file type"]))
            continue
        try:
            chunks, warnings = ingest_file(path)
        except Exception as error:                              # one broken file must not stop the whole run
            report.append((path.name, 0, [f"FAILED: {type(error).__name__}: {error}"]))
            continue
        fresh = [c for c in chunks if c["text"] not in seen]
        seen.update(c["text"] for c in fresh)
        all_chunks += fresh
        report.append((path.name, len(fresh), warnings))
    return all_chunks, report


def main():
    parser = argparse.ArgumentParser(description="Turn PDF, Excel, email and HTML files into clean chunks.")
    parser.add_argument("folder", help="folder with the files to ingest")
    parser.add_argument("--out", help="save all chunks to this .jsonl file")
    parser.add_argument("--show", type=int, default=0, help="print the first N chunks in full")
    args = parser.parse_args()
    if not Path(args.folder).is_dir():
        raise SystemExit(f"{args.folder} is not a folder. Did you run: python make_samples.py ?")

    chunks, report = ingest_folder(args.folder)
    print(f"{'file':<26}{'chunks':>7}  notes")
    for name, count, warnings in report:
        print(f"{name:<26}{count:>7}  {'; '.join(warnings)}")
    print(f"Total: {len(chunks)} chunks")
    for chunk in chunks[:args.show]:
        print("\n" + "-" * 70 + f"\n{chunk['id']}\n{json.dumps(chunk['metadata'], ensure_ascii=False)}\n\n{chunk['text']}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")   # JSON Lines: one object per line
        print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()
