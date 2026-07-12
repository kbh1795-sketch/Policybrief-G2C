from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

import feedparser
from dateutil import parser as date_parser

from policybrief_g2c.collectors.base import BaseCollector, CollectionError, validate_allowed_url
from policybrief_g2c.models import PolicyDocument, SourceType


class RSSCollector(BaseCollector):
    def collect(self) -> list[PolicyDocument]:
        if not self.source.feed_url:
            msg = "RSS source requires feed_url"
            raise CollectionError(msg)
        text = self.fetch_text(self.source.feed_url)
        return self.collect_from_text(text, self.source.feed_url)

    def collect_from_text(self, feed_text: str, feed_url: str) -> list[PolicyDocument]:
        validate_allowed_url(feed_url, self.source.allowed_domains)
        parsed = feedparser.parse(feed_text)
        documents: list[PolicyDocument] = []
        for entry in parsed.entries[: self.source.max_items_per_run]:
            link = str(entry.get("link") or feed_url)
            if link.startswith("http"):
                validate_allowed_url(link, self.source.allowed_domains)
            title = str(entry.get("title") or "제목 없음")
            raw_text = " ".join(
                str(part)
                for part in [
                    entry.get("summary", ""),
                    entry.get("description", ""),
                    entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "",
                ]
                if part
            )
            published = _parse_entry_date(entry)
            documents.append(
                PolicyDocument.from_source(
                    title=title,
                    agency=self.source.agency,
                    source_name=self.source.name,
                    source_type=SourceType.RSS,
                    source_url=feed_url,
                    canonical_url=link,
                    published_at=published,
                    raw_text=raw_text or title,
                    metadata={"feed_id": entry.get("id", "")},
                )
            )
        return documents


def _parse_entry_date(entry: object) -> datetime:
    for key in ("published", "updated", "created"):
        value = getattr(entry, key, None) or entry.get(key) if hasattr(entry, "get") else None
        if value:
            parsed = date_parser.parse(str(value))
            parsed_datetime = cast(datetime, parsed)
            return (
                parsed_datetime if parsed_datetime.tzinfo else parsed_datetime.replace(tzinfo=UTC)
            )
    return datetime.now(UTC)
