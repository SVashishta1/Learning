"""Build the search index from the protocols/ folder (run it again whenever a protocol changes).

Run:  python ingest.py
Makes: data/clinic.db
"""
import sys

from clinic_rag import DB, EMBED_MODEL, PROTOCOLS, OllamaError, build_index, chunk

print(f"📄 Reading protocols from {PROTOCOLS}")
for path in sorted(PROTOCOLS.glob("*.md")):
    print(f"   {path.name}: {len(chunk(path.read_text(encoding='utf-8')))} chunks")
try:
    count = build_index()
except OllamaError as error:
    sys.exit(f"❌ {error}")
print(f"✅ Embedded {count} chunks with {EMBED_MODEL} into {DB}")
