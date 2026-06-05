"""Tests for Python package metadata."""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_package_data_includes_runtime_yaml_and_brand_assets() -> None:
    """Include Home Assistant service descriptions and brand icons in packages."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]

    assert "*.yaml" in package_data["custom_components.animated_scenes"]
    assert "brand/*.png" in package_data["custom_components.animated_scenes"]
