from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from policybrief_g2c.models import NewsletterIssue, PolicyDocument


class PolicyRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.session() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    canonical_url TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'collected',
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS duplicate_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keeper_id TEXT NOT NULL,
                    duplicate_url TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(keeper_id, duplicate_url)
                );
                CREATE TABLE IF NOT EXISTS newsletter_issues (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS send_history (
                    issue_id TEXT PRIMARY KEY,
                    recipient_count INTEGER NOT NULL,
                    sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def save_document(self, document: PolicyDocument, status: str = "processed") -> None:
        with self.session() as connection:
            connection.execute(
                """
                INSERT INTO documents(id, canonical_url, content_hash, status, payload)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    canonical_url=excluded.canonical_url,
                    content_hash=excluded.content_hash,
                    status=excluded.status,
                    payload=excluded.payload,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    document.id,
                    document.canonical_url,
                    document.content_hash,
                    status,
                    document.model_dump_json(),
                ),
            )
            for duplicate_url in document.metadata.get("duplicate_source_urls", []):
                connection.execute(
                    """
                    INSERT OR IGNORE INTO duplicate_relationships(keeper_id, duplicate_url)
                    VALUES (?, ?)
                    """,
                    (document.id, duplicate_url),
                )

    def get_documents(self) -> list[PolicyDocument]:
        with self.session() as connection:
            rows = connection.execute("SELECT payload FROM documents ORDER BY id").fetchall()
        return [PolicyDocument.model_validate_json(str(row["payload"])) for row in rows]

    def save_issue(self, issue: NewsletterIssue) -> None:
        with self.session() as connection:
            connection.execute(
                """
                INSERT INTO newsletter_issues(id, payload, status)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload=excluded.payload,
                    status=excluded.status,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (issue.id, issue.model_dump_json(), issue.status.value),
            )

    def get_issue(self, issue_id: str) -> NewsletterIssue | None:
        with self.session() as connection:
            row = connection.execute(
                "SELECT payload FROM newsletter_issues WHERE id = ?", (issue_id,)
            ).fetchone()
        return NewsletterIssue.model_validate_json(str(row["payload"])) if row else None

    def stats(self) -> dict[str, Any]:
        with self.session() as connection:
            documents = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            duplicates = connection.execute(
                "SELECT COUNT(*) FROM duplicate_relationships"
            ).fetchone()[0]
            issues = connection.execute("SELECT COUNT(*) FROM newsletter_issues").fetchone()[0]
        return {"documents": documents, "duplicates": duplicates, "newsletter_issues": issues}
