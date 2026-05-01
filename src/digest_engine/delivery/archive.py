from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
from ..types import ReportData


@dataclass
class ArchiveResult:
    pdf_path: Path
    data_path: Path
    index_path: Path


def _serialize(data: ReportData) -> dict:
    return {
        "title": data.title,
        "subtitle": data.subtitle,
        "week_id": data.week_id,
        "executive_summary": data.executive_summary,
        "metrics": data.metrics,
        "days": data.days,
        "highlights": data.highlights,
        "next_steps": data.next_steps,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def archive_report(*, pdf_bytes: bytes, data: ReportData, reports_dir: Path) -> ArchiveResult:
    reports_dir = Path(reports_dir)
    week_dir = reports_dir / data.week_id
    week_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = week_dir / "relatorio.pdf"
    data_path = week_dir / "data.json"
    pdf_path.write_bytes(pdf_bytes)
    data_path.write_text(
        json.dumps(_serialize(data), ensure_ascii=False, indent=2),
        encoding="utf-8")

    index_path = reports_dir / "index.json"
    if index_path.exists():
        idx = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        idx = {"reports": []}
    entry = {
        "week_id": data.week_id,
        "title": data.title,
        "pdf": f"{data.week_id}/relatorio.pdf",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    idx["reports"] = [r for r in idx["reports"] if r["week_id"] != data.week_id]
    idx["reports"].append(entry)
    idx["reports"].sort(key=lambda r: r["week_id"])
    index_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")

    return ArchiveResult(pdf_path=pdf_path, data_path=data_path, index_path=index_path)
