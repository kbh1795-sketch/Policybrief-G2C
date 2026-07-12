from __future__ import annotations

import re

from policybrief_g2c.models import PolicyDocument, SummaryResult
from policybrief_g2c.summarization.base import Summarizer

UNKNOWN = "원문에서 확인되지 않음"


class ExtractiveSummarizer(Summarizer):
    def summarize(self, document: PolicyDocument) -> SummaryResult:
        sentences = _sentences(document.clean_text or document.raw_text)
        overview = sentences[0] if sentences else f"{document.title}에 관한 공식 발표입니다."
        key_points = _top_points(sentences, document.title)
        text = document.clean_text or document.raw_text
        return SummaryResult(
            overview=overview,
            key_points=key_points,
            citizen_impact=_find_line(text, ("지원", "혜택", "부담", "개선", "영향")) or UNKNOWN,
            eligibility=_find_line(text, ("대상", "자격", "청년", "가구", "소상공인", "국민"))
            or UNKNOWN,
            application_method=_find_line(text, ("신청", "접수", "온라인", "방문", "누리집"))
            or UNKNOWN,
            effective_date=_find_date_line(text, ("시행", "부터", "적용")) or UNKNOWN,
            deadline=_find_date_line(text, ("마감", "까지", "기한")) or UNKNOWN,
            source_url=document.canonical_url,
        )


def _sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    parts = re.findall(r"[^.!?。]+(?:다\.|[.!?。]|$)", compact)
    return [part.strip() for part in parts if len(part.strip()) >= 15]


def _top_points(sentences: list[str], title: str) -> list[str]:
    keywords = [word for word in re.split(r"\W+", title) if len(word) >= 2]
    ranked = sorted(
        sentences,
        key=lambda sentence: (
            sum(1 for word in keywords if word in sentence),
            any(term in sentence for term in ("지원", "대상", "신청", "시행", "마감")),
            len(sentence),
        ),
        reverse=True,
    )
    points = ranked[:3] or sentences[:3]
    while len(points) < 3:
        points.append("세부 내용은 원문에서 확인이 필요합니다.")
    return points[:3]


def _find_line(text: str, terms: tuple[str, ...]) -> str | None:
    for line in text.splitlines():
        if any(term in line for term in terms) and len(line.strip()) >= 10:
            return line.strip()
    for sentence in _sentences(text):
        if any(term in sentence for term in terms):
            return sentence
    return None


def _find_date_line(text: str, terms: tuple[str, ...]) -> str | None:
    date_pattern = re.compile(r"(\d{4}[년.-]\s*\d{1,2}[월.-]\s*\d{1,2}일?|\d{1,2}월\s*\d{1,2}일)")
    for line in text.splitlines():
        if any(term in line for term in terms) and date_pattern.search(line):
            return line.strip()
    return None
