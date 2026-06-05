"""Shared scene configuration normalization for Animated Scenes."""

from __future__ import annotations

import copy
from typing import Any

from homeassistant.components.light import (
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_XY_COLOR,
    VALID_TRANSITION,
)
from homeassistant.const import CONF_BRIGHTNESS, CONF_LIGHTS, CONF_NAME
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    ATTR_COLOR_TEMP,
    BRIGHTNESS_MAX,
    BRIGHTNESS_MIN,
    CHANGE_AMOUNT_MAX,
    CHANGE_AMOUNT_MIN,
    CHANGE_FREQUENCY_MAX,
    CHANGE_FREQUENCY_MIN,
    CONF_ANIMATE_BRIGHTNESS,
    CONF_ANIMATE_COLOR,
    CONF_ANIMATED_SCENE_SWITCH,
    CONF_CHANGE_AMOUNT,
    CONF_CHANGE_FREQUENCY,
    CONF_CHANGE_SEQUENCE,
    CONF_COLOR,
    CONF_COLOR_ADD_COLOR,
    CONF_COLOR_DELETE_COLOR,
    CONF_COLOR_NEARBY_COLORS,
    CONF_COLOR_ONE_CHANGE_PER_TICK,
    CONF_COLOR_RGB,
    CONF_COLOR_TYPE,
    CONF_COLOR_WEIGHT,
    CONF_COLORS,
    CONF_IGNORE_OFF,
    CONF_PRIORITY,
    CONF_RESTORE,
    CONF_RESTORE_POWER,
    CONF_SKIP_RESTORE,
    CONF_TRANSITION,
    DEFAULT_ANIMATE_BRIGHTNESS,
    DEFAULT_ANIMATE_COLOR,
    DEFAULT_BRIGHTNESS,
    DEFAULT_CHANGE_AMOUNT,
    DEFAULT_CHANGE_FREQUENCY,
    DEFAULT_CHANGE_SEQUENCE,
    DEFAULT_COLOR_NEARBY_COLORS,
    DEFAULT_COLOR_ONE_CHANGE_PER_TICK,
    DEFAULT_COLOR_WEIGHT,
    DEFAULT_IGNORE_OFF,
    DEFAULT_PRIORITY,
    DEFAULT_RESTORE,
    DEFAULT_RESTORE_POWER,
    DEFAULT_TRANSITION,
    ERROR_BRIGHTNESS_NOT_INT_OR_RANGE,
    ERROR_CHANGE_AMOUNT_NOT_INT_OR_ALL,
    ERROR_CHANGE_FREQUENCY_NOT_INT_OR_RANGE,
    ERROR_MUST_SELECT_LIGHTS,
    ERROR_TRANSITION_NOT_INT_OR_RANGE,
    TRANSITION_MAX,
    TRANSITION_MIN,
)

SCENE_DEFAULTS: dict[str, Any] = {
    CONF_BRIGHTNESS: DEFAULT_BRIGHTNESS,
    CONF_ANIMATE_BRIGHTNESS: DEFAULT_ANIMATE_BRIGHTNESS,
    CONF_ANIMATE_COLOR: DEFAULT_ANIMATE_COLOR,
    CONF_CHANGE_AMOUNT: DEFAULT_CHANGE_AMOUNT,
    CONF_CHANGE_FREQUENCY: DEFAULT_CHANGE_FREQUENCY,
    CONF_CHANGE_SEQUENCE: DEFAULT_CHANGE_SEQUENCE,
    CONF_RESTORE: DEFAULT_RESTORE,
    CONF_RESTORE_POWER: DEFAULT_RESTORE_POWER,
    CONF_IGNORE_OFF: DEFAULT_IGNORE_OFF,
    CONF_TRANSITION: DEFAULT_TRANSITION,
    CONF_PRIORITY: DEFAULT_PRIORITY,
}

COLOR_GROUP_SCHEMA = {
    vol.Optional(CONF_BRIGHTNESS, default=DEFAULT_BRIGHTNESS): vol.Any(
        vol.Range(min=BRIGHTNESS_MIN, max=BRIGHTNESS_MAX),
        vol.All([vol.Range(min=BRIGHTNESS_MIN, max=BRIGHTNESS_MAX)]),
    ),
    vol.Optional(CONF_COLOR_WEIGHT, default=DEFAULT_COLOR_WEIGHT): vol.Range(min=0, max=255),
    vol.Optional(CONF_COLOR_ONE_CHANGE_PER_TICK, default=DEFAULT_COLOR_ONE_CHANGE_PER_TICK): bool,
    vol.Optional(
        CONF_COLOR_NEARBY_COLORS,
        default=DEFAULT_COLOR_NEARBY_COLORS,
    ): vol.Range(min=0, max=10),
}

