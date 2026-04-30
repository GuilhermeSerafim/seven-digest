from datetime import datetime, timezone
from pathlib import Path
from digest_engine.types import Commit, RepoCommits, ClassifiedCommit
from digest_engine.classifier import preclassify_conventional, classify_all
from digest_engine.llm_client import LLMClient, ClassificationRequest, SummaryRequest


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


class FakeLLM:
    def __init__(self):
        self.classify_calls: list[ClassificationRequest] = []
        self.summary_calls: list[SummaryRequest] = []

    def classify_batch(self, req):
        self.classify_calls.append(req)
        return [
            ClassifiedCommit(commit=c, type=c.conventional_type() or "other",
                             business_value="bv", business_description="bd",
                             complexity_estimate="média")
            for c in req.commits
        ]

    def synthesize_summary(self, req):
        self.summary_calls.append(req)
        return "summary"


def test_classify_all_uses_pre_classification_then_llm(tmp_path: Path):
    commits = [_c("feat: A"), _c("garbage commit"), _c("fix: B")]
    commits[0] = Commit(**{**commits[0].__dict__, "hash": "H1"})
    commits[1] = Commit(**{**commits[1].__dict__, "hash": "H2"})
    commits[2] = Commit(**{**commits[2].__dict__, "hash": "H3"})
    repo = RepoCommits(repo_name="r", commits=commits)
    fake = FakeLLM()
    out = classify_all([repo], llm=fake, audience="aud", cache_dir=tmp_path)
    assert "r" in out
    assert len(out["r"]) == 3
    # Only the LLM call was needed for non-conventional commits
    assert len(fake.classify_calls) == 1
    assert len(fake.classify_calls[0].commits) == 3  # all sent (LLM enriches business fields)


def test_classify_all_uses_cache_on_second_run(tmp_path: Path):
    commits = [_c("feat: A")]
    commits[0] = Commit(**{**commits[0].__dict__, "hash": "HX"})
    repo = RepoCommits(repo_name="r", commits=commits)
    fake1 = FakeLLM()
    classify_all([repo], llm=fake1, audience="aud", cache_dir=tmp_path)
    assert len(fake1.classify_calls) == 1
    fake2 = FakeLLM()
    classify_all([repo], llm=fake2, audience="aud", cache_dir=tmp_path)
    assert len(fake2.classify_calls) == 0  # served from cache


def test_classify_all_batches_in_chunks_of_15(tmp_path: Path):
    commits = []
    for i in range(33):
        c = _c(f"feat: x{i}")
        commits.append(Commit(**{**c.__dict__, "hash": f"H{i:03d}"}))
    repo = RepoCommits(repo_name="r", commits=commits)
    fake = FakeLLM()
    classify_all([repo], llm=fake, audience="aud", cache_dir=tmp_path, batch_size=15)
    assert len(fake.classify_calls) == 3  # 15 + 15 + 3
