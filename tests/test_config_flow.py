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
    CONF_COLOR,
    CONF_COLOR_NEARBY_COLORS,
    CONF_COLOR_RGB_DICT,
    CONF_COLOR_SELECTOR_MODE,
    CONF_COLOR_WEIGHT,
    CONF_COLORS,
    CONF_ENTITY_TYPE,
    CONF_TRANSITION,
    DEFAULT_COLOR_NEARBY_COLORS,
    DEFAULT_COLOR_WEIGHT,
    DOMAIN,
    ENTITY_SCENE,
    ERROR_COLORS_IS_BLANK,
    ERROR_COLORS_MALFORMED,
)


def _schema_has_key(data_schema: object, key: str) -> bool:
    """Return whether a voluptuous schema includes a top-level key."""
    schema = getattr(data_schema, "schema", {})
    return any(getattr(marker, "schema", marker) == key for marker in schema)


def _options_flow(
    hass: HomeAssistant,
    *,
    selector_mode: str = COLOR_SELECTOR_YAML,
    color_rgb_dict: dict[str, dict[str, object]] | None = None,
) -> tuple[AnimatedScenesOptionsFlowHandler, MockConfigEntry]:
    """Return an options flow and its backing scene config entry."""
    data: dict[str, object] = {
        CONF_NAME: "Spooky",
        CONF_ENTITY_TYPE: ENTITY_SCENE,
        CONF_COLOR_SELECTOR_MODE: selector_mode,
        CONF_LIGHTS: ["light.one"],
        CONF_TRANSITION: 1,
    }
    if selector_mode == COLOR_SELECTOR_RGB_UI:
        data[CONF_COLOR_RGB_DICT] = color_rgb_dict or {}
    else:
        data.update(
            {
                "change_frequency": 1,
                "change_amount": "all",
                "brightness": 255,
            }
        )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Spooky",
        data=data,
        entry_id="spooky",
    )
    entry.add_to_hass(hass)
    flow = AnimatedScenesOptionsFlowHandler(entry)
    flow.hass = hass
    return flow, entry


async def test_options_rgb_ui_handles_empty_existing_color_dict(hass: HomeAssistant) -> None:
    """Show the first RGB color form when stored color data is empty.

    Args:
        hass: Home Assistant test instance.

    """
    flow, _ = _options_flow(hass, selector_mode=COLOR_SELECTOR_RGB_UI)

    result = await flow.async_step_color_rgb_ui()

    assert result["type"] == "form"
    assert result["step_id"] == "color_rgb_ui"


async def test_options_scene_form_exposes_name_for_rename(hass: HomeAssistant) -> None:
    """Expose the scene name in options so users can submit renames."""
    flow, _ = _options_flow(hass)

    result = await flow.async_step_init()

    assert result["type"] == "form"
    assert _schema_has_key(result["data_schema"], CONF_NAME)


async def test_options_rgb_ui_defaults_missing_optional_color_values(
    hass: HomeAssistant,
) -> None:
    """Apply optional RGB UI color defaults before rounding submitted values."""
    flow, entry = _options_flow(hass, selector_mode=COLOR_SELECTOR_RGB_UI)

    with patch.object(hass.config_entries, "async_reload", AsyncMock()):
        result = await flow.async_step_color_rgb_ui({CONF_COLOR: [255, 0, 0]})

    assert result["type"] == "create_entry"
    color_data = next(iter(entry.data[CONF_COLOR_RGB_DICT].values()))
    assert color_data[CONF_COLOR_WEIGHT] == DEFAULT_COLOR_WEIGHT
    assert color_data[CONF_COLOR_NEARBY_COLORS] == DEFAULT_COLOR_NEARBY_COLORS


async def test_options_rename_stops_previous_animation_before_reload(
    hass: HomeAssistant,
) -> None:
    """Stop an active pre-rename animation before options update entry data."""
    manager = Animations(hass)
    manager.animations["Spooky"] = cast("Animation", AsyncMock())
    Animations.instance = manager
    flow, entry = _options_flow(hass)

    with (
        patch.object(manager, "stop_by_name", AsyncMock()) as stop_by_name,
        patch.object(hass.config_entries, "async_reload", AsyncMock()) as reload_entry,
    ):
        scene_result = await flow.async_step_scene({CONF_NAME: "Scary"})
        result = await flow.async_step_color_yaml(
            {CONF_COLORS: [{"color_type": "rgb_color", "color": [255, 0, 0]}]}
        )

    assert scene_result["type"] == "form"
    assert scene_result["step_id"] == "color_yaml"
    stop_by_name.assert_awaited_once_with("Spooky")
    reload_entry.assert_awaited_once_with("spooky")
    assert entry.title == "Scary"
    assert entry.data[CONF_NAME] == "Scary"
    assert result["type"] == "create_entry"


async def test_options_yaml_rejects_empty_color_list(hass: HomeAssistant) -> None:
    """Reject an empty YAML color list before saving options."""
    flow, _ = _options_flow(hass)

    result = await flow.async_step_color_yaml({CONF_COLORS: []})

    assert result["type"] == "form"
    errors = result["errors"]
    assert errors is not None
    assert errors["base"] == ERROR_COLORS_IS_BLANK


async def test_options_yaml_rejects_malformed_color_payload(
    hass: HomeAssistant,
) -> None:
    """Reject malformed YAML colors before saving options."""
    flow, _ = _options_flow(hass)

    result = await flow.async_step_color_yaml(
        {CONF_COLORS: [{"color_type": "rgb_color", "color": [255, 0]}]}
    )

    assert result["type"] == "form"
    errors = result["errors"]
    assert errors is not None
    assert errors["base"] == ERROR_COLORS_MALFORMED
