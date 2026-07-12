from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from policybrief_g2c.collectors.html import HTMLCollector
from policybrief_g2c.collectors.rss import RSSCollector
from policybrief_g2c.config import (
    AppSettings,
    SourceConfig,
    load_category_config,
    load_source_configs,
)
from policybrief_g2c.models import NewsletterIssue, PolicyDocument, SourceType, make_content_hash
from policybrief_g2c.newsletter.renderer import NewsletterRenderer
from policybrief_g2c.processing.classifier import KeywordClassifier
from policybrief_g2c.processing.cleaner import CleaningError, clean_text
from policybrief_g2c.processing.deduplicator import Deduplicator
from policybrief_g2c.processing.ranker import ImportanceRanker
from policybrief_g2c.storage.repository import PolicyRepository
from policybrief_g2c.summarization.extractive import ExtractiveSummarizer
from policybrief_g2c.summarization.llm import LLMSummarizer


class PolicyPipeline:
    def __init__(
        self, settings: AppSettings | None = None, repository: PolicyRepository | None = None
    ) -> None:
        self.settings = settings or AppSettings()
        self.repository = repository or PolicyRepository(self.settings.database_path)
        self.repository.initialize()

    def collect(self) -> list[PolicyDocument]:
        configs = [
            source
            for source in load_source_configs(self.settings.source_config_path)
            if source.enabled
        ]
        documents: list[PolicyDocument] = []
        for source in configs:
            collector = (
                RSSCollector(source)
                if source.source_type == SourceType.RSS
                else HTMLCollector(source)
            )
            documents.extend(collector.collect())
        for document in documents:
            self.repository.save_document(document, status="collected")
        return documents

    def process(self, documents: list[PolicyDocument] | None = None) -> list[PolicyDocument]:
        documents = documents or self.repository.get_documents()
        processed: list[PolicyDocument] = []
        for document in documents:
            try:
                document.clean_text = clean_text(
                    document.raw_text, min_chars=self.settings.min_document_chars
                )
                document.content_hash = make_content_hash(document.clean_text)
                processed.append(document)
            except CleaningError:
                document.metadata["rejected_reason"] = "insufficient_content"
                self.repository.save_document(document, status="rejected")
        unique = (
            Deduplicator(self.settings.duplicate_threshold).deduplicate(processed).unique_documents
        )
        classifier = KeywordClassifier(load_category_config(self.settings.category_config_path))
        ranker = ImportanceRanker()
        for document in unique:
            classifier.apply(document)
            ranker.score(document)
            self.repository.save_document(document, status="processed")
        return unique

    def summarize(self, documents: list[PolicyDocument] | None = None) -> list[PolicyDocument]:
        documents = documents or self.repository.get_documents()
        summarizer = (
            LLMSummarizer(self.settings)
            if self.settings.summary_provider.lower() == "llm"
            else ExtractiveSummarizer()
        )
        for document in documents:
            document.apply_summary(summarizer.summarize(document))
            self.repository.save_document(document, status="summarized")
        return documents

    def build_newsletter(
        self, documents: list[PolicyDocument] | None = None
    ) -> tuple[NewsletterIssue, Path, Path]:
        now = datetime.now(UTC)
        start = now - timedelta(days=self.settings.lookback_days)
        documents = documents or self.repository.get_documents()
        selected = [
            document
            for document in documents
            if start <= document.published_at <= now and document.summary
        ]
        selected.sort(key=lambda item: item.importance_score, reverse=True)
        selected = selected[: self.settings.max_newsletter_items]
        issue = NewsletterIssue.create(
            title=f"정책한눈 주간 브리프 {now.date().isoformat()}",
            covered_start=start,
            covered_end=now,
            documents=selected,
        )
        renderer = NewsletterRenderer()
        renderer.render(issue)
        html_path, text_path = renderer.write(issue, self.settings.output_dir)
        self.repository.save_issue(issue)
        return issue, html_path, text_path

    def run(self, *, demo: bool = False) -> tuple[NewsletterIssue, Path, Path]:
        documents = self.load_demo_documents() if demo else self.collect()
        processed = self.process(documents)
        summarized = self.summarize(processed)
        return self.build_newsletter(summarized)

    def load_demo_documents(self) -> list[PolicyDocument]:
        fixture_dir = Path("tests/fixtures")
        rss_source = SourceConfig(
            name="demo_rss",
            agency="예시정책청",
            source_type=SourceType.RSS,
            base_url="https://demo.example.go.kr",
            feed_url="https://demo.example.go.kr/rss.xml",
            allowed_domains=["demo.example.go.kr"],
            enabled=True,
        )
        html_source = SourceConfig(
            name="demo_html",
            agency="예시복지부",
            source_type=SourceType.HTML,
            base_url="https://demo.example.go.kr",
            list_url="https://demo.example.go.kr/list.html",
            allowed_domains=["demo.example.go.kr"],
            title_selector="h1",
            content_selector="main",
            date_selector="time",
            enabled=True,
        )
        rss_docs = RSSCollector(rss_source).collect_from_text(
            (fixture_dir / "demo_feed.xml").read_text(encoding="utf-8"),
            "https://demo.example.go.kr/rss.xml",
        )
        html_doc = HTMLCollector(html_source).parse_article_file(
            fixture_dir / "demo_article.html",
            "https://demo.example.go.kr/policy/youth-housing.html",
        )
        return [*rss_docs, html_doc]
