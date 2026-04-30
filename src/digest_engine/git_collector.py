import re
import subprocess
from datetime import datetime
from pathlib import Path
from .config import RepoConfig
from .types import Commit, RepoCommits


_PRETTY = "%H%x09%an%x09%aI%x09%s"


def collect_commits(repo: RepoConfig, since: datetime, until: datetime) -> RepoCommits:
    path = Path(repo.path).resolve()
    if not (path / ".git").exists():
        raise FileNotFoundError(f"not a git repo: {path}")

    cmd = [
        "git", "-C", str(path), "log", repo.branch,
        f"--since={since.isoformat()}",
        f"--until={until.isoformat()}",
        f"--pretty=format:{_PRETTY}",
        "--numstat",
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout

    commits: list[Commit] = []
    ignored = [re.compile(p) for p in repo.ignore_patterns]
    for block in out.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        header = lines[0]
        try:
            h, author, iso, message = header.split("\t", 3)
        except ValueError:
            continue
        if any(pat.match(message) for pat in ignored):
            continue
        adds, dels, files = 0, 0, 0
        for ln in lines[1:]:
            parts = ln.split("\t")
            if len(parts) != 3:
                continue
            files += 1
            try:
                adds += int(parts[0]) if parts[0] != "-" else 0
                dels += int(parts[1]) if parts[1] != "-" else 0
            except ValueError:
                pass
        commits.append(Commit(
            hash=h, author=author, date=datetime.fromisoformat(iso),
            message=message, files_changed=files, additions=adds, deletions=dels,
        ))
    return RepoCommits(repo_name=repo.name, commits=commits)
