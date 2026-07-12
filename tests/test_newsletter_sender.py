from datetime import UTC, datetime

from policybrief_g2c.config import AppSettings
from policybrief_g2c.models import NewsletterIssue, PolicyDocument, SourceType
from policybrief_g2c.newsletter.renderer import NewsletterRenderer
from policybrief_g2c.newsletter.sender import EmailSender, EmailSendError


def _issue() -> NewsletterIssue:
    doc = PolicyDocument.from_source(
        title="<b>청년 지원</b>",
        agency="예시복지부",
        source_name="demo",
        source_type=SourceType.FILE,
        source_url="https://demo.example.go.kr/a",
        canonical_url="https://demo.example.go.kr/a",
        published_at=datetime(2026, 7, 10, tzinfo=UTC),
        raw_text="청년 대상 정책입니다. 신청은 온라인에서 가능합니다. 전국 대상 지원입니다.",
    )
    doc.clean_text = doc.raw_text
    doc.summary = "청년 대상 정책입니다."
    doc.key_points = ["신청은 온라인에서 가능합니다.", "전국 대상 지원입니다.", "원문 확인 필요"]
    return NewsletterIssue.create(
        title="테스트",
        covered_start=datetime(2026, 7, 1, tzinfo=UTC),
        covered_end=datetime(2026, 7, 11, tzinfo=UTC),
        documents=[doc],
    )


def test_renderer_escapes_html() -> None:
    issue = NewsletterRenderer().render(_issue())
    assert "&lt;b&gt;청년 지원&lt;/b&gt;" in issue.generated_html
    assert "<b>청년 지원</b>" not in issue.generated_html


def test_email_disabled_by_default() -> None:
    sender = EmailSender(AppSettings(email_recipients="person@example.com"))
    result = sender.send(_issue(), dry_run=True)
    assert result["recipient_count"] == 1
    try:
        sender.send(_issue(), dry_run=False, confirm_send=False)
    except EmailSendError as exc:
        assert "EMAIL_SEND_ENABLED" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("send should be blocked")
