"""Tests for Animated Scenes switch entities."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
import pytest

from custom_components.animated_scenes.animations import Animations
from custom_components.animated_scenes.const import (
    COLOR_SELECTOR_RGB_UI,
    CONF_COLOR_RGB_DICT,
    CONF_COLOR_SELECTOR_MODE,
    EVENT_NAME_CHANGE,
    EVENT_STATE_STARTED,
    EVENT_STATE_STOPPED,
)
from custom_components.animated_scenes.switch import AnimatedSceneSwitch


def _switch_config() -> dict[str, object]:
    """Return a valid scene switch config-entry payload.

    Returns:
        A config-entry data dictionary that exercises RGB UI color conversion
        and contains the runtime keys required to start an animation.

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


@pytest.mark.asyncio
async def test_switch_animation_config_ready_in_constructor(hass: HomeAssistant) -> None:
    """Build runtime animation data before the switch can be turned on.

    The constructor must prepare the RGB UI color list synchronously so an
    immediate service or UI turn-on cannot start an animation with an empty
    config.
    """
    switch = AnimatedSceneSwitch(hass, _switch_config(), "entry-id")

    assert switch._animation_config["colors"] == [
        {
            "color": [255, 0, 0],
            "brightness": 255,
            "weight": 10,
            "color_type": "rgb_color",
        }
    ]


@pytest.mark.asyncio
async def test_switch_tracks_animation_events(hass: HomeAssistant) -> None:
    """Update switch state immediately when animation lifecycle events fire."""
    switch = AnimatedSceneSwitch(hass, _switch_config(), "entry-id")
    switch.hass = hass
    with patch.object(AnimatedSceneSwitch, "async_write_ha_state") as write_state:
        await switch.async_added_to_hass()

        hass.bus.async_fire(
            EVENT_NAME_CHANGE,
            {"animation": "Spooky", "state": EVENT_STATE_STARTED},
        )
        await hass.async_block_till_done()

        assert switch.is_on is True
        write_state.assert_called()
        started_write_count = write_state.call_count

        hass.bus.async_fire(
            EVENT_NAME_CHANGE,
            {"animation": "Spooky", "state": EVENT_STATE_STOPPED},
        )
        await hass.async_block_till_done()

        assert switch.is_on is False
        assert write_state.call_count == started_write_count + 1

        hass.bus.async_fire(
            EVENT_NAME_CHANGE,
            {"animation": "Other", "state": EVENT_STATE_STARTED},
        )
        await hass.async_block_till_done()

        assert switch.is_on is False
        assert write_state.call_count == started_write_count + 1


@pytest.mark.asyncio
async def test_switch_turn_on_stays_off_for_one_shot_scene(hass: HomeAssistant) -> None:
    """Keep one-shot scenes off after the manager releases them during startup."""
    manager = Animations(hass)
    Animations.instance = manager
    config = _switch_config()
    config["change_frequency"] = 0
    switch = AnimatedSceneSwitch(hass, config, "entry-id")

    await switch.async_turn_on()

    assert switch.is_on is False
    assert manager.animations == {}