START_SERVICE_CONFIG = {
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_IGNORE_OFF, default=DEFAULT_IGNORE_OFF): bool,
    vol.Optional(CONF_RESTORE, default=DEFAULT_RESTORE): bool,
    vol.Optional(CONF_RESTORE_POWER, default=DEFAULT_RESTORE_POWER): bool,
    vol.Optional(CONF_BRIGHTNESS, default=DEFAULT_BRIGHTNESS): vol.Any(
        vol.Range(min=BRIGHTNESS_MIN, max=BRIGHTNESS_MAX),
        vol.All([vol.Range(min=BRIGHTNESS_MIN, max=BRIGHTNESS_MAX)]),
    ),
    vol.Optional(CONF_TRANSITION, default=DEFAULT_TRANSITION): vol.Any(
        VALID_TRANSITION,
        vol.All([VALID_TRANSITION]),
    ),
    vol.Optional(CONF_CHANGE_FREQUENCY, default=DEFAULT_CHANGE_FREQUENCY): vol.Any(
        vol.All(vol.Coerce(float), vol.Range(min=CHANGE_FREQUENCY_MIN, max=CHANGE_FREQUENCY_MAX)),
        vol.All(
            [
                vol.All(
                    vol.Coerce(float),
                    vol.Range(min=CHANGE_FREQUENCY_MIN, max=CHANGE_FREQUENCY_MAX),
                )
            ]
        ),
    ),
    vol.Optional(CONF_CHANGE_AMOUNT, default=DEFAULT_CHANGE_AMOUNT): vol.Any(
        "all",
        vol.All(vol.Coerce(int), vol.Range(min=CHANGE_AMOUNT_MIN, max=CHANGE_AMOUNT_MAX)),
        vol.All(
            [vol.All(vol.Coerce(int), vol.Range(min=CHANGE_AMOUNT_MIN, max=CHANGE_AMOUNT_MAX))]
        ),
    ),
    vol.Optional(CONF_CHANGE_SEQUENCE, default=DEFAULT_CHANGE_SEQUENCE): bool,
    vol.Optional(CONF_ANIMATE_BRIGHTNESS, default=DEFAULT_ANIMATE_BRIGHTNESS): bool,
    vol.Optional(CONF_ANIMATE_COLOR, default=DEFAULT_ANIMATE_COLOR): bool,
    vol.Optional(CONF_PRIORITY, default=DEFAULT_PRIORITY): int,
    vol.Required(CONF_LIGHTS): cv.entity_ids,
    vol.Optional(CONF_COLORS, default=[]): vol.All(
        cv.ensure_list,
        [
            vol.Any(
                vol.Schema(
                    {
                        vol.Required(CONF_COLOR_TYPE): ATTR_RGB_COLOR,
                        vol.Required(CONF_COLOR): vol.All(
                            vol.Coerce(tuple), vol.ExactSequence((cv.byte,) * 3)
                        ),
                    }
                ).extend(COLOR_GROUP_SCHEMA),
                vol.Schema(
                    {
                        vol.Required(CONF_COLOR_TYPE): ATTR_RGBW_COLOR,
                        vol.Required(CONF_COLOR): vol.All(
                            vol.Coerce(tuple), vol.ExactSequence((cv.byte,) * 4)
                        ),
                    }
                ).extend(COLOR_GROUP_SCHEMA),
                vol.Schema(
                    {
                        vol.Required(CONF_COLOR_TYPE): ATTR_RGBWW_COLOR,
                        vol.Required(CONF_COLOR): vol.All(
                            vol.Coerce(tuple), vol.ExactSequence((cv.byte,) * 5)
                        ),
                    }
                ).extend(COLOR_GROUP_SCHEMA),
                vol.Schema(
                    {
                        vol.Required(CONF_COLOR_TYPE): ATTR_XY_COLOR,
                        vol.Required(CONF_COLOR): vol.All(
                            vol.Coerce(tuple),
                            vol.ExactSequence((cv.small_float, cv.small_float)),
                        ),
                    }
                ).extend(COLOR_GROUP_SCHEMA),
                vol.Schema(
                    {
                        vol.Required(CONF_COLOR_TYPE): ATTR_HS_COLOR,
                        vol.Required(CONF_COLOR): vol.All(
                            vol.Coerce(tuple),
                            vol.ExactSequence(
                                (
                                    vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
                                    vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
                                )
                            ),
                        ),
                    }
                ).extend(COLOR_GROUP_SCHEMA),
                vol.Schema(
                    {
                        vol.Required(CONF_COLOR_TYPE): ATTR_COLOR_TEMP,
                        vol.Required(CONF_COLOR): vol.All(vol.Coerce(int), vol.Range(min=1)),
                    }
                ).extend(COLOR_GROUP_SCHEMA),
                vol.Schema(
                    {
                        vol.Required(CONF_COLOR_TYPE): ATTR_COLOR_TEMP_KELVIN,
                        vol.Required(CONF_COLOR): cv.positive_int,
                    }
                ).extend(COLOR_GROUP_SCHEMA),
            )
        ],
    ),
}

