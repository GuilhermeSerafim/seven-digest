from datetime import datetime, timezone
from digest_engine.types import Commit
from digest_engine.classifier import preclassify_conventional


def _c(msg: str) -> Commit:
    return Commit(hash="x", author="a", date=datetime.now(timezone.utc),
                  message=msg, files_changed=1, additions=1, deletions=0)


def test_preclassify_extracts_feat():
    cc = preclassify_conventional(_c("feat: add login"))
    assert cc is not None
    assert cc.type == "feat"
    assert cc.commit.message == "feat: add login"


def test_preclassify_extracts_fix_with_scope():
    cc = preclassify_conventional(_c("fix(auth): handle expired token"))
    assert cc is not None
    assert cc.type == "fix"


def test_preclassify_returns_none_for_non_conventional():
    assert preclassify_conventional(_c("just some change")) is None


def test_preclassify_business_fields_empty_until_llm():
    cc = preclassify_conventional(_c("feat: x"))
    assert cc.business_value == ""
    assert cc.business_description == ""
