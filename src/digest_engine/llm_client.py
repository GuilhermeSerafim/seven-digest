from dataclasses import dataclass
from typing import Protocol
import json
from .types import Commit, ClassifiedCommit


@dataclass
class ClassificationRequest:
    commits: list[Commit]
    audience: str
    prompt_override: str | None = None


@dataclass
class SummaryRequest:
    classified: list[ClassifiedCommit]
    audience: str


class LLMClient(Protocol):
    def classify_batch(self, req: ClassificationRequest) -> list[ClassifiedCommit]: ...
    def synthesize_summary(self, req: SummaryRequest) -> str: ...


_SYSTEM_CLASSIFY = """Você é um tradutor técnico→negócio.
Para cada commit, gere JSON com:
- hash (cópia exata do input)
- type (feat|fix|docs|chore|refactor|test|ci|infra|perf|other)
- business_value (frase curta sobre impacto comercial, em pt-BR)
- business_description (1-2 frases para {audience})
- complexity_estimate (baixa|média|alta)

Responda APENAS JSON: {{"items": [...]}}"""


_SYSTEM_SUMMARY = """Você sintetiza relatórios semanais para {audience}.
Dado um conjunto de entregas classificadas, escreva 1 parágrafo de 3-5 frases
em pt-BR destacando os progressos mais importantes da semana, em linguagem
de negócio. Sem jargão técnico. Sem listas."""


def _build_classify_user_prompt(commits: list[Commit]) -> str:
    items = [
        {"hash": c.hash, "message": c.message,
         "files_changed": c.files_changed,
         "additions": c.additions, "deletions": c.deletions}
        for c in commits
    ]
    return json.dumps({"commits": items}, ensure_ascii=False)


def parse_classification_response(raw: str, commits: list[Commit]) -> list[ClassifiedCommit]:
    by_hash = {c.hash: c for c in commits}
    data = json.loads(raw)
    out: list[ClassifiedCommit] = []
    for item in data.get("items", []):
        h = item.get("hash")
        if h not in by_hash:
            continue
        out.append(ClassifiedCommit(
            commit=by_hash[h],
            type=item.get("type", "other"),
            business_value=item.get("business_value", ""),
            business_description=item.get("business_description", ""),
            complexity_estimate=item.get("complexity_estimate", "média"),
        ))
    return out


class OpenAIClient:
    def __init__(self, model: str, api_key: str, _client=None):
        if _client is None:
            from openai import OpenAI
            _client = OpenAI(api_key=api_key)
        self._client = _client
        self.model = model

    def classify_batch(self, req: ClassificationRequest) -> list[ClassifiedCommit]:
        system = (req.prompt_override or _SYSTEM_CLASSIFY).format(audience=req.audience)
        user = _build_classify_user_prompt(req.commits)
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = resp.choices[0].message.content
        return parse_classification_response(content, req.commits)

    def synthesize_summary(self, req: SummaryRequest) -> str:
        system = _SYSTEM_SUMMARY.format(audience=req.audience)
        bullets = [
            f"- [{c.type}] {c.business_description}" for c in req.classified if c.business_description
        ]
        user = "Entregas da semana:\n" + "\n".join(bullets) if bullets else "Sem entregas relevantes."
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
