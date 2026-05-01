from collections import Counter
from datetime import datetime
from .types import ClassifiedCommit, ReportData


_TYPE_BUCKETS = {
    "feat": "Features novas",
    "fix": "Bug fixes",
    "docs": "Docs / Specs",
    "ci": "CI / Infra",
    "infra": "CI / Infra",
    "chore": "CI / Infra",
}


def _date_label_pt(d: datetime) -> str:
    weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    return f"{d.strftime('%d/%m')} — {weekdays[d.weekday()]}"


def aggregate_report_data(
    *, week_id: str, classified_by_repo: dict[str, list[ClassifiedCommit]],
    executive_summary: str, project_name: str, week_label: str,
    next_steps: list[str],
) -> ReportData:
    metrics: dict[str, dict[str, int]] = {}
    for repo, items in classified_by_repo.items():
        counter = Counter()
        counter["Commits"] = len(items)
        for cc in items:
            label = _TYPE_BUCKETS.get(cc.type)
            if label:
                counter[label] += 1
        metrics[repo] = dict(counter)

    days_map: dict[str, list[str]] = {}
    flat: list[ClassifiedCommit] = []
    for items in classified_by_repo.values():
        flat.extend(items)
    flat.sort(key=lambda c: c.commit.date)
    for cc in flat:
        key = _date_label_pt(cc.commit.date)
        bullet = cc.business_description or cc.commit.message
        days_map.setdefault(key, []).append(bullet)
    days = [{"date_label": k, "items": v} for k, v in days_map.items()]

    highlights = [
        f"{cc.business_value}: {cc.business_description}".strip(": ").strip()
        for cc in flat if cc.complexity_estimate == "alta"
    ]

    return ReportData(
        title=f"{project_name} — Relatório Semanal",
        subtitle=week_label,
        week_id=week_id,
        executive_summary=executive_summary,
        metrics=metrics,
        days=days,
        highlights=highlights,
        next_steps=next_steps,
    )
