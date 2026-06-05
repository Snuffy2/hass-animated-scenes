"""Regression tests for scene configuration normalization."""

from __future__ import annotations

from homeassistant.const import CONF_BRIGHTNESS, CONF_LIGHTS, CONF_NAME

from custom_components.animated_scenes.const import CONF_CHANGE_AMOUNT
from custom_components.animated_scenes.scene_config import normalize_scene_input


def test_normalize_scene_input_clamps_change_amount_to_all() -> None:
    """Preserve the shared contract for unlimited scene change amounts."""

    normalized = normalize_scene_input(
        {
            CONF_NAME: "Scene",
            CONF_LIGHTS: ["light.one", "light.two"],
            CONF_CHANGE_AMOUNT: "3",
            "transition": "1",
            "change_frequency": "1",
            CONF_BRIGHTNESS: "255",
        }
    )

    assert normalized[CONF_CHANGE_AMOUNT] == "all"
