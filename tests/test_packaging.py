"""Tests for Python package metadata."""

from __future__ import annotations

import ast
from pathlib import Path
import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
CONST_PATH = REPO_ROOT / "custom_components" / "animated_scenes" / "const.py"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
POST_COVERAGE_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "post_coverage_to_pr.yml"
RELEASE_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"


def _const_version() -> str:
    """Read VERSION from const.py without importing the integration package."""
    module = ast.parse(CONST_PATH.read_text(encoding="utf-8"))
    for node in module.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise AssertionError("VERSION constant not found")


def test_static_project_version_matches_integration_constant() -> None:
    """Keep package metadata version static and synchronized without importing HA."""
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))

    assert pyproject["project"]["version"] == _const_version()
    assert "dynamic" not in pyproject["project"]


def test_package_data_includes_runtime_yaml_and_brand_assets() -> None:
    """Include Home Assistant service descriptions and brand icons in packages."""
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]

    assert "*.yaml" in package_data["custom_components.animated_scenes"]
    assert "brand/*.png" in package_data["custom_components.animated_scenes"]


def test_release_workflow_updates_static_package_version() -> None:
    """Keep release automation synchronized with static package metadata."""
    workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Update Version in pyproject.toml" in workflow
    assert "RELEASE_TAG: ${{ github.event.release.tag_name }}" in workflow
    assert "${RELEASE_TAG}" in workflow


def test_post_coverage_workflow_skips_prs_without_comment_artifacts() -> None:
    """Keep the privileged coverage comment workflow aligned with artifact creation."""
    workflow = POST_COVERAGE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Check coverage comment eligibility" in workflow
    assert "github.rest.pulls.get" in workflow
    assert "github.rest.actions.listWorkflowRunArtifacts" in workflow
    assert "artifact.name === 'python-coverage-comment-action'" in workflow
    assert "hasCommentArtifact &&" in workflow
    assert "labels.includes('dependencies')" in workflow
    assert "pullRequest.user?.type !== 'Bot'" in workflow
    assert "if: steps.coverage_eligibility.outputs.should_post == 'true'" in workflow
