from pathlib import Path

from typer.testing import CliRunner

from policybrief_g2c.cli import app
from policybrief_g2c.config import AppSettings
from policybrief_g2c.pipeline import PolicyPipeline
from policybrief_g2c.storage.repository import PolicyRepository


def test_demo_pipeline_idempotent(tmp_path: Path) -> None:
    settings = AppSettings(
        database_path=tmp_path / "demo.db",
        output_dir=tmp_path / "newsletters",
        category_config_path=Path("config/categories.yaml"),
    )
    pipeline = PolicyPipeline(settings, PolicyRepository(settings.database_path))
    first_issue, first_html, _ = pipeline.run(demo=True)
    second_issue, second_html, _ = pipeline.run(demo=True)
    assert first_html.exists()
    assert second_html.exists()
    assert first_issue.id == second_issue.id
    assert len(pipeline.repository.get_documents()) == 3


def test_repository_issue_roundtrip_and_stats(tmp_path: Path) -> None:
    settings = AppSettings(
        database_path=tmp_path / "demo.db",
        output_dir=tmp_path / "newsletters",
        category_config_path=Path("config/categories.yaml"),
    )
    pipeline = PolicyPipeline(settings, PolicyRepository(settings.database_path))
    issue, _, _ = pipeline.run(demo=True)
    loaded = pipeline.repository.get_issue(issue.id)
    stats = pipeline.repository.stats()
    assert loaded is not None
    assert loaded.id == issue.id
    assert stats["documents"] == 3
    assert stats["newsletter_issues"] == 1


def test_cli_run_demo_and_stats(tmp_path: Path) -> None:
    runner = CliRunner()
    env = {
        "DATABASE_PATH": str(tmp_path / "cli.db"),
        "OUTPUT_DIR": str(tmp_path / "newsletters"),
        "CATEGORY_CONFIG_PATH": "config/categories.yaml",
        "SOURCE_CONFIG_PATH": "config/sources.example.yaml",
    }
    run_result = runner.invoke(app, ["run", "--demo"], env=env)
    assert run_result.exit_code == 0
    assert "Generated newsletter HTML" in run_result.output

    stats_result = runner.invoke(app, ["show-stats"], env=env)
    assert stats_result.exit_code == 0
    assert "documents" in stats_result.output

    config_result = runner.invoke(app, ["validate-config"], env=env)
    assert config_result.exit_code == 0
    assert "Configuration OK" in config_result.output


def test_cli_dry_run_send_requires_issue_id() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["send"])
    assert result.exit_code != 0
