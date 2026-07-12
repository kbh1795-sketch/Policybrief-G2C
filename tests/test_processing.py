from datetime import UTC, datetime

from policybrief_g2c.models import PolicyDocument, SourceType, make_document_id
from policybrief_g2c.processing.classifier import KeywordClassifier
from policybrief_g2c.processing.cleaner import clean_text
from policybrief_g2c.processing.deduplicator import Deduplicator
from policybrief_g2c.processing.ranker import ImportanceRanker


def _doc(title: str, text: str, url: str = "https://demo.example.go.kr/a") -> PolicyDocument:
    return PolicyDocument.from_source(
        title=title,
        agency="예시정책청",
        source_name="demo",
        source_type=SourceType.FILE,
        source_url=url,
        canonical_url=url,
        published_at=datetime(2026, 7, 10, tzinfo=UTC),
        raw_text=text,
    )


def test_clean_text_and_hash_id() -> None:
    cleaned = clean_text(
        "<main><p>전국 국민에게 지원하는 정책입니다.</p>"
        "<p>신청은 온라인에서 가능합니다. 자세한 기준과 절차를 안내합니다.</p></main>",
        min_chars=20,
    )
    assert "온라인" in cleaned
    assert make_document_id(
        "https://a.test", datetime(2026, 1, 1, tzinfo=UTC), "제목"
    ) == make_document_id("https://a.test", datetime(2026, 1, 1, tzinfo=UTC), "제목")


def test_deduplicator_exact_and_near() -> None:
    text = "전국 소상공인 에너지 비용 지원 신청 안내입니다. 신청 대상과 마감 기한을 설명합니다."
    first = _doc("전국 소상공인 에너지 비용 지원", text, "https://demo.example.go.kr/a")
    second = _doc(
        "전국 소상공인 에너지 비용 지원 안내",
        text + " 추가 안내입니다.",
        "https://demo.example.go.kr/b",
    )
    first.clean_text = text
    second.clean_text = text + " 추가 안내입니다."
    result = Deduplicator(near_duplicate_threshold=80).deduplicate([first, second])
    assert len(result.unique_documents) == 1
    assert result.duplicate_count == 1


def test_classifier_and_ranker() -> None:
    doc = _doc(
        "청년 전세보증금 지원", "청년 주거 안정을 위해 전국 무주택 청년에게 신청 지원을 제공합니다."
    )
    classifier = KeywordClassifier({"주거·부동산": {"전세": 3, "주거": 3}, "기타": {}})
    classifier.apply(doc)
    score = ImportanceRanker().score(doc, now=datetime(2026, 7, 11, tzinfo=UTC))
    assert doc.policy_category == "주거·부동산"
    assert score > 40
    assert "importance_components" in doc.metadata
