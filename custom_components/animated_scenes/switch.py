"""Switch platform for the Animated Scenes integration.

This module provides a switch entity that represents an animated scene
so that scenes can be managed from the Home Assistant UI or via YAML
imports. The switch delegates start/stop operations to the Animations
singleton.
"""

import copy
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.switch import ENTITY_ID_FORMAT, SwitchEntity
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_BRIGHTNESS, CONF_ICON, CONF_LIGHTS, CONF_NAME, MATCH_ALL
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

from .animations import Animations
from .const import (
    COLOR_SELECTOR_RGB_UI,
    CONF_ANIMATE_BRIGHTNESS,
    CONF_ANIMATE_COLOR,
    CONF_CHANGE_AMOUNT,
    CONF_CHANGE_FREQUENCY,
    CONF_CHANGE_SEQUENCE,
    CONF_COLOR_RGB_DICT,
    CONF_COLOR_SELECTOR_MODE,
    CONF_COLORS,
    CONF_ENTITY_TYPE,
    CONF_IGNORE_OFF,
    CONF_PLATFORM,
    CONF_PRIORITY,
    CONF_RESTORE,
    CONF_RESTORE_POWER,
    CONF_TRANSITION,
    DOMAIN,
    EVENT_NAME_CHANGE,
    EVENT_STATE_STARTED,
    EVENT_STATE_STOPPED,
    INTEGRATION_NAME,
)
from .scene_config import START_SERVICE_CONFIG, build_colors_from_rgb_dict

_LOGGER: logging.Logger = logging.getLogger(__name__)

