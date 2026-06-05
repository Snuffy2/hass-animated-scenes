"""Regression tests for scene configuration normalization."""

from __future__ import annotations

from custom_components.animated_scenes.const import CONF_CHANGE_AMOUNT
from custom_components.animated_scenes.scene_config import normalize_scene_input

try:
    from custom_components.animated_scenes.const import CONF_LIGHTS
except ImportError:  # pragma: no cover - compatibility with current branch state.
    CONF_LIGHTS = "lights"


def test_normalize_scene_input_clamps_change_amount_to_all() -> None:
    """Preserve the shared contract for unlimited scene change amounts."""

    normalized = normalize_scene_input(
        {
            "name": "Spooky",
            CONF_LIGHTS: ["light.one", "light.two"],
            CONF_CHANGE_AMOUNT: "3",
            "transition": "1",
            "change_frequency": "1",
            "brightness": "255",
        }
    )

    assert normalized[CONF_CHANGE_AMOUNT] == "all"
