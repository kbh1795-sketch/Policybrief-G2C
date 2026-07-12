from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup


class CleaningError(ValueError):
    """Raised when a document lacks enough meaningful text."""


BOILERPLATE_PATTERNS = [
    re.compile(r"^\s*(목록|이전글|다음글|첨부파일|담당부서|저작권|공유하기)\s*$"),
    re.compile(r"^\s*\d+\s*/\s*\d+\s*$"),
]


def clean_text(raw_text: str, *, min_chars: int = 80) -> str:
    text = raw_text
    if "<" in raw_text and ">" in raw_text:
        soup = BeautifulSoup(raw_text, "lxml")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        text = soup.get_text("\n", strip=True)

    text = unicodedata.normalize("NFKC", text)
    lines = []
    for line in text.splitlines():
        stripped = re.sub(r"\s+", " ", line).strip()
        if not stripped:
            continue
        if any(pattern.match(stripped) for pattern in BOILERPLATE_PATTERNS):
            continue
        lines.append(stripped)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
    if len(re.sub(r"\s+", "", cleaned)) < min_chars:
        msg = "document has insufficient meaningful content"
        raise CleaningError(msg)
    return cleaned