START_SERVICE_SCHEMA = vol.Schema(START_SERVICE_CONFIG)
STOP_SERVICE_SCHEMA = vol.Schema({vol.Required(CONF_NAME): cv.string})
ADD_LIGHTS_TO_ANIMATION_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LIGHTS): cv.entity_ids,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ANIMATED_SCENE_SWITCH): cv.entity_id,
    }
)
REMOVE_LIGHTS_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LIGHTS): cv.entity_ids,
        vol.Optional(CONF_SKIP_RESTORE, default=False): bool,
    }
)


def is_int(value: Any) -> tuple[bool, Any]:
    """Return whether value is integer-like and its normalized value."""
    if value is None or not isinstance(value, int | float | str):
        return False, value
    try:
        parsed = float(value)
    except TypeError, ValueError:
        return False, value
    if parsed.is_integer():
        return True, int(parsed)
    return False, value


def list_or_int_to_str(value: Any) -> Any:
    """Return a UI string representation for an int or two-item list."""
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    is_int_check, is_int_value = is_int(value)
    if is_int_check:
        return str(is_int_value)
    return value


def _strlist_to_list(value: str) -> list[str]:
    """Convert a bracketed comma-separated string into a two-item list."""
    return value.strip("][").split(",")


def is_int_or_list(
    value: Any, min_value: int | None = None, max_value: int | None = None
) -> tuple[bool, Any]:
    """Validate and normalize an int or two-item integer range."""
    if value is None:
        return True, value
    is_int_check, is_int_value = is_int(value)
    if is_int_check:
        if (min_value is None or is_int_value >= min_value) and (
            max_value is None or is_int_value <= max_value
        ):
            return True, is_int_value
        return False, value
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("[") and value.endswith("]") and value.count(",") == 1:
            value = _strlist_to_list(value)
        else:
            return False, value
    if isinstance(value, list) and len(value) == 2:
        is_first, first = is_int(value[0])
        is_second, second = is_int(value[1])
        if not (is_first and is_second):
            return False, value
        normalized = [min(first, second), max(first, second)]
        if (min_value is None or min(normalized) >= min_value) and (
            max_value is None or max(normalized) <= max_value
        ):
            if normalized[0] == normalized[1]:
                return True, normalized[0]
            return True, normalized
    return False, value


def is_number(value: Any) -> tuple[bool, Any]:
    """Return whether value is numeric and its normalized value."""
    if value is None or not isinstance(value, int | float | str):
        return False, value
    try:
        parsed = float(value)
    except TypeError, ValueError:
        return False, value
    if parsed.is_integer():
        return True, int(parsed)
    return True, parsed


def is_number_or_list(
    value: Any, min_value: float | None = None, max_value: float | None = None
) -> tuple[bool, Any]:
    """Validate and normalize a number or two-item numeric range."""
    if value is None:
        return True, value
    is_number_check, number_value = is_number(value)
    if is_number_check:
        if (min_value is None or number_value >= min_value) and (
            max_value is None or number_value <= max_value
        ):
            return True, number_value
        return False, value
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("[") and value.endswith("]") and value.count(",") == 1:
            value = _strlist_to_list(value)
        else:
            return False, value
    if isinstance(value, list) and len(value) == 2:
        is_first, first = is_number(value[0])
        is_second, second = is_number(value[1])
        if not (is_first and is_second):
            return False, value
        normalized = [min(first, second), max(first, second)]
        if (min_value is None or min(normalized) >= min_value) and (
            max_value is None or max(normalized) <= max_value
        ):
            if normalized[0] == normalized[1]:
                return True, normalized[0]
            return True, normalized
    return False, value


