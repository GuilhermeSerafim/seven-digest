import httpx
import pytest
from digest_engine.delivery.whatsapp import (
    WhatsAppDeliverer, RecipientResult, build_template_payload,
)
from digest_engine.config import Recipient, WhatsAppConfig


def test_build_template_payload_uses_three_params():
    payload = build_template_payload(
        phone="+5511999",
        template_name="seven_relatorio_semanal",
        params=["W17 (21-27/abr)", "Lead qualification publicada", "https://x.com/r.pdf"],
    )
    assert payload["to"] == "+5511999"
    assert payload["template"]["name"] == "seven_relatorio_semanal"
    components = payload["template"]["components"][0]["parameters"]
    assert [p["text"] for p in components] == \
        ["W17 (21-27/abr)", "Lead qualification publicada", "https://x.com/r.pdf"]


def test_send_to_all_returns_one_result_per_recipient(monkeypatch):
    recipients = [Recipient(name="A", phone="+551"), Recipient(name="B", phone="+552")]
    cfg = WhatsAppConfig(provider="meta_cloud_api", phone_number_id="PID",
                         template_name="tpl", recipients=recipients)
    seen: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(req.url.path)
        return httpx.Response(200, json={"messages": [{"id": "wamid_xxx"}]})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="https://graph.facebook.com")
    d = WhatsAppDeliverer(config=cfg, access_token="TOK", _http=client)
    results = d.send_to_all(week_label="W17", summary_bullet="x", report_url="https://r/x.pdf")
    assert len(results) == 2
    assert all(r.success for r in results)
    assert all("/v19.0/PID/messages" in p for p in seen)


def test_send_to_all_records_failures_per_recipient():
    recipients = [Recipient(name="A", phone="+551"), Recipient(name="B", phone="+552")]
    cfg = WhatsAppConfig(provider="meta_cloud_api", phone_number_id="PID",
                         template_name="tpl", recipients=recipients)
    calls = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json={"messages": [{"id": "wamid"}]})
        return httpx.Response(400, json={"error": {"message": "boom"}})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="https://graph.facebook.com")
    d = WhatsAppDeliverer(config=cfg, access_token="TOK", _http=client)
    results = d.send_to_all(week_label="W17", summary_bullet="x", report_url="https://r/x.pdf")
    assert results[0].success and not results[1].success
    assert "boom" in results[1].error
