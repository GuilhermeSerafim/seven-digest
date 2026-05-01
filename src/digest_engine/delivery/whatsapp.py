from dataclasses import dataclass
import httpx
from ..config import WhatsAppConfig


@dataclass
class RecipientResult:
    name: str
    phone: str
    success: bool
    wamid: str | None = None
    error: str = ""


def build_template_payload(*, phone: str, template_name: str, params: list[str]) -> dict:
    return {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "pt_BR"},
            "components": [{
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in params],
            }],
        },
    }


class WhatsAppDeliverer:
    def __init__(self, *, config: WhatsAppConfig, access_token: str, _http: httpx.Client | None = None):
        self.config = config
        self._http = _http or httpx.Client(base_url="https://graph.facebook.com",
                                           timeout=httpx.Timeout(30.0))
        self._headers = {"Authorization": f"Bearer {access_token}",
                         "Content-Type": "application/json"}

    def send_to_all(self, *, week_label: str, summary_bullet: str, report_url: str) -> list[RecipientResult]:
        results: list[RecipientResult] = []
        path = f"/v19.0/{self.config.phone_number_id}/messages"
        for r in self.config.recipients:
            payload = build_template_payload(
                phone=r.phone,
                template_name=self.config.template_name,
                params=[week_label, summary_bullet, report_url],
            )
            try:
                resp = self._http.post(path, json=payload, headers=self._headers)
                if resp.status_code >= 400:
                    err = resp.json().get("error", {}).get("message", resp.text)
                    results.append(RecipientResult(name=r.name, phone=r.phone,
                                                   success=False, error=err))
                else:
                    wamid = resp.json().get("messages", [{}])[0].get("id")
                    results.append(RecipientResult(name=r.name, phone=r.phone,
                                                   success=True, wamid=wamid))
            except httpx.HTTPError as e:
                results.append(RecipientResult(name=r.name, phone=r.phone,
                                               success=False, error=str(e)))
        return results
