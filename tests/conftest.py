"""Shared pytest fixtures for Animated Scenes integration tests."""

from collections.abc import Iterator

import pytest

from custom_components.animated_scenes.animations import Animations
from custom_components.animated_scenes.const import DOMAIN

pytest_plugins = ("pytest_homeassistant_custom_component",)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Iterator[None]:
    """Enable custom integrations for every test.

    Yields:
        None. The fixture restores the animation singleton after each test.

    """
    _ = enable_custom_integrations
    previous_instance = Animations.instance
    try:
        yield
    finally:
        Animations.instance = previous_instance


@pytest.fixture
def integration_domain() -> str:
    """Return the Animated Scenes integration domain.

    Returns:
        str: The integration domain used by Home Assistant tests.

    """
    return DOMAIN
