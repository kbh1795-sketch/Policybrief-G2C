from pathlib import Path

import pytest

from policybrief_g2c.collectors.base import CollectionError, validate_allowed_url
from policybrief_g2c.collectors.html import HTMLCollector
from policybrief_g2c.collectors.rss import RSSCollector
from policybrief_g2c.config import SourceConfig
from policybrief_g2c.models import SourceType

FIXTURES = Path(__file__).with_name("fixtures")


def test_rss_parsing() -> None:
    source = SourceConfig(
        name="demo",
        agency="예시정책청",
        source_type=SourceType.RSS,
        base_url="https://demo.example.go.kr",
        feed_url="https://demo.example.go.kr/rss.xml",
        allowed_domains=["demo.example.go.kr"],
    )
    docs = RSSCollector(source).collect_from_text(
        (FIXTURES / "demo_feed.xml").read_text(encoding="utf-8"),
        "https://demo.example.go.kr/rss.xml",
    )
    assert len(docs) == 2
    assert docs[0].title.startswith("전국 소상공인")


def test_html_parsing() -> None:
    source = SourceConfig(
        name="demo",
        agency="예시복지부",
        source_type=SourceType.HTML,
        base_url="https://demo.example.go.kr",
        list_url="https://demo.example.go.kr/list.html",
        allowed_domains=["demo.example.go.kr"],
        title_selector="h1",
        content_selector="main",
        date_selector="time",
    )
    doc = HTMLCollector(source).parse_article_file(
        FIXTURES / "demo_article.html",
        "https://demo.example.go.kr/policy/youth-housing.html",
    )
    assert doc.title == "청년 전세보증금 반환보증료 지원 확대"
    assert "무주택 청년" in doc.raw_text


def test_html_extract_article_links() -> None:
    source = SourceConfig(
        name="demo",
        agency="예시복지부",
        source_type=SourceType.HTML,
        base_url="https://demo.example.go.kr",
        list_url="https://demo.example.go.kr/list.html",
        allowed_domains=["demo.example.go.kr"],
        article_link_selector="a.policy-link",
    )
    html = """
    <html><body>
      <a class="policy-link" href="/policy/a.html">A</a>
      <a class="policy-link" href="https://demo.example.go.kr/policy/b.html">B</a>
      <a href="https://demo.example.go.kr/ignored.html">ignored</a>
    </body></html>
    """
    links = HTMLCollector(source).extract_article_links(
        html, "https://demo.example.go.kr/list.html"
    )
    assert links == [
        "https://demo.example.go.kr/policy/a.html",
        "https://demo.example.go.kr/policy/b.html",
    ]


def test_url_allowlist_validation() -> None:
    validate_allowed_url("https://demo.example.go.kr/a", ["example.go.kr"])
    with pytest.raises(CollectionError):
        validate_allowed_url("https://evil.test/a", ["example.go.kr"])
