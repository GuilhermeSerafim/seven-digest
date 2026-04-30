import subprocess
from datetime import datetime, timezone
from pathlib import Path
import pytest
from digest_engine.git_collector import collect_commits
from digest_engine.config import RepoConfig


def _run(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "fake"
    repo.mkdir()
    _run(repo, "init", "-b", "main")
    _run(repo, "config", "user.email", "t@t.com")
    _run(repo, "config", "user.name", "T")
    (repo / "a.txt").write_text("a")
    _run(repo, "add", ".")
    _run(repo, "commit", "-m", "feat: add A")
    (repo / "b.txt").write_text("b")
    _run(repo, "add", ".")
    _run(repo, "commit", "-m", "chore(deps): bump x")
    (repo / "c.txt").write_text("c")
    _run(repo, "add", ".")
    _run(repo, "commit", "-m", "fix: correct B")
    return repo


def test_collect_commits_returns_within_window(fake_repo: Path):
    cfg = RepoConfig(name="t", path=str(fake_repo), branch="main", ignore_patterns=[])
    start = datetime(2000, 1, 1, tzinfo=timezone.utc)
    end = datetime(2099, 1, 1, tzinfo=timezone.utc)
    rc = collect_commits(cfg, start, end)
    assert rc.repo_name == "t"
    assert len(rc.commits) == 3
    assert all(c.hash for c in rc.commits)
    assert rc.commits[0].message.startswith("fix:")  # most recent first


def test_collect_commits_applies_ignore_patterns(fake_repo: Path):
    cfg = RepoConfig(
        name="t", path=str(fake_repo), branch="main",
        ignore_patterns=["^chore\\(deps\\):"],
    )
    rc = collect_commits(cfg,
        datetime(2000, 1, 1, tzinfo=timezone.utc),
        datetime(2099, 1, 1, tzinfo=timezone.utc))
    assert len(rc.commits) == 2
    assert all("chore(deps)" not in c.message for c in rc.commits)


def test_collect_commits_returns_empty_for_no_match(fake_repo: Path):
    cfg = RepoConfig(name="t", path=str(fake_repo), branch="main", ignore_patterns=[])
    rc = collect_commits(cfg,
        datetime(1990, 1, 1, tzinfo=timezone.utc),
        datetime(1990, 1, 2, tzinfo=timezone.utc))
    assert rc.commits == []
