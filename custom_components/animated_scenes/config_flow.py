"""Config flow for the Animated Scenes integration.

This module implements the config and options flows used by Home
Assistant to configure Animated Scenes. It includes small helper
functions used to parse and validate user input from the UI.
"""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_BRIGHTNESS, CONF_ICON, CONF_LIGHTS, CONF_NAME, Platform
from homeassistant.core import callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
from homeassistant.util import uuid

from .const import (
    ABORT_ACTIVITY_SENSOR_NO_OPTIONS,
    ABORT_INTEGRATION_NO_OPTIONS,
    BRIGHTNESS_MAX,
    BRIGHTNESS_MIN,
    COLOR_SELECTOR_RGB_UI,
    COLOR_SELECTOR_YAML,
    COMPONENT_COLOR_CONFIG_URL,
    CONF_ANIMATE_BRIGHTNESS,
    CONF_ANIMATE_COLOR,
    CONF_CHANGE_AMOUNT,
    CONF_CHANGE_FREQUENCY,
    CONF_CHANGE_SEQUENCE,
    CONF_COLOR,
    CONF_COLOR_ADD_COLOR,
    CONF_COLOR_DELETE_COLOR,
    CONF_COLOR_NEARBY_COLORS,
    CONF_COLOR_ONE_CHANGE_PER_TICK,
    CONF_COLOR_RGB_DICT,
    CONF_COLOR_SELECTOR_MODE,
    CONF_COLOR_WEIGHT,
    CONF_COLORS,
    CONF_ENTITY_TYPE,
    CONF_IGNORE_OFF,
    CONF_PRIORITY,
    CONF_RESTORE,
    CONF_RESTORE_POWER,
    CONF_TRANSITION,
    DEFAULT_ANIMATE_BRIGHTNESS,
    DEFAULT_ANIMATE_COLOR,
    DEFAULT_BRIGHTNESS,
    DEFAULT_CHANGE_AMOUNT,
    DEFAULT_CHANGE_FREQUENCY,
    DEFAULT_CHANGE_SEQUENCE,
    DEFAULT_COLOR_ADD_COLOR,
    DEFAULT_COLOR_DELETE_COLOR,
    DEFAULT_COLOR_NEARBY_COLORS,
    DEFAULT_COLOR_ONE_CHANGE_PER_TICK,
    DEFAULT_COLOR_WEIGHT,
    DEFAULT_ICON,
    DEFAULT_IGNORE_OFF,
    DEFAULT_PRIORITY,
    DEFAULT_RESTORE,
    DEFAULT_RESTORE_POWER,
    DEFAULT_TRANSITION,
    DOMAIN,
    ENTITY_ACTIVITY_SENSOR,
    ENTITY_SCENE,
    ERROR_BRIGHTNESS_NOT_INT_OR_RANGE,
    ERROR_COLORS_IS_BLANK,
    ERROR_COLORS_MALFORMED,
)

from .scene_config import (
    clean_color_rgb_dict,
    is_int_or_list,
    list_or_int_to_str,
    normalize_scene_input,
)

_LOGGER: logging.Logger = logging.getLogger(__name__)
COLOR_SELECTOR_OPTION_LIST = [
    selector.SelectOptionDict(label="Use RGB Selectors", value=COLOR_SELECTOR_RGB_UI),
    selector.SelectOptionDict(label="Configure via YAML", value=COLOR_SELECTOR_YAML),
]