PLATFORM_SCHEMA_PART = vol.Schema(
    {
        vol.Required(CONF_PLATFORM): DOMAIN,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA_PART.extend(START_SERVICE_CONFIG)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    _: AddEntitiesCallback,
    __: DiscoveryInfoType | None = None,
) -> None:
    """Set up the platform from legacy YAML configuration.

    This will create a config flow entry to import the YAML configuration
    into the UI-driven config entries system if the scene is not already
    registered.
    """

    _LOGGER.debug(
        "[async_setup_platform] config name: %s, existing scenes title list: %s",
        config.get(CONF_NAME, None),
        [x.title for x in hass.config_entries.async_entries(DOMAIN)],
    )
    async_create_issue(
        hass,
        HOMEASSISTANT_DOMAIN,
        f"deprecated_yaml_{DOMAIN}",
        breaks_in_ha_version="2025.1",
        is_fixable=False,
        is_persistent=False,
        issue_domain=DOMAIN,
        severity=IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
        translation_placeholders={
            "domain": DOMAIN,
            "integration_title": INTEGRATION_NAME,
        },
    )
    if config.get(CONF_NAME, None) not in [
        x.title for x in hass.config_entries.async_entries(DOMAIN)
    ]:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=config,
            )
        )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Animated Scene switch for a config entry.

    Instantiate and register the `AnimatedSceneSwitch` entity for the
    provided config entry.
    """

    config = hass.data.get(DOMAIN).get(config_entry.entry_id)
    unique_id: str = config_entry.entry_id
    async_add_entities([AnimatedSceneSwitch(hass, config, unique_id)])


class AnimatedSceneSwitch(SwitchEntity):
    """Switch entity representing a single animated scene.

    The switch exposes the scene configuration as attributes and forwards
    turn_on/turn_off operations to the Animations singleton.
    """

    _unrecorded_attributes = frozenset({MATCH_ALL})

    def __init__(self, hass: HomeAssistant, config: ConfigType, unique_id: str) -> None:
        """Initialize the AnimatedSceneSwitch entity.

        Store the provided configuration and prepare derived animation fields
        immediately so the entity can be turned on as soon as Home Assistant
        adds it.
        """

        _LOGGER.debug("[AnimatedSceneSwitch init] config: %s", config)
        # _LOGGER.debug(f"[AnimatedSceneSwitch init] unique_id: {unique_id}")
        self.hass: HomeAssistant = hass
        self._config = config
        self._attr_name: str = config[CONF_NAME]
        self._attr_icon: str = config[CONF_ICON]
        self._attr_is_on: bool = False
        self.entity_id = ENTITY_ID_FORMAT.format(slugify(f"{DOMAIN}_{self._attr_name}"))
        self._attr_unique_id: str = unique_id
        self._animation_config: dict[str, Any] = self._build_animation_config()

    def _build_animation_config(self) -> dict[str, Any]:
        """Build runtime animation configuration from config-entry data.

        Returns:
            A deep-copied service configuration with entity-only metadata and
            UI-only color selector fields removed.
        """

        if self._config.get(CONF_COLOR_SELECTOR_MODE, None) == COLOR_SELECTOR_RGB_UI:
            self._config[CONF_COLORS] = build_colors_from_rgb_dict(
                self._config.get(CONF_COLOR_RGB_DICT, {})
            )
        animation_config = copy.deepcopy(self._config)
        animation_config.pop(CONF_PLATFORM, None)
        animation_config.pop(CONF_ICON, None)
        animation_config.pop(CONF_ENTITY_TYPE, None)
        animation_config.pop(CONF_COLOR_RGB_DICT, None)
        animation_config.pop(CONF_COLOR_SELECTOR_MODE, None)
        return animation_config

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the switch's extra state attributes.

        The attributes expose the animation configuration options for
        inspection in the UI.
        """

        return {
            CONF_PRIORITY: self._config.get(CONF_PRIORITY),
            CONF_CHANGE_FREQUENCY: self._config.get(CONF_CHANGE_FREQUENCY),
            CONF_TRANSITION: self._config.get(CONF_TRANSITION),
            CONF_CHANGE_AMOUNT: self._config.get(CONF_CHANGE_AMOUNT),
            CONF_BRIGHTNESS: self._config.get(CONF_BRIGHTNESS),
            CONF_CHANGE_SEQUENCE: self._config.get(CONF_CHANGE_SEQUENCE),
            CONF_ANIMATE_BRIGHTNESS: self._config.get(CONF_ANIMATE_BRIGHTNESS),
            CONF_ANIMATE_COLOR: self._config.get(CONF_ANIMATE_COLOR),
            CONF_IGNORE_OFF: self._config.get(CONF_IGNORE_OFF),
            CONF_RESTORE: self._config.get(CONF_RESTORE),
            CONF_RESTORE_POWER: self._config.get(CONF_RESTORE_POWER),
            CONF_LIGHTS: self._config.get(CONF_LIGHTS),
            CONF_COLORS: self._config.get(CONF_COLORS),
        }

    @property
    def is_on(self) -> bool:
        """Return whether the animated scene is currently active.

        Returns:
            True when the switch has observed a start event or was turned on
            locally; false after a stop event or local turn-off.
        """

        return self._attr_is_on

    async def async_added_to_hass(self) -> None:
        """Subscribe the switch to animation lifecycle events.

        Returns:
            None. The listener removal callback is registered with Home
            Assistant so it is cleaned up automatically when the entity unloads.
        """

        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_NAME_CHANGE, self._handle_animation_event)
        )

    @callback
    def _handle_animation_event(self, event: Event) -> None:
        """Update switch state when this scene starts or stops.

        Args:
            event: Home Assistant event containing the animation name and
                lifecycle state.

        Returns:
            None. Unrelated animation events are ignored.
        """

        if event.data.get("animation") != self._attr_name:
            return
        state = event.data.get("state")
        if state == EVENT_STATE_STARTED:
            self._attr_is_on = True
        elif state == EVENT_STATE_STOPPED:
            self._attr_is_on = False
        else:
            return
        self.async_write_ha_state()

    async def async_turn_on(self, **_: Any) -> None:
        """Turn the switch on and start the corresponding animation.

        If the switch is already on this is a no-op.
        """

        if not self._attr_is_on:
            if Animations.instance:
                await Animations.instance.start(self._animation_config)
                self._attr_is_on = True
            else:
                _LOGGER.warning(
                    "[async_turn_on] Animations manager is not initialized; ignoring turn on"
                )

    async def async_turn_off(self, **_: Any) -> None:
        """Turn the switch off and stop the corresponding animation."""

        self._attr_is_on = False
        if Animations.instance:
            await Animations.instance.stop({"name": self._attr_name})
