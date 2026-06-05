"""Regression tests for scene configuration normalization."""

from custom_components.animated_scenes.const import (
    CONF_CHANGE_AMOUNT,
    DEFAULT_CHANGE_AMOUNT,
)
from custom_components.animated_scenes.scene_config import normalize_scene_input


def test_normalize_scene_input_clamps_change_amount_to_all() -> None:
    """Preserve the shared contract for unlimited scene change amounts."""

    normalized = normalize_scene_input({CONF_CHANGE_AMOUNT: "999"})

    assert normalized[CONF_CHANGE_AMOUNT] == DEFAULT_CHANGE_AMOUNT
