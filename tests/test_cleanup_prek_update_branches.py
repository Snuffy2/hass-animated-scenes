"""Tests for the prek autoupdate cleanup helper."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest

SCRIPT_PATH = Path(__file__).parents[1] / ".github" / "scripts" / "cleanup_prek_update_branches.py"


def _load_cleanup_module() -> ModuleType:
    """Load the workflow cleanup script as an importable test module."""
    spec = importlib.util.spec_from_file_location("cleanup_prek_update_branches", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load cleanup_prek_update_branches.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


cleanup = _load_cleanup_module()


class FakeGithubClient:
    """Record cleanup actions without calling the GitHub API."""

    def __init__(
        self,
        *,
        open_pulls: list[dict[str, object]] | None = None,
        closed_pulls: list[dict[str, object]] | None = None,
    ) -> None:
        """Initialize fake pull lists and action logs."""
        self.open_pulls = open_pulls or []
        self.closed_pulls = closed_pulls or []
        self.closed_numbers: list[int] = []
        self.deleted_refs: list[str] = []
        self.list_calls: list[dict[str, Any]] = []

    def list_pulls(self, *, state: str, max_pages: int | None = None) -> list[dict[str, object]]:
        """Return configured pull requests for the requested state."""
        self.list_calls.append({"state": state, "max_pages": max_pages})
        if state == "open":
            return self.open_pulls
        if state == "closed":
            return self.closed_pulls
        raise ValueError(f"Unexpected state {state}")

    def close_pull(self, pull_number: int) -> None:
        """Record a close request."""
        self.closed_numbers.append(pull_number)

    def delete_ref(self, ref: str) -> None:
        """Record a ref deletion request."""
        self.deleted_refs.append(ref)


def _pull(
    number: int,
    *,
    head_ref: str = "chore/prek-updates-old",
    label: str = "dependencies",
    author: str = "github-actions[bot]",
    body: str = "Automated update of `prek` hooks.",
    repository: str = "owner/repo",
    merged_at: str | None = None,
) -> dict[str, object]:
    """Build a minimal GitHub pull request payload."""
    return {
        "number": number,
        "labels": [{"name": label}],
        "user": {"login": author},
        "body": body,
        "head": {"ref": head_ref, "repo": {"full_name": repository}},
        "merged_at": merged_at,
    }


def test_next_link_returns_next_pagination_url() -> None:
    """Parse the next URL from GitHub's Link header."""
    link_header = (
        '<https://api.github.com/repositories/1/pulls?page=2>; rel="next", '
        '<https://api.github.com/repositories/1/pulls?page=5>; rel="last"'
    )

    assert cleanup._next_link(link_header) == "https://api.github.com/repositories/1/pulls?page=2"
    assert (
        cleanup._next_link('<https://api.github.com/repositories/1/pulls?page=5>; rel="last"')
        is None
    )
    assert cleanup._next_link(None) is None


def _workflow_pull_kwargs() -> dict[str, str]:
    """Return the ownership markers for workflow-created update pull requests."""
    return {
        "repository": "owner/repo",
        "branch": "chore/prek-updates",
        "branch_prefix": "chore/prek-updates",
        "label_name": "dependencies",
        "author_login": "github-actions[bot]",
        "body_marker": "Automated update of `prek` hooks.",
    }


def test_is_workflow_pull_accepts_matching_ownership_markers() -> None:
    """Accept a pull request with every workflow ownership marker."""
    assert cleanup._is_workflow_pull(_pull(1), **_workflow_pull_kwargs()) is True


@pytest.mark.parametrize(
    "pull",
    [
        pytest.param(_pull(1, label="manual"), id="label"),
        pytest.param(_pull(1, author="alice"), id="author"),
        pytest.param(_pull(1, body="manual update"), id="body"),
        pytest.param(_pull(1, head_ref="feature/manual"), id="branch"),
        pytest.param(_pull(1, repository="fork/repo"), id="repository"),
    ],
)
def test_is_workflow_pull_rejects_missing_ownership_marker(
    pull: dict[str, object],
) -> None:
    """Reject pull requests missing any workflow ownership marker."""
    assert cleanup._is_workflow_pull(pull, **_workflow_pull_kwargs()) is False


def test_cleanup_update_branches_keeps_current_pr_and_deletes_stale_refs() -> None:
    """Close stale workflow PRs while protecting the PR created by this run."""
    client = FakeGithubClient(
        open_pulls=[
            _pull(10, head_ref="chore/prek-updates"),
            _pull(11, head_ref="chore/prek-updates-stale"),
            _pull(12, head_ref="feature/manual"),
        ],
        closed_pulls=[
            _pull(20, head_ref="chore/prek-updates-merged", merged_at="2026-06-05T01:00:00Z"),
            _pull(21, head_ref="chore/prek-updates-closed"),
        ],
    )

    result = cleanup.cleanup_update_branches(
        client=client,
        **_workflow_pull_kwargs(),
        keep_pr_number=10,
        close_stale_prs=True,
        delete_stale_branch=True,
        delete_merged_branches=True,
    )

    assert result.closed_prs == [11]
    assert result.deleted_branches == [
        "chore/prek-updates-merged",
        "chore/prek-updates-stale",
    ]
    assert client.closed_numbers == [11]
    assert client.deleted_refs == [
        "heads/chore/prek-updates-merged",
        "heads/chore/prek-updates-stale",
    ]
    assert client.list_calls == [
        {"state": "open", "max_pages": None},
        {"state": "closed", "max_pages": cleanup.CLOSED_PULL_PAGE_LIMIT},
    ]


def test_cleanup_update_branches_deletes_current_stale_branch_when_unprotected() -> None:
    """Delete the current workflow branch when no kept PR protects it."""
    client = FakeGithubClient(open_pulls=[])

    result = cleanup.cleanup_update_branches(
        client=client,
        **_workflow_pull_kwargs(),
        keep_pr_number=None,
        close_stale_prs=False,
        delete_stale_branch=True,
        delete_merged_branches=False,
    )

    assert result.deleted_branches == ["chore/prek-updates"]
    assert client.deleted_refs == ["heads/chore/prek-updates"]
