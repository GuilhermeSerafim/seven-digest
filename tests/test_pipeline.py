import subprocess
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
from digest_engine.config import (
    Config, ProjectConfig, BrandConfigYaml, RepoConfig,
    ClassificationConfig, ScreenshotsConfig, DeliveryConfig,
    WhatsAppConfig, ArchiveConfig,
)
from digest_engine.orchestrator import RunContext, run_pipeline
from digest_engine.git_collector import collect_commits
from digest_engine.types import ClassifiedCommit


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


def _make_repo(path: Path, messages: list[str]) -> None:
    path.mkdir(parents=True)
    _git(path, "init", "-b", "main")
    _git(path, "config", "user.email", "t@t.com")
    _git(path, "config", "user.name", "T")
    for i, msg in enumerate(messages):
        (path / f"f{i}.txt").write_text(str(i))
        _git(path, "add", ".")
        _git(path, "commit", "-m", msg)


class _FakeLLM:
    def classify_batch(self, req):
        return [
            ClassifiedCommit(
                commit=c,
                type=c.conventional_type() or "other",
                business_value=f"valor {c.message[:20]}",
                business_description=f"impacto: {c.message}",
                complexity_estimate="alta" if "feat" in c.message else "média",
            ) for c in req.commits
        ]

    def synthesize_summary(self, req):
        return "Semana com entregas de feat e fix."


def test_full_pipeline_produces_pdf_and_index(tmp_path: Path):
    repo = tmp_path / "repos" / "backend"
    _make_repo(repo, ["feat: A", "fix: B", "chore: noise"])

    cfg = Config(
        project=ProjectConfig(name="SEVEN Tools", brand=BrandConfigYaml(
            primary_color="#1e3a5f", light_color="#e8eef5", logo_path=None)),
        repos=[RepoConfig(name="backend", path=str(repo), branch="main",
                          ignore_patterns=[])],
        classification=ClassificationConfig(llm_provider="openai", model="gpt-4o",
            audience="sócios SEVEN", prompt_overrides=None),
        screenshots=ScreenshotsConfig(enabled=False),
        delivery=DeliveryConfig(
            whatsapp=WhatsAppConfig(provider="meta_cloud_api",
                phone_number_id="PID", template_name="tpl", recipients=[]),
            archive=ArchiveConfig(path="reports", commit_to_repo=False)),
    )

    from digest_engine.iso_week import current_iso_week
    week_id = current_iso_week()

    ctx = RunContext(
        config=cfg, week_id=week_id,
        reports_dir=tmp_path / "reports", cache_dir=tmp_path / "cache",
        collect_fn=collect_commits, llm=_FakeLLM(),
        whatsapp=None, report_url="https://x/r.pdf", dry_run=False,
    )
    result = run_pipeline(ctx)
    assert result.success is True
    pdf_path = tmp_path / "reports" / week_id / "relatorio.pdf"
    assert pdf_path.exists()

    reader = PdfReader(pdf_path.open("rb"))
    text = "\n".join(p.extract_text() or "" for p in reader.pages)
    assert "SEVEN Tools" in text
    assert "Resumo Executivo" in text
    assert "Semana com entregas" in text
    assert "valor" in text or "impacto" in text
