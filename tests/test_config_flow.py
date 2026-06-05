"""Tests for Animated Scenes config and options flows."""

from __future__ import annotations

from homeassistant.const import CONF_LIGHTS, CONF_NAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.animated_scenes.config_flow import AnimatedScenesOptionsFlowHandler
from custom_components.animated_scenes.const import (
    COLOR_SELECTOR_RGB_UI,
    CONF_COLOR_RGB_DICT,
    CONF_COLOR_SELECTOR_MODE,
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
