from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from policybrief_g2c.models import SourceType


class PaginationConfig(BaseModel):
    max_pages: int = 1
    page_param: str = "page"


class SourceConfig(BaseModel):
    name: str
    agency: str
    source_type: SourceType
    base_url: str
    feed_url: str | None = None
    list_url: str | None = None
    allowed_domains: list[str]
    article_link_selector: str | None = None
    title_selector: str | None = None
    content_selector: str | None = None
    date_selector: str | None = None
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
    enabled: bool = False
    request_delay_seconds: float = 1.0
    user_agent: str = "PolicyBrief-G2C/0.1"
    max_items_per_run: int = 20
    note: str | None = None

    @field_validator("allowed_domains")
    @classmethod
    def domains_required(cls, value: list[str]) -> list[str]:
        if not value:
            msg = "allowed_domains must contain at least one domain"
            raise ValueError(msg)
        return [domain.lower() for domain in value]


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    log_level: str = "INFO"
    database_path: Path = Path("data/policybrief.db")
    source_config_path: Path = Path("config/sources.example.yaml")
    category_config_path: Path = Path("config/categories.yaml")
    output_dir: Path = Path("data/newsletters")
    lookback_days: int = 7
    max_newsletter_items: int = 10
    duplicate_threshold: int = 88
    summary_provider: str = "extractive"
    min_document_chars: int = 80

    llm_enabled: bool = False
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    email_send_enabled: bool = False
    email_recipients: str = ""
    email_recipients_file: Path = Path("subscribers.txt")
    email_batch_size: int = 20


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        msg = f"YAML root must be a mapping: {path}"
        raise ValueError(msg)
    return data


def load_source_configs(path: Path) -> list[SourceConfig]:
    data = load_yaml(path)
    sources = data.get("sources", [])
    if not isinstance(sources, list):
        msg = "sources must be a list"
        raise ValueError(msg)
    return [SourceConfig.model_validate(source) for source in sources]


def load_category_config(path: Path) -> dict[str, dict[str, int]]:
    data = load_yaml(path)
    categories = data.get("categories", {})
    if not isinstance(categories, dict):
        msg = "categories must be a mapping"
        raise ValueError(msg)

    parsed: dict[str, dict[str, int]] = {}
    for category, body in categories.items():
        keywords = body.get("keywords", {}) if isinstance(body, dict) else {}
        parsed[str(category)] = {str(word): int(weight) for word, weight in keywords.items()}
    return parsed
