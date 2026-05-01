import json
from pathlib import Path
from digest_engine.delivery.archive import archive_report
from digest_engine.types import ReportData


def _data(week: str = "2026-W17") -> ReportData:
    return ReportData(
        title="t", subtitle="s", week_id=week, executive_summary="e",
        metrics={"backend": {"Commits": 1}}, days=[], highlights=[], next_steps=[],
    )


def test_archive_writes_pdf_and_data_json(tmp_path: Path):
    pdf = b"%PDF-1.4 fake"
    result = archive_report(
        pdf_bytes=pdf, data=_data(), reports_dir=tmp_path,
    )
    week_dir = tmp_path / "2026-W17"
    assert (week_dir / "relatorio.pdf").read_bytes() == pdf
    raw = json.loads((week_dir / "data.json").read_text(encoding="utf-8"))
    assert raw["week_id"] == "2026-W17"
    assert result.pdf_path == week_dir / "relatorio.pdf"


def test_archive_creates_index_when_missing(tmp_path: Path):
    archive_report(pdf_bytes=b"%PDF-1.4", data=_data(), reports_dir=tmp_path)
    idx = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert idx["reports"][0]["week_id"] == "2026-W17"


def test_archive_appends_to_existing_index(tmp_path: Path):
    (tmp_path / "index.json").write_text(json.dumps({
        "reports": [{"week_id": "2026-W16", "pdf": "2026-W16/relatorio.pdf"}]
    }))
    archive_report(pdf_bytes=b"%PDF-1.4", data=_data(), reports_dir=tmp_path)
    idx = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert len(idx["reports"]) == 2
    assert idx["reports"][-1]["week_id"] == "2026-W17"


def test_archive_replaces_existing_entry_for_same_week(tmp_path: Path):
    archive_report(pdf_bytes=b"%PDF-1.4 v1", data=_data(), reports_dir=tmp_path)
    archive_report(pdf_bytes=b"%PDF-1.4 v2", data=_data(), reports_dir=tmp_path)
    idx = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert len([r for r in idx["reports"] if r["week_id"] == "2026-W17"]) == 1
    assert (tmp_path / "2026-W17" / "relatorio.pdf").read_bytes() == b"%PDF-1.4 v2"
