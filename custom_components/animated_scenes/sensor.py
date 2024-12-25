import logging
from typing import Any, MutableMapping

from homeassistant.components.sensor import ENTITY_ID_FORMAT, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .animations import Animations
from .const import DEFAULT_ACTIVITY_SENSOR_ICON

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    _: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([AnimatedScenesSensor(hass)])


class AnimatedScenesSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass: HomeAssistant = hass
        self._attr_native_unit_of_measurement: str = "active animation(s)"
        self._attr_state_class: str = "measurement"
        self._attr_has_entity_name: bool = True
        self._attr_unique_id: str = "animated_scenes_activity_sensor"
        self._attr_name: str = "Activity"
        self._attr_icon: str = DEFAULT_ACTIVITY_SENSOR_ICON
        self.entity_id: str = ENTITY_ID_FORMAT.format("animated_scenes_activity_sensor")
        self._scan_interval: int = 3

    @property
    def native_value(self) -> int:
        return len(Animations.instance.animations)

    @property
    def extra_state_attributes(self) -> MutableMapping[str, Any]:
        return {
            "active": list(Animations.instance.animations.keys()),
            "active_lights": list(Animations.instance.light_owner.keys()),
        }
