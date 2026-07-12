from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from time import sleep
from typing import cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from policybrief_g2c.collectors.base import BaseCollector, CollectionError, validate_allowed_url
from policybrief_g2c.models import PolicyDocument, SourceType


class HTMLCollector(BaseCollector):
    def collect(self) -> list[PolicyDocument]:
        if not self.source.list_url:
            msg = "HTML source requires list_url"
            raise CollectionError(msg)
        html = self.fetch_text(self.source.list_url)
        links = self.extract_article_links(html, self.source.list_url)
        documents: list[PolicyDocument] = []
        for link in links[: self.source.max_items_per_run]:
            sleep(self.source.request_delay_seconds)
            article_html = self.fetch_text(link)
            documents.append(self.parse_article(article_html, link))
        return documents

    def extract_article_links(self, html: str, list_url: str) -> list[str]:
        selector = self.source.article_link_selector
        if not selector:
            msg = "HTML source requires article_link_selector"
            raise CollectionError(msg)
        soup = BeautifulSoup(html, "lxml")
        links: list[str] = []
        for element in soup.select(selector):
            href = element.get("href")
            if not href:
                continue
            url = urljoin(list_url, str(href))
            validate_allowed_url(url, self.source.allowed_domains)
            if url not in links:
                links.append(url)
        return links

    def parse_article(self, html: str, url: str) -> PolicyDocument:
        validate_allowed_url(url, self.source.allowed_domains)
        soup = BeautifulSoup(html, "lxml")
        title = _first_text(soup, self.source.title_selector) or "제목 없음"
        content_selector = self.source.content_selector or "body"
        content = soup.select_one(content_selector)
        raw_text = (
            content.get_text("\n", strip=True) if content else soup.get_text("\n", strip=True)
        )
        date_text = _first_text(soup, self.source.date_selector)
        published = _parse_date(date_text)
        return PolicyDocument.from_source(
            title=title,
            agency=self.source.agency,
            source_name=self.source.name,
            source_type=SourceType.HTML,
            source_url=url,
            canonical_url=url,
            published_at=published,
            raw_text=raw_text,
            metadata={"selector": content_selector},
        )

    def parse_article_file(self, path: Path, canonical_url: str) -> PolicyDocument:
        return self.parse_article(path.read_text(encoding="utf-8"), canonical_url)


def _first_text(soup: BeautifulSoup, selector: str | None) -> str | None:
    if not selector:
        return None
    element = soup.select_one(selector)
    return element.get_text(" ", strip=True) if element else None


def _parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    parsed = date_parser.parse(value)
    parsed_datetime = cast(datetime, parsed)
    return parsed_datetime if parsed_datetime.tzinfo else parsed_datetime.replace(tzinfo=UTC)
