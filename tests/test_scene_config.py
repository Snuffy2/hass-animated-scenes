"""Tests for shared Animated Scenes configuration normalization."""

from __future__ import annotations

import pytest
import voluptuous as vol

from custom_components.animated_scenes.const import (
    CONF_CHANGE_AMOUNT,
    CONF_COLOR_RGB,
    CONF_COLORS,
    DEFAULT_ANIMATE_BRIGHTNESS,
    DEFAULT_ANIMATE_COLOR,
    DEFAULT_CHANGE_SEQUENCE,
    DEFAULT_IGNORE_OFF,
    DEFAULT_PRIORITY,
    DEFAULT_RESTORE,
    DEFAULT_RESTORE_POWER,
)
from custom_components.animated_scenes.scene_config import (
    build_colors_from_rgb_dict,
    normalize_scene_input,
    validate_start_service_data,
)
from homeassistant.const import CONF_BRIGHTNESS, CONF_LIGHTS, CONF_NAME


def _base_input() -> dict[str, object]:
    """Return minimal valid scene input."""
    return {
        CONF_NAME: "Spooky",
        CONF_LIGHTS: ["light.one", "light.two"],
        CONF_CHANGE_AMOUNT: "3",
        "transition": "1",
        "change_frequency": "1",
        CONF_BRIGHTNESS: "255",
        CONF_COLORS: [{"color_type": "rgb_color", "color": [255, 0, 0]}],
    }


def test_normalize_scene_input_clamps_change_amount_to_all() -> None:
    """Normalize change_amount larger than selected lights to all."""
    result = normalize_scene_input(_base_input())

    assert result[CONF_CHANGE_AMOUNT] == "all"


def test_normalize_scene_input_adds_defaults() -> None:
    """Add integration defaults exactly once in shared normalization."""
    result = normalize_scene_input(_base_input())

    assert result["animate_brightness"] is DEFAULT_ANIMATE_BRIGHTNESS
    assert result["animate_color"] is DEFAULT_ANIMATE_COLOR
    assert result["change_sequence"] is DEFAULT_CHANGE_SEQUENCE
    assert result["ignore_off"] is DEFAULT_IGNORE_OFF
    assert result["priority"] == DEFAULT_PRIORITY
    assert result["restore"] is DEFAULT_RESTORE
    assert result["restore_power"] is DEFAULT_RESTORE_POWER


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (CONF_CHANGE_AMOUNT, "bad", "change_amount_not_int_or_all"),
        ("transition", "[1, bad]", "transition_not_int_or_range"),
        ("change_frequency", "61", "change_frequency_not_int_or_range"),
        (CONF_BRIGHTNESS, "300", "brightness_not_int_or_range"),
    ],
)
def test_normalize_scene_input_reports_specific_errors(
    field: str, value: object, message: str
) -> None:
    """Return the same error keys used by config and options flows."""
    data = _base_input()
    data[field] = value

    with pytest.raises(vol.Invalid, match=message):
        normalize_scene_input(data)


def test_validate_start_service_data_accepts_normalized_scene_data() -> None:
    """Validate start service data through the shared runtime schema."""
    result = validate_start_service_data(normalize_scene_input(_base_input()))

    assert result[CONF_NAME] == "Spooky"
    assert result[CONF_CHANGE_AMOUNT] == "all"


def test_build_colors_from_rgb_dict_converts_to_color_list() -> None:
    """Convert config-flow RGB UI storage into runtime colors."""
    result = build_colors_from_rgb_dict(
        {
            "one": {"color": [1, 2, 3], "brightness": 200, "weight": 10},
            "two": {"color": [4, 5, 6], "brightness": [100, 255], "weight": 5},
        }
    )

    assert result == [
        {"color": [1, 2, 3], "brightness": 200, "weight": 10, "color_type": CONF_COLOR_RGB},
        {
            "color": [4, 5, 6],
            "brightness": [100, 255],
            "weight": 5,
            "color_type": CONF_COLOR_RGB,
        },
    ]
