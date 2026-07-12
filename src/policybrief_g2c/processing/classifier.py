from __future__ import annotations

from dataclasses import dataclass

from policybrief_g2c.models import PolicyDocument


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    scores: dict[str, float]
    matched_keywords: list[str]


class KeywordClassifier:
    def __init__(self, categories: dict[str, dict[str, int]], fallback: str = "기타") -> None:
        self.categories = categories
        self.fallback = fallback

    def classify(self, document: PolicyDocument) -> ClassificationResult:
        haystack = f"{document.title}\n{document.clean_text or document.raw_text}".lower()
        scores: dict[str, float] = {}
        matches: dict[str, list[str]] = {}
        for category, keywords in self.categories.items():
            score = 0.0
            matched: list[str] = []
            for keyword, weight in keywords.items():
                if keyword.lower() in haystack:
                    score += float(weight)
                    matched.append(keyword)
            scores[category] = score
            matches[category] = matched

        best_category = (
            max(scores, key=lambda category: scores[category]) if scores else self.fallback
        )
        if scores.get(best_category, 0.0) <= 0:
            best_category = self.fallback
        return ClassificationResult(best_category, scores, matches.get(best_category, []))

    def apply(self, document: PolicyDocument) -> PolicyDocument:
        result = self.classify(document)
        document.policy_category = result.category
        document.keywords = result.matched_keywords
        document.metadata["classification_scores"] = result.scores
        return document
