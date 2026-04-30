from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path
import json
from .types import Commit, ClassifiedCommit, RepoCommits
from .llm_client import LLMClient, ClassificationRequest


def preclassify_conventional(commit: Commit) -> ClassifiedCommit | None:
    t = commit.conventional_type()
    if t is None:
        return None
    return ClassifiedCommit(
        commit=commit, type=t,
        business_value="", business_description="", complexity_estimate="",
    )


def _cache_path(cache_dir: Path, h: str) -> Path:
    return cache_dir / f"{h}.json"


def _load_cached(cache_dir: Path, commit: Commit) -> ClassifiedCommit | None:
    p = _cache_path(cache_dir, commit.hash)
    if not p.exists():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    return ClassifiedCommit(
        commit=commit,
        type=raw["type"],
        business_value=raw["business_value"],
        business_description=raw["business_description"],
        complexity_estimate=raw["complexity_estimate"],
    )


def _save_cached(cache_dir: Path, cc: ClassifiedCommit) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": cc.type,
        "business_value": cc.business_value,
        "business_description": cc.business_description,
        "complexity_estimate": cc.complexity_estimate,
    }
    _cache_path(cache_dir, cc.commit.hash).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def classify_all(
    repos: list[RepoCommits],
    *, llm: LLMClient, audience: str,
    cache_dir: Path, batch_size: int = 15,
) -> dict[str, list[ClassifiedCommit]]:
    cache_dir = Path(cache_dir)
    out: dict[str, list[ClassifiedCommit]] = {}
    for repo in repos:
        results: list[ClassifiedCommit] = []
        to_classify: list[Commit] = []
        for c in repo.commits:
            cached = _load_cached(cache_dir, c)
            if cached is not None:
                results.append(cached)
            else:
                to_classify.append(c)

        for i in range(0, len(to_classify), batch_size):
            batch = to_classify[i:i + batch_size]
            req = ClassificationRequest(commits=batch, audience=audience)
            classified = llm.classify_batch(req)
            for cc in classified:
                _save_cached(cache_dir, cc)
                results.append(cc)
        out[repo.repo_name] = results
    return out
