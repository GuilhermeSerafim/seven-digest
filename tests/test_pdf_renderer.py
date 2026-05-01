from io import BytesIO
from datetime import datetime, timezone
import pytest
from pypdf import PdfReader
from digest_engine.types import (
    Commit, ClassifiedCommit, ReportData, BrandConfig
)
from digest_engine.renderers.pdf import render


def _sample_report() -> ReportData:
    return ReportData(
        title="SEVEN Tools — Relatório Semanal",
        subtitle="20 de Abril – 26 de Abril de 2026",
        week_id="2026-W17",
        executive_summary="Semana focada em qualificação de leads e CI.",
        metrics={
            "backend": {"Commits": 12, "Features novas": 3, "Bug fixes": 2},
            "frontend": {"Commits": 18, "Features novas": 5, "Bug fixes": 4},
        },
        days=[
            {"date_label": "20/04 — Segunda",
             "items": ["Lead Qualification API publicada", "Auth fixes"]},
            {"date_label": "21/04 — Terça",
             "items": ["UI de qualificação"]},
        ],
        highlights=["Lead Qualification end-to-end concluído"],
        next_steps=["Sales Copilot Caloni Fase 2"],
    )


def test_render_produces_valid_pdf_bytes():
    brand = BrandConfig(primary_color="#1e3a5f", light_color="#e8eef5", logo_path=None)
    data = _sample_report()
    out = render(data, brand)
    assert isinstance(out, bytes)
    assert out.startswith(b"%PDF-")
    reader = PdfReader(BytesIO(out))
    assert len(reader.pages) >= 1


def test_render_contains_expected_sections():
    brand = BrandConfig(primary_color="#1e3a5f", light_color="#e8eef5", logo_path=None)
    data = _sample_report()
    out = render(data, brand)
    reader = PdfReader(BytesIO(out))
    text = "\n".join(p.extract_text() or "" for p in reader.pages)
    assert "Resumo Executivo" in text
    assert "Detalhamento por Dia" in text
    assert "Destaques" in text
    assert "Próximos Passos" in text
    assert "20/04 — Segunda" in text


def test_render_handles_empty_sections():
    brand = BrandConfig(primary_color="#1e3a5f", light_color="#e8eef5", logo_path=None)
    data = ReportData(
        title="Empty", subtitle="-", week_id="2026-W17",
        executive_summary="Nada a destacar.",
        metrics={"backend": {"Commits": 0}}, days=[], highlights=[], next_steps=[],
    )
    out = render(data, brand)
    assert out.startswith(b"%PDF-")
