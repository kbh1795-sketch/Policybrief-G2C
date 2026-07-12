from __future__ import annotations

from rapidfuzz import fuzz

from policybrief_g2c.models import PolicyDocument, normalize_for_hash


class DeduplicationResult:
    def __init__(self, unique_documents: list[PolicyDocument], duplicate_count: int) -> None:
        self.unique_documents = unique_documents
        self.duplicate_count = duplicate_count


class Deduplicator:
    def __init__(self, near_duplicate_threshold: int = 88) -> None:
        self.near_duplicate_threshold = near_duplicate_threshold

    def deduplicate(self, documents: list[PolicyDocument]) -> DeduplicationResult:
        unique: list[PolicyDocument] = []
        duplicate_count = 0
        for candidate in documents:
            match = self._find_duplicate(candidate, unique)
            if match is None:
                unique.append(candidate)
                continue
            duplicate_count += 1
            keeper = self._choose_keeper(match, candidate)
            duplicate = candidate if keeper is match else match
            keeper.metadata.setdefault("duplicate_source_urls", [])
            if duplicate.source_url not in keeper.metadata["duplicate_source_urls"]:
                keeper.metadata["duplicate_source_urls"].append(duplicate.source_url)
            if keeper is candidate:
                unique[unique.index(match)] = candidate
        return DeduplicationResult(unique, duplicate_count)

    def _find_duplicate(
        self, candidate: PolicyDocument, unique: list[PolicyDocument]
    ) -> PolicyDocument | None:
        for existing in unique:
            if candidate.canonical_url == existing.canonical_url:
                return existing
            if candidate.content_hash and candidate.content_hash == existing.content_hash:
                return existing
            title_score = fuzz.token_set_ratio(
                normalize_for_hash(candidate.title), normalize_for_hash(existing.title)
            )
            text_score = fuzz.token_set_ratio(
                normalize_for_hash(candidate.clean_text or candidate.raw_text),
                normalize_for_hash(existing.clean_text or existing.raw_text),
            )
            if (
                title_score >= self.near_duplicate_threshold
                and text_score >= self.near_duplicate_threshold
            ):
                return existing
        return None

    @staticmethod
    def _choose_keeper(left: PolicyDocument, right: PolicyDocument) -> PolicyDocument:
        left_len = len(left.clean_text or left.raw_text)
        right_len = len(right.clean_text or right.raw_text)
        if right_len > left_len * 1.1:
            return right
        if right.published_at > left.published_at:
            return right
        return left
