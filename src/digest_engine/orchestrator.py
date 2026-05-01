from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable
import json
from .config import Config, RepoConfig
from .iso_week import parse_iso_week
from .types import RepoCommits, BrandConfig
from .classifier import classify_all, synthesize_executive_summary
from .aggregator import aggregate_report_data
from .renderers.pdf import render as render_pdf
from .delivery.archive import archive_report, git_commit_and_push
from .delivery.whatsapp import WhatsAppDeliverer
from .llm_client import LLMClient


CollectFn = Callable[[RepoConfig, datetime, datetime], RepoCommits]


@dataclass
class RunContext:
    config: Config
    week_id: str
    reports_dir: Path
    cache_dir: Path
    collect_fn: CollectFn
    llm: LLMClient
    whatsapp: WhatsAppDeliverer | None
    report_url: str
    dry_run: bool = False


@dataclass
class RunResult:
    success: bool
    week_id: str
    pdf_path: Path | None = None
    delivery_results: list = field(default_factory=list)
    error: str = ""


def _log(event: str, **fields) -> None:
    print(json.dumps({"event": event, **fields}, ensure_ascii=False), flush=True)


def _week_label_pt(start: datetime, end: datetime) -> str:
    months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    return f"{start.day:02d} de {months[start.month-1]} – {end.day:02d} de {months[end.month-1]} de {end.year}"


def run_pipeline(ctx: RunContext) -> RunResult:
    try:
        start, end = parse_iso_week(ctx.week_id)
        _log("pipeline.start", week=ctx.week_id, start=start.isoformat(), end=end.isoformat())

        collected: list[RepoCommits] = []
        for repo in ctx.config.repos:
            rc = ctx.collect_fn(repo, start, end)
            _log("collect.done", repo=repo.name, commits=len(rc.commits))
            collected.append(rc)

        classified = classify_all(
            collected, llm=ctx.llm,
            audience=ctx.config.classification.audience,
            cache_dir=ctx.cache_dir)
        _log("classify.done",
             total=sum(len(v) for v in classified.values()))

        summary = synthesize_executive_summary(
            classified, llm=ctx.llm,
            audience=ctx.config.classification.audience)

        data = aggregate_report_data(
            week_id=ctx.week_id, classified_by_repo=classified,
            executive_summary=summary,
            project_name=ctx.config.project.name,
            week_label=_week_label_pt(start, end),
            next_steps=[])

        brand_yaml = ctx.config.project.brand
        brand = BrandConfig(
            primary_color=brand_yaml.primary_color,
            light_color=brand_yaml.light_color,
            logo_path=brand_yaml.logo_path)
        pdf_bytes = render_pdf(data, brand)
        _log("render.done", bytes=len(pdf_bytes))

        archive = archive_report(
            pdf_bytes=pdf_bytes, data=data, reports_dir=ctx.reports_dir)
        _log("archive.done", pdf=str(archive.pdf_path))

        if ctx.config.delivery.archive.commit_to_repo and not ctx.dry_run:
            git_commit_and_push(
                reports_dir=ctx.reports_dir, week_id=ctx.week_id, push=True)
            _log("git.pushed", week=ctx.week_id)

        delivery_results: list = []
        if ctx.whatsapp is not None and not ctx.dry_run:
            bullet = data.highlights[0] if data.highlights else summary[:120]
            delivery_results = ctx.whatsapp.send_to_all(
                week_label=ctx.week_id,
                summary_bullet=bullet,
                report_url=ctx.report_url)
            _log("whatsapp.done",
                 ok=sum(1 for r in delivery_results if r.success),
                 fail=sum(1 for r in delivery_results if not r.success))

        return RunResult(success=True, week_id=ctx.week_id,
                         pdf_path=archive.pdf_path,
                         delivery_results=delivery_results)
    except Exception as e:
        _log("pipeline.error", error=str(e), error_type=type(e).__name__)
        return RunResult(success=False, week_id=ctx.week_id, error=str(e))
