from datetime import datetime, timezone
from digest_engine.types import (
    Commit, ClassifiedCommit, RepoCommits, ReportData, BrandConfig
)


def test_commit_construction():
    c = Commit(
        hash="abc123",
        author="Guiler",
        date=datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
        message="feat: add lead qualification",
        files_changed=3,
        additions=120,
        deletions=4,
    )
    assert c.hash == "abc123"
    assert c.is_conventional() is True


def test_commit_non_conventional():
    c = Commit(hash="x", author="a", date=datetime.now(timezone.utc),
               message="fix typo", files_changed=1, additions=1, deletions=1)
    assert c.is_conventional() is False


def test_classified_commit_holds_translation():
    base = Commit(hash="x", author="a", date=datetime.now(timezone.utc),
                  message="feat: x", files_changed=1, additions=1, deletions=0)
    cc = ClassifiedCommit(
        commit=base, type="feat", business_value="onboarding mais rápido",
        business_description="Reduz fricção no cadastro inicial",
        complexity_estimate="média",
    )
    assert cc.type == "feat"


def test_report_data_round_trip():
    rd = ReportData(
        title="Test", subtitle="sub", week_id="2026-W17",
        executive_summary="resumo",
        metrics={"backend": {"commits": 5}}, days=[], highlights=[], next_steps=[],
    )
    assert rd.week_id == "2026-W17"


def test_brand_config_defaults_match_seven():
    b = BrandConfig(primary_color="#1e3a5f", light_color="#e8eef5", logo_path=None)
    assert b.primary_color == "#1e3a5f"
