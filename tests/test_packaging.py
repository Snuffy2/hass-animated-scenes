"""Tests for Python package metadata."""

from __future__ import annotations

import ast
from pathlib import Path
import tomllib


def _const_version() -> str:
    """Read VERSION from const.py without importing the integration package."""
    module = ast.parse(Path("custom_components/animated_scenes/const.py").read_text())
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
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["version"] == _const_version()
    assert "dynamic" not in pyproject["project"]


def test_package_data_includes_runtime_yaml_and_brand_assets() -> None:
    """Include Home Assistant service descriptions and brand icons in packages."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]

    assert "*.yaml" in package_data["custom_components.animated_scenes"]
    assert "brand/*.png" in package_data["custom_components.animated_scenes"]
