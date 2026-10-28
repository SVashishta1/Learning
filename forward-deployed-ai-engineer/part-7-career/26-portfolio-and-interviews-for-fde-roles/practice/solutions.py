"""Reference solutions for practice/problems.md. Try first, then compare."""
import re
import time


# ---------------------------------------------------------------- 1. merge contacts (union-find)
def norm_email(e: str | None) -> str:
    return (e or "").strip().lower()


def norm_phone(p: str | None) -> str:
    p = (p or "").replace("(0)", "")                     # "+31 (0)6..." -> "+31 6..." (trunk prefix)
    digits = re.sub(r"\D", "", p)
    return ("+" if p.strip().startswith("+") else "") + digits if digits else ""


def merge_contacts(rows: list[dict]) -> list[dict]:
    parent = list(range(len(rows)))

    def find(i):                                         # follow parents to the group's root
        while parent[i] != i:
            parent[i] = parent[parent[i]]                # path halving keeps chains short
            i = parent[i]
        return i

    seen: dict[str, int] = {}
    for i, r in enumerate(rows):
        for key in (("e:" + norm_email(r.get("email"))) if norm_email(r.get("email")) else None,
                    ("p:" + norm_phone(r.get("phone"))) if norm_phone(r.get("phone")) else None):
            if key is None:
                continue
            if key in seen:
                a, b = find(seen[key]), find(i)
                parent[max(a, b)] = min(a, b)            # the earlier row stays the root: keeps order
            else:
                seen[key] = i
    groups: dict[int, list[dict]] = {}
    for i, r in enumerate(rows):
        groups.setdefault(find(i), []).append(r)
    out = []
    for root in sorted(groups):
        g = groups[root]
        names = [" ".join((r.get("name") or "").split()) for r in g]
        out.append({"name": max(names, key=len),
                    "email": next((norm_email(r.get("email")) for r in g if norm_email(r.get("email"))), ""),
                    "phone": next((norm_phone(r.get("phone")) for r in g if norm_phone(r.get("phone"))), ""),
                    "sources": len(g)})
    return out


# ---------------------------------------------------------------- 2. paginate with retries
class TemporaryError(Exception):
    """A failure worth retrying (HTTP 429/503, a timeout)."""


def fetch_all(get_page, max_retries: int = 3, sleep=time.sleep) -> list:
    items, cursor, seen = [], None, set()
    while True:
        for attempt in range(max_retries + 1):
            try:
                page = get_page(cursor)
                break
            except TemporaryError:
                if attempt == max_retries:
                    raise
                sleep(2 ** attempt)                     # 1, 2, 4 ... seconds
        items.extend(page["items"])
        cursor = page.get("next")
        if cursor is None:
            return items
        if cursor in seen:
            raise ValueError(f"API returned cursor {cursor!r} twice: stopping to avoid an endless loop")
        seen.add(cursor)


# ---------------------------------------------------------------- 3. chunk for RAG
def chunk(text: str, max_words: int = 120, overlap: int = 20) -> list[str]:
    if overlap >= max_words:
        raise ValueError("overlap must be smaller than max_words")
    pieces = []
    for para in [p.split() for p in re.split(r"\n\s*\n", text) if p.strip()]:
        while len(para) > max_words:                     # a giant paragraph: cut it by words
            pieces.append(para[:max_words])
            para = para[max_words:]
        pieces.append(para)
    chunks, current = [], []
    for words in pieces:
        if current and len(current) + len(words) > max_words:
            chunks.append(current)
            current = current[-overlap:] if overlap else []
            if len(current) + len(words) > max_words:    # overlap + piece too long: shorten the overlap
                current = current[len(current) + len(words) - max_words:]
        current = current + words
    if current:
        chunks.append(current)
    return [" ".join(c) for c in chunks]
