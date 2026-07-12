from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from policybrief_g2c.models import NewsletterIssue


class NewsletterRenderer:
    def __init__(self, template_dir: Path | None = None) -> None:
        self.template_dir = template_dir or Path(__file__).with_name("templates")
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, issue: NewsletterIssue) -> NewsletterIssue:
        grouped: dict[str, list[object]] = defaultdict(list)
        for document in issue.documents:
            grouped[document.policy_category].append(document)
        context = {"issue": issue, "grouped_documents": dict(grouped)}
        issue.generated_html = self.env.get_template("newsletter.html.j2").render(**context)
        issue.generated_text = self.env.get_template("newsletter.txt.j2").render(**context)
        return issue

    def write(self, issue: NewsletterIssue, output_dir: Path) -> tuple[Path, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        html_path = output_dir / f"{issue.id}.html"
        text_path = output_dir / f"{issue.id}.txt"
        html_path.write_text(issue.generated_html, encoding="utf-8")
        text_path.write_text(issue.generated_text, encoding="utf-8")
        return html_path, text_path
