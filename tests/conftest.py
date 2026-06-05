"""Shared pytest fixtures for Animated Scenes integration tests."""

from collections.abc import Generator

import pytest

from custom_components.animated_scenes.const import DOMAIN

pytest_plugins = ("pytest_homeassistant_custom_component",)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Generator[None, None, None]:
    """Enable custom integrations for every test.

    Yields:
        None: Control returns to pytest after custom integrations are enabled.

    """
    yield


@pytest.fixture
def integration_domain() -> str:
    """Return the Animated Scenes integration domain.

    Returns:
        str: The integration domain used by Home Assistant tests.

    """
    return DOMAIN