async def _async_build_schema(
    user_input: dict[str, Any] | None,
    default_dict: dict[str, Any],
    options_flow: bool = False,
) -> vol.Schema:
    """Build a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> Any:
        """Get default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    build_schema = vol.Schema({})
    if not options_flow:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_NAME,
                    default=_get_default(CONF_NAME),
                ): selector.TextSelector(selector.TextSelectorConfig()),
                vol.Optional(
                    CONF_ICON, default=_get_default(CONF_ICON, DEFAULT_ICON)
                ): selector.IconSelector(selector.IconSelectorConfig()),
            }
        )
    build_schema = build_schema.extend(
        {
            vol.Optional(
                CONF_PRIORITY, default=_get_default(CONF_PRIORITY, DEFAULT_PRIORITY)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=-100,
                    max=100,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                CONF_CHANGE_FREQUENCY,
                default=list_or_int_to_str(
                    _get_default(CONF_CHANGE_FREQUENCY, DEFAULT_CHANGE_FREQUENCY)
                ),
            ): selector.TextSelector(selector.TextSelectorConfig()),
            vol.Optional(
                CONF_TRANSITION,
                default=list_or_int_to_str(_get_default(CONF_TRANSITION, DEFAULT_TRANSITION)),
            ): selector.TextSelector(selector.TextSelectorConfig()),
            vol.Optional(
                CONF_CHANGE_AMOUNT,
                default=list_or_int_to_str(
                    _get_default(CONF_CHANGE_AMOUNT, DEFAULT_CHANGE_AMOUNT)
                ),
            ): selector.TextSelector(selector.TextSelectorConfig()),
            vol.Optional(
                CONF_BRIGHTNESS,
                default=list_or_int_to_str(_get_default(CONF_BRIGHTNESS, DEFAULT_BRIGHTNESS)),
            ): selector.TextSelector(selector.TextSelectorConfig()),
            vol.Optional(
                CONF_CHANGE_SEQUENCE,
                default=_get_default(CONF_CHANGE_SEQUENCE, DEFAULT_CHANGE_SEQUENCE),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            vol.Optional(
                CONF_ANIMATE_BRIGHTNESS,
                default=_get_default(CONF_ANIMATE_BRIGHTNESS, DEFAULT_ANIMATE_BRIGHTNESS),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            vol.Optional(
                CONF_ANIMATE_COLOR,
                default=_get_default(CONF_ANIMATE_COLOR, DEFAULT_ANIMATE_COLOR),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            vol.Optional(
                CONF_IGNORE_OFF,
                default=_get_default(CONF_IGNORE_OFF, DEFAULT_IGNORE_OFF),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            vol.Optional(
                CONF_RESTORE, default=_get_default(CONF_RESTORE, DEFAULT_RESTORE)
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            vol.Optional(
                CONF_RESTORE_POWER,
                default=_get_default(CONF_RESTORE_POWER, DEFAULT_RESTORE_POWER),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            vol.Required(
                CONF_LIGHTS, default=_get_default(CONF_LIGHTS, [])
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=[Platform.LIGHT], multiple=True),
            ),
        }
    )

    return build_schema.extend(
        {
            vol.Required(
                CONF_COLOR_SELECTOR_MODE, default=_get_default(CONF_COLOR_SELECTOR_MODE, "")
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=COLOR_SELECTOR_OPTION_LIST,
                    multiple=False,
                    custom_value=False,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
        }
    )


async def _async_build_color_yaml_schema(
    user_input: dict[str, Any] | None, default_dict: dict[str, Any]
) -> vol.Schema:
    """Build a color YAML schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> Any:
        """Get default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    build_schema = vol.Schema({})

    if _get_default(CONF_COLORS) is None or _get_default(CONF_COLORS) == {}:
        build_schema = build_schema.extend(
            {
                vol.Required(CONF_COLORS): selector.ObjectSelector(),
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_COLORS, default=_get_default(CONF_COLORS)
                ): selector.ObjectSelector(),
            }
        )

    return build_schema


async def _async_build_color_rgb_ui_schema(
    user_input: dict[str, Any] | None,
    default_dict: dict[str, Any],
    options_flow: bool = False,
    is_last_color: bool = False,
) -> vol.Schema:
    """Build a color RGB UI schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> Any:
        """Get default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    build_schema = vol.Schema(
        {
            vol.Optional(CONF_COLOR, default=_get_default(CONF_COLOR)): selector.ColorRGBSelector(
                selector.ColorRGBSelectorConfig()
            ),
            vol.Optional(
                CONF_BRIGHTNESS,
                default=list_or_int_to_str(_get_default(CONF_BRIGHTNESS, DEFAULT_BRIGHTNESS)),
            ): selector.TextSelector(selector.TextSelectorConfig()),
            vol.Optional(
                CONF_COLOR_WEIGHT,
                default=_get_default(CONF_COLOR_WEIGHT, DEFAULT_COLOR_WEIGHT),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=255,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                CONF_COLOR_ONE_CHANGE_PER_TICK,
                default=_get_default(
                    CONF_COLOR_ONE_CHANGE_PER_TICK, DEFAULT_COLOR_ONE_CHANGE_PER_TICK
                ),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            vol.Optional(
                CONF_COLOR_NEARBY_COLORS,
                default=_get_default(CONF_COLOR_NEARBY_COLORS, DEFAULT_COLOR_NEARBY_COLORS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=10,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )
    if not options_flow or is_last_color:
        build_schema = build_schema.extend(
            {
                vol.Optional(
                    CONF_COLOR_ADD_COLOR,
                    default=_get_default(CONF_COLOR_ADD_COLOR, DEFAULT_COLOR_ADD_COLOR),
                ): cv.boolean,
            }
        )

    if options_flow:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_COLOR_DELETE_COLOR,
                    default=_get_default(CONF_COLOR_DELETE_COLOR, DEFAULT_COLOR_DELETE_COLOR),
                ): cv.boolean,
            }
        )

    return build_schema


class AnimatedScenesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial configuration flow for Animated Scenes.

    This class implements the steps shown to the user when creating an
    instance of the integration via the UI or importing YAML.
    """

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._data: dict[str, Any] = {}
        self._data[CONF_COLOR_RGB_DICT] = {}
        self._data[CONF_COLORS] = {}
        self._entry = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step.

        Presents a menu to choose between creating an activity sensor or
        a scene entry, depending on whether an activity sensor already
        exists.
        """
        activity_sensor_exists = False
        if DOMAIN in self.hass.data:
            for entity in self.hass.data[DOMAIN].values():
                if entity.get(CONF_ENTITY_TYPE, ENTITY_SCENE) == ENTITY_ACTIVITY_SENSOR:
                    activity_sensor_exists = True
                    break
        if activity_sensor_exists:
            return await self.async_step_scene(user_input=user_input)
        return self.async_show_menu(
            step_id="user",
            menu_options=["activity_sensor", "scene"],
        )

    async def async_step_activity_sensor(self, _: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Create an activity sensor config entry immediately."""
        self._data.update({CONF_NAME: "Activity Sensor", CONF_ENTITY_TYPE: ENTITY_ACTIVITY_SENSOR})
        # _LOGGER.debug(f"[async_step_activity_sensor] self._data: {self._data}")
        return self.async_create_entry(title="Activity Sensor", data=self._data)

    async def async_step_scene(
        self, user_input: dict[str, Any] | None = None, yaml_import: bool = False
    ) -> ConfigFlowResult:
        """Handle the scene creation step.

        Validates and normalizes user input before continuing to color
        configuration steps or creating the config entry.
        """

        errors: dict[str, Any] = {}

        # Defaults
        defaults = {
            CONF_ICON: DEFAULT_ICON,
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

        if user_input is not None:
            self._data.update(user_input)
            self._data.update({CONF_ENTITY_TYPE: ENTITY_SCENE})
            try:
                self._data = normalize_scene_input(self._data)
            except vol.Invalid as err:
                errors["base"] = str(err)
            for k, v in defaults.items():
                self._data.setdefault(k, v)
            # _LOGGER.debug(f"[async_step_scene] self._data: {self._data}")
            if not errors:
                if yaml_import:
                    self._data.update({CONF_COLOR_SELECTOR_MODE: COLOR_SELECTOR_YAML})
                    return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
                if (
                    self._data.get(CONF_COLOR_SELECTOR_MODE, COLOR_SELECTOR_RGB_UI)
                    == COLOR_SELECTOR_RGB_UI
                ):
                    return await self.async_step_color_rgb_ui()
                return await self.async_step_color_yaml()

        return self.async_show_form(
            step_id="scene",
            data_schema=await _async_build_schema(user_input, defaults),
            errors=errors,
        )

    async def async_step_color_yaml(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle color configuration when the user chooses YAML input."""
        errors: dict[str, Any] = {}

        # Defaults
        defaults: dict[str, Any] = {}

        if user_input is not None:
            self._data.update(user_input)
            if self._data.get(CONF_COLORS) is None or self._data.get(CONF_COLORS) == {}:
                errors["base"] = ERROR_COLORS_IS_BLANK
            if not isinstance(self._data.get(CONF_COLORS), list):
                errors["base"] = ERROR_COLORS_MALFORMED
            for k, v in defaults.items():
                self._data.setdefault(k, v)
            # _LOGGER.debug(f"[async_step_color_yaml] self._data: {self._data}")
            if not errors:
                return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
        return self.async_show_form(
            step_id="color_yaml",
            data_schema=await _async_build_color_yaml_schema(user_input, defaults),
            errors=errors,
            description_placeholders={
                "component_color_config_url": COMPONENT_COLOR_CONFIG_URL,
            },
        )

    async def async_step_color_rgb_ui(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle color configuration when the user uses the RGB UI selectors."""
        errors: dict[str, Any] = {}

        # Defaults
        defaults = {
            CONF_BRIGHTNESS: DEFAULT_BRIGHTNESS,
            CONF_COLOR_NEARBY_COLORS: DEFAULT_COLOR_NEARBY_COLORS,
            CONF_COLOR_ONE_CHANGE_PER_TICK: DEFAULT_COLOR_ONE_CHANGE_PER_TICK,
            CONF_COLOR_WEIGHT: DEFAULT_COLOR_WEIGHT,
            CONF_COLOR_ADD_COLOR: DEFAULT_COLOR_ADD_COLOR,
            CONF_COLOR_DELETE_COLOR: DEFAULT_COLOR_DELETE_COLOR,
        }

        if user_input is not None:
            _LOGGER.debug(
                "Checking Brightnes: %s, type: %s",
                user_input.get(CONF_BRIGHTNESS),
                type(user_input.get(CONF_BRIGHTNESS)),
            )
            brightness_check, brightness_value = is_int_or_list(
                user_input.get(CONF_BRIGHTNESS),
                BRIGHTNESS_MIN,
                BRIGHTNESS_MAX,
            )
            if brightness_check:
                user_input.update({CONF_BRIGHTNESS: brightness_value})
            else:
                errors["base"] = ERROR_BRIGHTNESS_NOT_INT_OR_RANGE
            user_input.update(
                {CONF_COLOR_WEIGHT: round(user_input.get(CONF_COLOR_WEIGHT, DEFAULT_COLOR_WEIGHT))}
            )
            user_input.update(
                {
                    CONF_COLOR_NEARBY_COLORS: round(
                        user_input.get(CONF_COLOR_NEARBY_COLORS, DEFAULT_COLOR_NEARBY_COLORS)
                    )
                }
            )
            for k, v in defaults.items():
                user_input.setdefault(k, v)
            if not errors:
                color_uuid = uuid.random_uuid_hex()
                self._data.get(CONF_COLOR_RGB_DICT, {}).update({color_uuid: user_input})
                # _LOGGER.debug(f"[async_step_color_rgb_ui] self._data: {self._data}")
                if user_input.get(CONF_COLOR_ADD_COLOR, False):
                    return await self.async_step_color_rgb_ui()
                self._data.update(
                    {
                        CONF_COLOR_RGB_DICT: clean_color_rgb_dict(
                            self._data.get(CONF_COLOR_RGB_DICT, {})
                        )
                    }
                )
                return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
            # _LOGGER.debug(f"[async_step_color_rgb_ui] user_input: {user_input}")

        return self.async_show_form(
            step_id="color_rgb_ui",
            data_schema=await _async_build_color_rgb_ui_schema(user_input, defaults),
            errors=errors,
            description_placeholders={
                "color_count": str(len(self._data.get(CONF_COLOR_RGB_DICT, {})) + 1),
            },
        )

    async def async_step_import(
        self, import_config: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Import a config entry from configuration.yaml."""
        if import_config:
            import_config.update({CONF_ENTITY_TYPE: ENTITY_SCENE})
            _LOGGER.debug("[async_step_import] import_config: %s", import_config)
        return await self.async_step_scene(user_input=import_config, yaml_import=True)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Options callback."""
        return AnimatedScenesOptionsFlowHandler(config_entry)


class AnimatedScenesOptionsFlowHandler(OptionsFlow):
    """Config flow options. Does not actually store these into Options but updates the Config instead."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.config = config_entry
        self._data = dict(config_entry.data)
        rgb_dict = self._data.get(CONF_COLOR_RGB_DICT)
        if rgb_dict:
            self._rgb_ui_color_keys = list(self._data.get(CONF_COLOR_RGB_DICT, {}).keys())
            self._rgb_ui_color_values = list(self._data.get(CONF_COLOR_RGB_DICT, {}).values())
            self._rgb_ui_color_max = len(self._rgb_ui_color_keys)
        self._rgb_ui_color_index = 0

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the options."""

        if self._data.get(CONF_ENTITY_TYPE, ENTITY_SCENE) == ENTITY_ACTIVITY_SENSOR:
            return self.async_abort(reason=ABORT_ACTIVITY_SENSOR_NO_OPTIONS)
        if self._data.get(CONF_ENTITY_TYPE) is None:
            return self.async_abort(reason=ABORT_INTEGRATION_NO_OPTIONS)
        return await self.async_step_scene(user_input=user_input)

    async def async_step_scene(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the scene options step in the options flow.

        Validate and normalize the provided options and either proceed to
        color configuration steps or update the entry data.
        """

        errors: dict[str, Any] = {}

        # Defaults
        defaults = {
            CONF_ICON: DEFAULT_ICON,
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

        if user_input is not None:
            self._data.update(user_input)
            self._data.update({CONF_ENTITY_TYPE: ENTITY_SCENE})
            try:
                self._data = normalize_scene_input(self._data)
            except vol.Invalid as err:
                errors["base"] = str(err)
            for k, v in defaults.items():
                self._data.setdefault(k, v)
            # _LOGGER.debug(f"[async_init_user] self._data: {self._data}")
            if not errors:
                if (
                    self._data.get(CONF_COLOR_SELECTOR_MODE, COLOR_SELECTOR_RGB_UI)
                    == COLOR_SELECTOR_RGB_UI
                ):
                    return await self.async_step_color_rgb_ui()
                return await self.async_step_color_yaml()

        return self.async_show_form(
            step_id="scene",
            data_schema=await _async_build_schema(user_input, self._data, options_flow=True),
            errors=errors,
            description_placeholders={"scene_name": self._data[CONF_NAME]},
        )

    async def async_step_color_yaml(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle color configuration in YAML mode within the options flow."""
        errors: dict[str, Any] = {}

        # Defaults
        defaults: dict[str, Any] = {}

        if user_input is not None:
            self._data.update(user_input)
            if self._data.get(CONF_COLORS) is None or self._data.get(CONF_COLORS) == {}:
                errors["base"] = ERROR_COLORS_IS_BLANK
            if not isinstance(self._data.get(CONF_COLORS), list):
                errors["base"] = ERROR_COLORS_MALFORMED
            for k, v in defaults.items():
                self._data.setdefault(k, v)
            # _LOGGER.debug(f"[async_step_color_yaml] self._data: {self._data}")
            if not errors:
                self._data.update({CONF_COLOR_RGB_DICT: {}})
                self.hass.config_entries.async_update_entry(
                    self.config, data=self._data, options=self.config.options
                )
                await self.hass.config_entries.async_reload(self.config.entry_id)
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="color_yaml",
            data_schema=await _async_build_color_yaml_schema(user_input, self._data),
            errors=errors,
            description_placeholders={
                "component_color_config_url": COMPONENT_COLOR_CONFIG_URL,
            },
        )

    async def async_step_color_rgb_ui(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle color configuration using the RGB UI selectors in options."""
        errors: dict[str, Any] = {}

        # Defaults
        defaults = {
            CONF_BRIGHTNESS: DEFAULT_BRIGHTNESS,
            CONF_COLOR_NEARBY_COLORS: DEFAULT_COLOR_NEARBY_COLORS,
            CONF_COLOR_ONE_CHANGE_PER_TICK: DEFAULT_COLOR_ONE_CHANGE_PER_TICK,
            CONF_COLOR_WEIGHT: DEFAULT_COLOR_WEIGHT,
            CONF_COLOR_ADD_COLOR: DEFAULT_COLOR_ADD_COLOR,
            CONF_COLOR_DELETE_COLOR: DEFAULT_COLOR_DELETE_COLOR,
        }
        if self._rgb_ui_color_index + 1 <= self._rgb_ui_color_max:
            color_data = self._rgb_ui_color_values[self._rgb_ui_color_index]
        else:
            color_data = {}

        if user_input is not None:
            color_data.update(user_input)
            _LOGGER.debug(
                "Checking Brightnes: %s, type: %s",
                color_data.get(CONF_BRIGHTNESS),
                type(color_data.get(CONF_BRIGHTNESS)),
            )
            brightness_check, brightness_value = is_int_or_list(
                color_data.get(CONF_BRIGHTNESS),
                BRIGHTNESS_MIN,
                BRIGHTNESS_MAX,
            )
            if brightness_check:
                color_data.update({CONF_BRIGHTNESS: brightness_value})
            else:
                errors["base"] = ERROR_BRIGHTNESS_NOT_INT_OR_RANGE
            color_data.update({CONF_COLOR_WEIGHT: round(color_data.get(CONF_COLOR_WEIGHT))})
            color_data.update(
                {CONF_COLOR_NEARBY_COLORS: round(color_data.get(CONF_COLOR_NEARBY_COLORS))}
            )
            for k, v in defaults.items():
                color_data.setdefault(k, v)
            if not errors:
                if self._rgb_ui_color_index + 1 <= self._rgb_ui_color_max:
                    self._data.get(CONF_COLOR_RGB_DICT, {}).update(
                        {self._rgb_ui_color_keys[self._rgb_ui_color_index]: color_data}
                    )
                else:
                    color_uuid = uuid.random_uuid_hex()
                    self._data.get(CONF_COLOR_RGB_DICT, {}).update({color_uuid: color_data})
                if self._rgb_ui_color_index + 1 < self._rgb_ui_color_max or (
                    self._rgb_ui_color_index + 1 >= self._rgb_ui_color_max
                    and color_data.get(CONF_COLOR_ADD_COLOR, False)
                ):
                    # _LOGGER.debug(f"[async_step_color_rgb_ui] self._data: {self._data}")
                    self._rgb_ui_color_index += 1
                    return await self.async_step_color_rgb_ui()
                self._data.update({CONF_COLORS: {}})
                self._data.update(
                    {
                        CONF_COLOR_RGB_DICT: clean_color_rgb_dict(
                            self._data.get(CONF_COLOR_RGB_DICT, {})
                        )
                    }
                )
                # _LOGGER.debug(f"[async_step_color_rgb_ui] self._data: {self._data}")
                self.hass.config_entries.async_update_entry(
                    self.config, data=self._data, options=self.config.options
                )
                await self.hass.config_entries.async_reload(self.config.entry_id)
                return self.async_create_entry(title="", data={})
            # _LOGGER.debug(f"[async_step_color_rgb_ui] color_data: {color_data}")

        return self.async_show_form(
            step_id="color_rgb_ui",
            data_schema=await _async_build_color_rgb_ui_schema(
                user_input,
                color_data,
                options_flow=True,
                is_last_color=(self._rgb_ui_color_index + 1 >= self._rgb_ui_color_max),
            ),
            errors=errors,
            description_placeholders={
                "component_color_config_url": COMPONENT_COLOR_CONFIG_URL,
                "color_count": str(self._rgb_ui_color_index + 1),
                "color_max": str(self._rgb_ui_color_max),
            },
        )
