import os
from datetime import datetime, timezone
import pytest
from digest_engine.types import Commit
from digest_engine.llm_client import OpenAIClient, ClassificationRequest, SummaryRequest


pytestmark = pytest.mark.skipif(
    "OPENAI_API_KEY" not in os.environ,
    reason="needs OPENAI_API_KEY (smoke job only)")


def _c(msg: str, h: str = "abc") -> Commit:
    return Commit(hash=h, author="t",
                  date=datetime.now(timezone.utc),
                  message=msg, files_changed=1, additions=10, deletions=2)


def test_openai_classifies_real_commit():
    client = OpenAIClient(model="gpt-4o", api_key=os.environ["OPENAI_API_KEY"])
    out = client.classify_batch(ClassificationRequest(
        commits=[_c("feat: add lead qualification scoring", h="HSMOKE1")],
        audience="sócios não-técnicos da SEVEN, em pt-BR"))
    assert len(out) == 1
    assert out[0].business_value
    assert out[0].business_description
    assert out[0].complexity_estimate in {"baixa", "média", "alta"}


def test_openai_synthesizes_real_summary():
    client = OpenAIClient(model="gpt-4o", api_key=os.environ["OPENAI_API_KEY"])
    from digest_engine.types import ClassifiedCommit
    cc = ClassifiedCommit(
        commit=_c("feat: add lead qual"), type="feat",
        business_value="onboarding mais rápido",
        business_description="Reduz fricção no cadastro inicial",
        complexity_estimate="alta")
    out = client.synthesize_summary(SummaryRequest(
        classified=[cc], audience="sócios não-técnicos da SEVEN"))
    assert isinstance(out, str) and len(out) > 20
