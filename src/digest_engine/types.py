from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
import re

_CONVENTIONAL_RE = re.compile(
    r"^(feat|fix|docs|chore|refactor|test|ci|infra|perf|style|build)(\([^)]+\))?!?:"
)

CommitType = Literal[
    "feat", "fix", "docs", "chore", "refactor", "test", "ci", "infra", "perf", "other"
]
Complexity = Literal["baixa", "média", "alta"]


@dataclass
class Commit:
    hash: str
    author: str
    date: datetime
    message: str
    files_changed: int
    additions: int
    deletions: int

    def is_conventional(self) -> bool:
        return _CONVENTIONAL_RE.match(self.message) is not None

    def conventional_type(self) -> str | None:
        m = _CONVENTIONAL_RE.match(self.message)
        return m.group(1) if m else None


@dataclass
class ClassifiedCommit:
    commit: Commit
    type: str
    business_value: str
    business_description: str
    complexity_estimate: str


@dataclass
class RepoCommits:
    repo_name: str
    commits: list[Commit] = field(default_factory=list)


@dataclass
class BrandConfig:
    primary_color: str
    light_color: str
    logo_path: str | None


@dataclass
class ReportData:
    title: str
    subtitle: str
    week_id: str
    executive_summary: str
    metrics: dict[str, dict[str, int]]  # {repo_name: {metric: count}}
    days: list[dict]                    # [{date_label: str, items: list[str]}]
    highlights: list[str]
    next_steps: list[str]
