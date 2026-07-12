from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from policybrief_g2c.config import SourceConfig
from policybrief_g2c.models import PolicyDocument


class CollectionError(RuntimeError):
    """Raised when a source cannot be collected."""


def validate_allowed_url(url: str, allowed_domains: Iterable[str]) -> None:
    host = (urlparse(url).hostname or "").lower()
    allowed = {domain.lower() for domain in allowed_domains}
    if host not in allowed and not any(host.endswith(f".{domain}") for domain in allowed):
        msg = f"URL host is not allowlisted: {host}"
        raise CollectionError(msg)


class BaseCollector(ABC):
    def __init__(self, source: SourceConfig, timeout_seconds: float = 15.0) -> None:
        self.source = source
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def collect(self) -> list[PolicyDocument]:
        """Collect documents from the configured source."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    def fetch_text(self, url: str) -> str:
        validate_allowed_url(url, self.source.allowed_domains)
        headers = {"User-Agent": self.source.user_agent}
        with httpx.Client(
            timeout=self.timeout_seconds, follow_redirects=True, headers=headers
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
