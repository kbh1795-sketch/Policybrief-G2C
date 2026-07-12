from datetime import UTC, datetime

import httpx
import respx

from policybrief_g2c.config import AppSettings
from policybrief_g2c.models import PolicyDocument, SourceType
from policybrief_g2c.summarization.extractive import ExtractiveSummarizer
from policybrief_g2c.summarization.llm import LLMSummarizer


def _doc() -> PolicyDocument:
    text = "\n".join(
        [
            "정부는 전국 소상공인의 에너지 비용 부담을 줄이기 위해 비용 일부를 지원합니다.",
            "지원 대상은 사업자등록을 한 소상공인입니다.",
            "신청은 2026년 7월 20일부터 온라인 누리집에서 접수합니다.",
            "신청 마감은 2026년 8월 31일까지입니다.",
        ]
    )
    doc = PolicyDocument.from_source(
        title="전국 소상공인 에너지 비용 지원 신청 안내",
        agency="예시정책청",
        source_name="demo",
        source_type=SourceType.FILE,
        source_url="https://demo.example.go.kr/a",
        canonical_url="https://demo.example.go.kr/a",
        published_at=datetime(2026, 7, 10, tzinfo=UTC),
        raw_text=text,
    )
    doc.clean_text = text
    return doc


def test_extractive_summary_fields() -> None:
    summary = ExtractiveSummarizer().summarize(_doc())
    assert len(summary.key_points) == 3
    assert "소상공인" in summary.eligibility
    assert "2026년 8월 31일" in summary.deadline


def test_llm_fallback_when_disabled() -> None:
    summary = LLMSummarizer(AppSettings(llm_enabled=False)).summarize(_doc())
    assert "소상공인" in summary.overview


def test_llm_success_with_mocked_response() -> None:
    settings = AppSettings(
        llm_enabled=True,
        llm_api_key="test-key",
        llm_base_url="https://llm.example.test/v1",
        llm_model="test-model",
    )
    response_body = {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"overview":"요약","key_points":["하나","둘","셋"],'
                        '"citizen_impact":"영향","eligibility":"대상",'
                        '"application_method":"신청","effective_date":"시행",'
                        '"deadline":"마감","source_url":"https://demo.example.go.kr/a"}'
                    )
                }
            }
        ]
    }
    with respx.mock:
        respx.post("https://llm.example.test/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=response_body)
        )
        summary = LLMSummarizer(settings).summarize(_doc())
    assert summary.overview == "요약"
    assert summary.key_points == ["하나", "둘", "셋"]
