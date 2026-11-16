"""Locate a Day 6 evidence quote verbatim inside a chunk.

Day 6 matched quotes after NFC + whitespace collapse + lower-casing, so quotes may
differ from chunk text by line breaks / case. The Day 7 starter `hit()` uses an
exact substring test. `find_verbatim` maps the normalized match back to the exact
span of the original chunk text, so the Day 7 gold evidence is a literal substring.
"""
import unicodedata


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Return (normalized text, index map normalized position -> original position)."""
    text = unicodedata.normalize("NFC", text)
    out, pos_map, in_space = [], [], False
    for i, ch in enumerate(text):
        if ch.isspace():
            if not in_space and out:
                out.append(" ")
                pos_map.append(i)
            in_space = True
            continue
        in_space = False
        low = ch.lower()
        if len(low) != 1:  # keep 1:1 mapping for rare multi-char lowercase forms
            low = ch
        out.append(low)
        pos_map.append(i)
    if out and out[-1] == " ":
        out.pop()
        pos_map.pop()
    return "".join(out), pos_map


def normalize(text: str) -> str:
    return _normalize_with_map(text)[0]


def find_verbatim(quote: str, chunk_text: str) -> str | None:
    """Exact substring of `chunk_text` that equals `quote` after normalization, else None."""
    target = normalize(quote)
    if not target:
        return None
    norm_text, pos_map = _normalize_with_map(chunk_text)
    start = norm_text.find(target)
    if start < 0:
        return None
    end = start + len(target) - 1
    original = unicodedata.normalize("NFC", chunk_text)
    return original[pos_map[start]:pos_map[end] + 1]