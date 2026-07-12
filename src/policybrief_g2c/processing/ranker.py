from __future__ import annotations

import math
from datetime import UTC, datetime

from policybrief_g2c.models import PolicyDocument

NATIONWIDE_TERMS = ("전국", "국민", "전체", "모든", "전 지역")
DEADLINE_TERMS = ("마감", "기한", "까지", "신청")
IMPACT_TERMS = ("지원", "혜택", "감면", "보조", "대상", "신청", "개선")
LEGAL_TERMS = ("시행", "법", "규정", "고시", "의무", "제도")


class ImportanceRanker:
    def __init__(self, agency_priorities: dict[str, float] | None = None) -> None:
        self.agency_priorities = agency_priorities or {}

    def score(self, document: PolicyDocument, *, now: datetime | None = None) -> float:
        now = now or datetime.now(UTC)
        text = f"{document.title}\n{document.clean_text or document.raw_text}"
        age_days = max((now - document.published_at).days, 0)
        recency = max(0.0, 25.0 * math.exp(-age_days / 14))
        agency = min(self.agency_priorities.get(document.agency, 0.0), 10.0)
        nationwide = 15.0 if any(term in text for term in NATIONWIDE_TERMS) else 0.0
        deadline = 10.0 if any(term in text for term in DEADLINE_TERMS) else 0.0
        impact = min(sum(1 for term in IMPACT_TERMS if term in text) * 5.0, 20.0)
        legal = min(sum(1 for term in LEGAL_TERMS if term in text) * 3.0, 10.0)
        completeness = min(len(document.clean_text or document.raw_text) / 1500 * 10.0, 10.0)
        novelty = 10.0
        components = {
            "recency": recency,
            "agency_priority": agency,
            "nationwide_applicability": nationwide,
            "deadline_presence": deadline,
            "citizen_impact": impact,
            "legal_or_financial_effect": legal,
            "completeness": completeness,
            "novelty": novelty,
        }
        score = min(sum(components.values()), 100.0)
        document.importance_score = round(score, 2)
        document.metadata["importance_components"] = {k: round(v, 2) for k, v in components.items()}
        return document.importance_score