def is_int_list_or_all(
    value: Any, min_value: int | None = None, max_value: int | None = None
) -> tuple[bool, Any]:
    """Validate and normalize an int, two-item integer range, or all."""
    is_valid, normalized = is_int_or_list(value, min_value, max_value)
    if is_valid:
        return True, normalized
    if isinstance(value, str) and value.strip() == "all":
        return True, "all"
    return False, value


def override_max_change_amount(value: Any, light_count: int) -> Any:
    """Clamp change_amount to the selected light count."""
    if isinstance(value, int) and value > light_count:
        return "all"
    if isinstance(value, list) and value[1] > light_count:
        if value[0] >= light_count:
            return "all"
        value[1] = light_count
    return value


def normalize_scene_input(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize config-flow or service scene data and raise vol.Invalid on errors."""
    normalized = dict(data)
    for key, default in SCENE_DEFAULTS.items():
        normalized.setdefault(key, default)

    if len(normalized.get(CONF_LIGHTS, [])) == 0:
        raise vol.Invalid(ERROR_MUST_SELECT_LIGHTS)

    change_ok, change_value = is_int_list_or_all(
        normalized.get(CONF_CHANGE_AMOUNT), CHANGE_AMOUNT_MIN, CHANGE_AMOUNT_MAX
    )
    if not change_ok:
        raise vol.Invalid(ERROR_CHANGE_AMOUNT_NOT_INT_OR_ALL)
    normalized[CONF_CHANGE_AMOUNT] = override_max_change_amount(
        change_value, len(normalized.get(CONF_LIGHTS, []))
    )

    transition_ok, transition_value = is_number_or_list(
        normalized.get(CONF_TRANSITION), TRANSITION_MIN, TRANSITION_MAX
    )
    if not transition_ok:
        raise vol.Invalid(ERROR_TRANSITION_NOT_INT_OR_RANGE)
    normalized[CONF_TRANSITION] = transition_value

    frequency_ok, frequency_value = is_number_or_list(
        normalized.get(CONF_CHANGE_FREQUENCY), CHANGE_FREQUENCY_MIN, CHANGE_FREQUENCY_MAX
    )
    if not frequency_ok:
        raise vol.Invalid(ERROR_CHANGE_FREQUENCY_NOT_INT_OR_RANGE)
    normalized[CONF_CHANGE_FREQUENCY] = frequency_value

    brightness_ok, brightness_value = is_int_or_list(
        normalized.get(CONF_BRIGHTNESS), BRIGHTNESS_MIN, BRIGHTNESS_MAX
    )
    if not brightness_ok:
        raise vol.Invalid(ERROR_BRIGHTNESS_NOT_INT_OR_RANGE)
    normalized[CONF_BRIGHTNESS] = brightness_value
    normalized[CONF_PRIORITY] = round(normalized.get(CONF_PRIORITY, DEFAULT_PRIORITY))
    return normalized


def clean_color_rgb_dict(color_rgb_dict: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Remove RGB UI-only helper keys from stored color data."""
    cleaned = copy.deepcopy(color_rgb_dict)
    for key, color in list(cleaned.items()):
        cleaned[key].pop(CONF_COLOR_ADD_COLOR, None)
        if color.get(CONF_COLOR_DELETE_COLOR, False):
            cleaned.pop(key, None)
        else:
            cleaned[key].pop(CONF_COLOR_DELETE_COLOR, None)
    return cleaned


def build_colors_from_rgb_dict(color_rgb_dict: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert RGB UI storage into the runtime colors list."""
    color_list = list(copy.deepcopy(color_rgb_dict).values())
    for color in color_list:
        color[CONF_COLOR_TYPE] = CONF_COLOR_RGB
    return color_list


def validate_start_service_data(data: dict[str, Any]) -> dict[str, Any]:
    """Validate runtime start service data."""
    return START_SERVICE_SCHEMA(dict(data))
