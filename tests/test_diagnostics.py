"""Tests for Animated Scenes diagnostics."""

from __future__ import annotations

import pytest

from custom_components.animated_scenes.animations import Animations
from custom_components.animated_scenes.const import (
    COLOR_SELECTOR_RGB_UI,
    CONF_COLOR_RGB_DICT,
    CONF_COLOR_SELECTOR_MODE,
    DOMAIN,
    INTEGRATION_NAME,
)
from custom_components.animated_scenes.diagnostics import async_get_config_entry_diagnostics
from custom_components.animated_scenes.sensor import AnimatedScenesSensor
from custom_components.animated_scenes.switch import AnimatedSceneSwitch
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_diagnostics_redacts_entity_ids_and_reports_runtime(
    hass: HomeAssistant,
) -> None:
    """Return redacted config data with a summary of runtime manager state."""
    manager = Animations(hass)
    Animations.instance = manager
    manager.light_owner["light.kitchen"] = object()  # type: ignore[assignment]
    entry = _diagnostic_entry()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["title"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["name"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["lights"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["target"]["entity_id"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["selector"]["animated_scene_switch"] == "**REDACTED**"
    assert diagnostics["runtime"]["active_light_count"] == 1


@pytest.mark.asyncio
async def test_diagnostics_reports_zero_runtime_without_manager(hass: HomeAssistant) -> None:
    """Return zero runtime counters when no animation manager is active."""
    Animations.instance = None

    diagnostics = await async_get_config_entry_diagnostics(hass, _diagnostic_entry())

    assert diagnostics["runtime"] == {
        "active_animation_count": 0,
        "active_light_count": 0,
        "stored_state_count": 0,
    }


def test_entities_expose_animated_scenes_device_info(hass: HomeAssistant) -> None:
    """Group switch and sensor entities under the Animated Scenes device."""
    switch = AnimatedSceneSwitch(hass, _switch_config(), "entry-id")
    sensor = AnimatedScenesSensor(hass)
    expected_device = {
        "identifiers": {(DOMAIN, "animated_scenes")},
        "name": INTEGRATION_NAME,
        "manufacturer": INTEGRATION_NAME,
    }

    assert switch.device_info == expected_device
    assert sensor.device_info == expected_device


def _diagnostic_entry() -> ConfigEntry:
    """Return a config entry containing every redacted diagnostics key.

    Returns:
        A config entry with top-level and nested entity identifiers plus a
        user-authored scene name.

    """
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Kitchen Spooky",
        data={
            "name": "Kitchen Spooky",
            "lights": ["light.kitchen"],
            "colors": [],
            "target": {"entity_id": "light.kitchen"},
            "selector": {"animated_scene_switch": "switch.kitchen_spooky"},
        },
        discovery_keys={},
        options={},
        source="user",
        subentries_data={},
        unique_id=None,
        entry_id="spooky",
    )


def _switch_config() -> dict[str, object]:
    """Return config-entry data for constructing a diagnostics switch.

    Returns:
        A minimal switch configuration with RGB UI colors so construction can
        build the runtime animation config.

    """
    return {
        "name": "Spooky",
        "icon": "mdi:lightbulb",
        "lights": ["light.one"],
        "colors": {},
        CONF_COLOR_SELECTOR_MODE: COLOR_SELECTOR_RGB_UI,
        CONF_COLOR_RGB_DICT: {"one": {"color": [255, 0, 0], "brightness": 255, "weight": 10}},
        "ignore_off": True,
        "restore": True,
        "restore_power": False,
        "brightness": 255,
        "transition": 1,
        "change_frequency": 1,
        "change_amount": "all",
        "change_sequence": False,
        "animate_brightness": True,
        "animate_color": True,
        "priority": 0,
        "entity_type": "scene",
    }
