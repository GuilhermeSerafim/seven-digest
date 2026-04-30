from .types import Commit, ClassifiedCommit


def preclassify_conventional(commit: Commit) -> ClassifiedCommit | None:
    t = commit.conventional_type()
    if t is None:
        return None
    return ClassifiedCommit(
        commit=commit,
        type=t,
        business_value="",
        business_description="",
        complexity_estimate="",
    )
