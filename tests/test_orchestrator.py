from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock
from digest_engine.orchestrator import run_pipeline, RunContext
from digest_engine.config import Config, ProjectConfig, BrandConfigYaml, RepoConfig, \
    ClassificationConfig, ScreenshotsConfig, DeliveryConfig, WhatsAppConfig, ArchiveConfig, Recipient
from digest_engine.types import RepoCommits, Commit, ClassifiedCommit


def _build_cfg(repos_dir: Path, reports_dir: Path) -> Config:
    return Config(
        project=ProjectConfig(name="P", brand=BrandConfigYaml(
            primary_color="#1e3a5f", light_color="#e8eef5", logo_path=None)),
        repos=[RepoConfig(name="r1", path=str(repos_dir / "r1"), branch="main",
                          ignore_patterns=[])],
        classification=ClassificationConfig(llm_provider="openai", model="gpt-4o",
            audience="aud", prompt_overrides=None),
        screenshots=ScreenshotsConfig(enabled=False),
        delivery=DeliveryConfig(
            whatsapp=WhatsAppConfig(provider="meta_cloud_api",
                phone_number_id="PID", template_name="tpl", recipients=[]),
            archive=ArchiveConfig(path=str(reports_dir), commit_to_repo=False)),
    )


def test_run_pipeline_calls_components_in_order(tmp_path: Path):
    cfg = _build_cfg(repos_dir=tmp_path, reports_dir=tmp_path / "reports")

    fake_collect = MagicMock(return_value=RepoCommits(repo_name="r1", commits=[
        Commit(hash="H", author="a",
               date=datetime(2026, 4, 20, 12, tzinfo=timezone.utc),
               message="feat: x", files_changed=1, additions=1, deletions=0)
    ]))
    fake_llm = MagicMock()
    fake_llm.classify_batch.return_value = [
        ClassifiedCommit(commit=fake_collect.return_value.commits[0], type="feat",
                         business_value="bv", business_description="bd",
                         complexity_estimate="alta")
    ]
    fake_llm.synthesize_summary.return_value = "exec summary"
    fake_whatsapp = MagicMock()
    fake_whatsapp.send_to_all.return_value = []

    ctx = RunContext(
        config=cfg, week_id="2026-W17", reports_dir=tmp_path / "reports",
        cache_dir=tmp_path / "cache",
        collect_fn=fake_collect, llm=fake_llm, whatsapp=fake_whatsapp,
        report_url="https://x/r.pdf", dry_run=False,
    )
    result = run_pipeline(ctx)
    assert result.success is True
    assert (tmp_path / "reports" / "2026-W17" / "relatorio.pdf").exists()
    fake_llm.classify_batch.assert_called_once()
    fake_llm.synthesize_summary.assert_called_once()
    fake_whatsapp.send_to_all.assert_called_once()


def test_run_pipeline_dry_run_skips_whatsapp(tmp_path: Path):
    cfg = _build_cfg(repos_dir=tmp_path, reports_dir=tmp_path / "reports")
    fake_collect = MagicMock(return_value=RepoCommits(repo_name="r1", commits=[]))
    fake_llm = MagicMock()
    fake_llm.synthesize_summary.return_value = "—"
    fake_whatsapp = MagicMock()

    ctx = RunContext(
        config=cfg, week_id="2026-W17", reports_dir=tmp_path / "reports",
        cache_dir=tmp_path / "cache",
        collect_fn=fake_collect, llm=fake_llm, whatsapp=fake_whatsapp,
        report_url="x", dry_run=True,
    )
    result = run_pipeline(ctx)
    assert result.success is True
    fake_whatsapp.send_to_all.assert_not_called()
