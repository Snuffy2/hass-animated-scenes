"""Shared pytest fixtures for Animated Scenes integration tests."""

import pytest

from custom_components.animated_scenes.const import DOMAIN

pytest_plugins = ("pytest_homeassistant_custom_component",)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations for every test.

    Returns:
        None.

    """
    return


@pytest.fixture
def integration_domain() -> str:
    """Return the Animated Scenes integration domain.

    Returns:
        str: The integration domain used by Home Assistant tests.

    """
    return DOMAIN
