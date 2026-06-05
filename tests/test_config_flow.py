"""Tests for Animated Scenes config and options flows."""

from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_LIGHTS, CONF_NAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.animated_scenes.animations import Animation, Animations
from custom_components.animated_scenes.config_flow import AnimatedScenesOptionsFlowHandler
from custom_components.animated_scenes.const import (
    COLOR_SELECTOR_RGB_UI,
    COLOR_SELECTOR_YAML,
    CONF_COLOR_RGB_DICT,
    CONF_COLOR_SELECTOR_MODE,
    CONF_COLORS,
    CONF_ENTITY_TYPE,
    CONF_TRANSITION,
    DOMAIN,
    ENTITY_SCENE,
)


async def test_options_rgb_ui_handles_empty_existing_color_dict(hass: HomeAssistant) -> None:
    """Show the first RGB color form when stored color data is empty.

    Args:
        hass: Home Assistant test instance.

    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Spooky",
        data={
            CONF_NAME: "Spooky",
            CONF_ENTITY_TYPE: ENTITY_SCENE,
            CONF_COLOR_SELECTOR_MODE: COLOR_SELECTOR_RGB_UI,
            CONF_COLOR_RGB_DICT: {},
            CONF_LIGHTS: ["light.one"],
            CONF_TRANSITION: 1,
        },
        entry_id="spooky",
    )
    entry.add_to_hass(hass)
    flow = AnimatedScenesOptionsFlowHandler(entry)
    flow.hass = hass

    result = await flow.async_step_color_rgb_ui()

    assert result["type"] == "form"
    assert result["step_id"] == "color_rgb_ui"


async def test_options_rename_stops_previous_animation_before_reload(
    hass: HomeAssistant,
) -> None:
    """Stop an active pre-rename animation before options update entry data."""
    manager = Animations(hass)
    manager.animations["Spooky"] = cast("Animation", AsyncMock())
    Animations.instance = manager
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Spooky",
        data={
            CONF_NAME: "Spooky",
            CONF_ENTITY_TYPE: ENTITY_SCENE,
            CONF_COLOR_SELECTOR_MODE: COLOR_SELECTOR_YAML,
            CONF_LIGHTS: ["light.one"],
            CONF_TRANSITION: 1,
            "change_frequency": 1,
            "change_amount": "all",
            "brightness": 255,
        },
        entry_id="spooky",
    )
    entry.add_to_hass(hass)
    flow = AnimatedScenesOptionsFlowHandler(entry)
    flow.hass = hass
    flow._data.update(
        {
            CONF_NAME: "Scary",
            CONF_ENTITY_TYPE: ENTITY_SCENE,
            CONF_COLOR_SELECTOR_MODE: COLOR_SELECTOR_YAML,
            CONF_LIGHTS: ["light.one"],
            CONF_TRANSITION: 1,
            "change_frequency": 1,
            "change_amount": "all",
            "brightness": 255,
        }
    )

    with (
        patch.object(manager, "stop_by_name", AsyncMock()) as stop_by_name,
        patch.object(hass.config_entries, "async_reload", AsyncMock()) as reload_entry,
    ):
        result = await flow.async_step_color_yaml(
            {CONF_COLORS: [{"color_type": "rgb_color", "color": [255, 0, 0]}]}
        )

    stop_by_name.assert_awaited_once_with("Spooky")
    reload_entry.assert_awaited_once_with("spooky")
    assert entry.title == "Scary"
    assert entry.data[CONF_NAME] == "Scary"
    assert result["type"] == "create_entry"
