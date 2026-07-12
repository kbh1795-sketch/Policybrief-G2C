from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceType(StrEnum):
    RSS = "RSS"
    HTML = "HTML"
    API = "API"
    FILE = "FILE"


class NewsletterStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    SENT = "sent"


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_for_hash(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value


def make_content_hash(text: str) -> str:
    return hashlib.sha256(normalize_for_hash(text).encode("utf-8")).hexdigest()


def make_document_id(canonical_url: str, published_at: datetime | None, title: str) -> str:
    date_part = published_at.date().isoformat() if published_at else "unknown-date"
    raw = f"{normalize_for_hash(canonical_url)}|{date_part}|{normalize_for_hash(title)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


class SummaryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overview: str
    key_points: list[str] = Field(default_factory=list, min_length=1, max_length=5)
    citizen_impact: str = "원문에서 확인되지 않음"
    eligibility: str = "원문에서 확인되지 않음"
    application_method: str = "원문에서 확인되지 않음"
    effective_date: str = "원문에서 확인되지 않음"
    deadline: str = "원문에서 확인되지 않음"
    source_url: str


class PolicyDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    agency: str
    source_name: str
    source_type: SourceType
    source_url: str
    canonical_url: str
    published_at: datetime
    collected_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime | None = None
    raw_text: str
    clean_text: str = ""
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    citizen_impact: str = ""
    eligibility: str = ""
    application_method: str = ""
    effective_date: str = ""
    deadline: str = ""
    policy_category: str = "기타"
    keywords: list[str] = Field(default_factory=list)
    importance_score: float = 0.0
    content_hash: str = ""
    language: str = "ko"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("published_at", "collected_at", "updated_at")
    @classmethod
    def ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    @field_validator("content_hash")
    @classmethod
    def fill_hash(cls, value: str, info: Any) -> str:
        if value:
            return value
        text = info.data.get("clean_text") or info.data.get("raw_text") or ""
        return make_content_hash(str(text))

    @classmethod
    def from_source(
        cls,
        *,
        title: str,
        agency: str,
        source_name: str,
        source_type: SourceType,
        source_url: str,
        canonical_url: str,
        published_at: datetime,
        raw_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyDocument:
        doc_id = make_document_id(canonical_url, published_at, title)
        return cls(
            id=doc_id,
            title=title.strip(),
            agency=agency.strip(),
            source_name=source_name.strip(),
            source_type=source_type,
            source_url=source_url,
            canonical_url=canonical_url,
            published_at=published_at,
            raw_text=raw_text,
            content_hash=make_content_hash(raw_text),
            metadata=metadata or {},
        )

    def apply_summary(self, summary: SummaryResult) -> None:
        self.summary = summary.overview
        self.key_points = summary.key_points[:3]
        self.citizen_impact = summary.citizen_impact
        self.eligibility = summary.eligibility
        self.application_method = summary.application_method
        self.effective_date = summary.effective_date
        self.deadline = summary.deadline


class NewsletterIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    id: str
    title: str
    publication_date: datetime
    covered_start: datetime
    covered_end: datetime
    documents: list[PolicyDocument]
    generated_html: str = ""
    generated_text: str = ""
    status: NewsletterStatus = NewsletterStatus.DRAFT
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        title: str,
        covered_start: datetime,
        covered_end: datetime,
        documents: list[PolicyDocument],
    ) -> NewsletterIssue:
        issue_key = f"{title}|{covered_start.date()}|{covered_end.date()}"
        issue_id = hashlib.sha256(issue_key.encode("utf-8")).hexdigest()[:16]
        return cls(
            id=issue_id,
            title=title,
            publication_date=utc_now(),
            covered_start=covered_start,
            covered_end=covered_end,
            documents=documents,
        )
