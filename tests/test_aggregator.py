from datetime import datetime, timezone
from digest_engine.types import Commit, ClassifiedCommit
from digest_engine.aggregator import aggregate_report_data


def _cc(msg: str, type_: str, complexity: str = "média", day: int = 20) -> ClassifiedCommit:
    return ClassifiedCommit(
        commit=Commit(hash=msg, author="a",
                      date=datetime(2026, 4, day, 12, tzinfo=timezone.utc),
                      message=msg, files_changed=1, additions=1, deletions=0),
        type=type_, business_value="v", business_description=f"desc {msg}",
        complexity_estimate=complexity)


def test_aggregate_counts_metrics_by_type():
    data = aggregate_report_data(
        week_id="2026-W17",
        classified_by_repo={
            "backend": [_cc("a", "feat"), _cc("b", "fix"), _cc("c", "feat")],
            "frontend": [_cc("d", "docs")],
        },
        executive_summary="s", project_name="P", week_label="L",
        next_steps=[],
    )
    assert data.metrics["backend"]["Commits"] == 3
    assert data.metrics["backend"]["Features novas"] == 2
    assert data.metrics["backend"]["Bug fixes"] == 1
    assert data.metrics["frontend"]["Docs / Specs"] == 1


def test_aggregate_groups_days_chronologically():
    data = aggregate_report_data(
        week_id="2026-W17",
        classified_by_repo={
            "backend": [_cc("a", "feat", day=21), _cc("b", "fix", day=20)],
        },
        executive_summary="s", project_name="P", week_label="L",
        next_steps=[],
    )
    assert data.days[0]["date_label"].startswith("20/04")
    assert data.days[1]["date_label"].startswith("21/04")


def test_aggregate_highlights_only_high_complexity():
    data = aggregate_report_data(
        week_id="2026-W17",
        classified_by_repo={
            "backend": [_cc("a", "feat", "alta"), _cc("b", "fix", "baixa")],
        },
        executive_summary="s", project_name="P", week_label="L",
        next_steps=[],
    )
    assert len(data.highlights) == 1
