"""Tests for Animated Scenes runtime manager and service setup."""

from __future__ import annotations

import pytest

from custom_components.animated_scenes import async_setup
from custom_components.animated_scenes.const import DOMAIN
from custom_components.animated_scenes.scene_config import (
    ADD_LIGHTS_TO_ANIMATION_SERVICE_SCHEMA,
    REMOVE_LIGHTS_SERVICE_SCHEMA,
    START_SERVICE_SCHEMA,
    STOP_SERVICE_SCHEMA,
)
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_services_register_with_schema(hass: HomeAssistant) -> None:
    """Require each public service registration to enforce its shared schema.

    Home Assistant applies the schema passed to ``async_register`` before the
    service handler runs. This protects the runtime manager from receiving
    malformed service data through the public service API.
    """

    assert await async_setup(hass, {}) is True

    registrations = hass.services.async_services_internal()[DOMAIN]

    assert set(registrations) == {
        "start_animation",
        "stop_animation",
        "remove_lights",
        "add_lights_to_animation",
    }
    assert registrations["start_animation"].schema is START_SERVICE_SCHEMA
    assert registrations["stop_animation"].schema is STOP_SERVICE_SCHEMA
    assert registrations["remove_lights"].schema is REMOVE_LIGHTS_SERVICE_SCHEMA
    assert registrations["add_lights_to_animation"].schema is ADD_LIGHTS_TO_ANIMATION_SERVICE_SCHEMA
