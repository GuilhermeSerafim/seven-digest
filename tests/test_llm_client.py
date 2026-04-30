import json
from datetime import datetime, timezone
from digest_engine.types import Commit
from digest_engine.llm_client import (
    OpenAIClient, parse_classification_response, ClassificationRequest,
)


def _c(msg: str) -> Commit:
    return Commit(hash="h1", author="a", date=datetime.now(timezone.utc),
                  message=msg, files_changed=1, additions=1, deletions=0)


def test_parse_classification_response_maps_results_back_to_hashes():
    commits = [_c("feat: x"), _c("fix: y")]
    commits[0] = Commit(**{**commits[0].__dict__, "hash": "AAA"})
    commits[1] = Commit(**{**commits[1].__dict__, "hash": "BBB"})
    raw = json.dumps({
        "items": [
            {"hash": "AAA", "type": "feat", "business_value": "v1",
             "business_description": "d1", "complexity_estimate": "alta"},
            {"hash": "BBB", "type": "fix", "business_value": "v2",
             "business_description": "d2", "complexity_estimate": "baixa"},
        ]
    })
    out = parse_classification_response(raw, commits)
    assert len(out) == 2
    assert out[0].type == "feat" and out[0].business_value == "v1"
    assert out[1].complexity_estimate == "baixa"


def test_parse_classification_response_skips_unknown_hashes():
    commits = [Commit(hash="AAA", author="a",
                      date=datetime.now(timezone.utc),
                      message="feat: x", files_changed=1, additions=1, deletions=0)]
    raw = json.dumps({"items": [
        {"hash": "ZZZ", "type": "feat", "business_value": "v",
         "business_description": "d", "complexity_estimate": "média"},
    ]})
    assert parse_classification_response(raw, commits) == []


class _FakeOpenAI:
    """Minimal stand-in for openai.OpenAI."""
    def __init__(self, response_text: str):
        self.chat = type("C", (), {"completions": type("CC", (), {
            "create": lambda *a, **k: type("R", (), {
                "choices": [type("Ch", (), {
                    "message": type("M", (), {"content": response_text})()
                })()]
            })()
        })()})()


def test_openai_client_classify_uses_response():
    raw = json.dumps({"items": [{"hash": "h1", "type": "feat",
        "business_value": "v", "business_description": "d",
        "complexity_estimate": "alta"}]})
    fake = _FakeOpenAI(raw)
    client = OpenAIClient(model="gpt-4o", api_key="x", _client=fake)
    req = ClassificationRequest(commits=[_c("feat: x")], audience="aud")
    out = client.classify_batch(req)
    assert len(out) == 1
    assert out[0].business_value == "v"
