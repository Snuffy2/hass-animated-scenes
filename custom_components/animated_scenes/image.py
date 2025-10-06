"""Create and cache horizontal block images representing dominant scene colors for the Animated Scenes integration."""

from __future__ import annotations

import copy
import io
import logging
from typing import Any

from PIL import Image as PILImage, ImageDraw as PILImageDraw

from homeassistant.components.image import Image, ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    COLOR_SELECTOR_RGB_UI,
    CONF_COLOR_RGB,
    CONF_COLOR_RGB_DICT,
    CONF_COLOR_SELECTOR_MODE,
    CONF_COLOR_TYPE,
    CONF_COLORS,
    CONF_NAME,
)

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Animated Scenes image entity for a config entry.

    Creates and adds a single AnimatedScenesImage entity for this integration.
    The integration configuration is retrieved from hass.data using DOMAIN and
    the provided config_entry.entry_id.

    Parameters
    ----------
    hass : HomeAssistant
        Home Assistant core object.
    config_entry : ConfigEntry
        The configuration entry to set up.
    async_add_entities : AddConfigEntryEntitiesCallback
        Callback used to add entities to Home Assistant.

    """
    _LOGGER.debug("[async_setup_entry] config: %s", config_entry.data)
    unique_id: str = config_entry.entry_id
    async_add_entities(
        [AnimatedScenesImage(hass=hass, config=dict(config_entry.data), unique_id=unique_id)]
    )


class AnimatedScenesImage(ImageEntity):
    """Image entity for Animated Scenes that generates and caches a horizontal block image.

    This entity creates a PNG image composed of horizontal blocks whose widths are
    proportional to the provided color weights and whose colors match the dominant
    scene colors. The generated PNG bytes are wrapped in a Home Assistant Image and
    cached on the entity.

    Attributes
    ----------
    _cached_image : homeassistant.components.image.Image | None
        Cached image (PNG bytes wrapped in HA Image) or None if not yet generated.
    _attr_image_last_updated : datetime
        Timestamp of the last update to the cached image.

    """

    def __init__(self, hass: HomeAssistant, config: dict[str, Any], unique_id: str) -> None:
        """Initialize the AnimatedScenesImage entity.

        Parameters
        ----------
        hass : HomeAssistant
            Home Assistant core object.
        config : ConfigType
            Integration configuration data for this entity.
        unique_id : str
            Unique identifier for this entity (typically config_entry.entry_id).

        """
        ImageEntity.__init__(self, hass)
        self._attr_name: str = f"{config[CONF_NAME]} Color Block"
        self._attr_image_last_updated = dt_util.utcnow()
        self._cached_image: Image | None = None
        self._attr_unique_id: str = f"{unique_id}-image"
        self._config = config

    async def async_added_to_hass(self) -> None:
        """Handle the entity being added to Home Assistant.

        This coroutine is called when the entity is added to Home Assistant; it
        logs the addition and generates the color block image.

        Returns
        -------
        None
            This method performs side effects (logging and image creation) and
            does not return a value.

        """
        if self._config.get(CONF_COLOR_SELECTOR_MODE, None) == COLOR_SELECTOR_RGB_UI:
            await self._async_build_colors_from_rgb_dict()
        _LOGGER.debug("[async_added_to_hass] config after RGB build: %s", self._config)
        await self.create_color_block_image(scene_colors=self._config.get(CONF_COLORS, []))

    async def _async_build_colors_from_rgb_dict(self) -> None:
        """Build a colors list from a color RGB dictionary in the config.

        Converts the stored RGB dict into a list of color mappings and marks
        each entry as an RGB color type so the rest of the code can use a
        unified `CONF_COLORS` structure.
        """

        color_list = list(copy.deepcopy(self._config.get(CONF_COLOR_RGB_DICT, {})).values())
        for color in color_list:
            color.update({CONF_COLOR_TYPE: CONF_COLOR_RGB})
        # _LOGGER.debug(f"[async_build_colors_from_rgb_dict] color_list: {color_list}")
        self._config.update({CONF_COLORS: color_list})

    async def create_color_block_image(self, scene_colors: list) -> None:
        """Generate and cache a horizontal block PNG image representing dominant scene colors.

        The method builds an RGB PNG image where each horizontal block's width is
        proportional to the corresponding color's "weight" and its fill color is
        taken from the "color" entry. The resulting PNG bytes are stored in
        self._cached_image and self._attr_image_last_updated is updated.

        Parameters
        ----------
        scene_colors : list
            Sequence of dicts with keys:
            - "color": a sequence of three ints (R, G, B)
            - "weight": a numeric value indicating the relative width of the block

        Returns
        -------
        None
            The generated image is cached on the entity; nothing is returned.

        """
        _LOGGER.debug("[create_color_block_image] scene_colors: %s", scene_colors)

        # Calculate the width of each block based on the weight
        width, height = 500, 100  # Size of the output image
        total_weight = sum(color_info["weight"] for color_info in scene_colors) or 1

        # Create a new image
        block_image = PILImage.new("RGB", (width, height))
        draw = PILImageDraw.Draw(block_image)

        current_x = 0
        for color_info in scene_colors:
            block_width = int((color_info["weight"] / total_weight) * width)
            # Ensure we don't produce zero-width blocks for very small weights
            if block_width <= 0:
                continue
            color = tuple(color_info["color"])
            draw.rectangle([current_x, 0, current_x + block_width, height], fill=color)
            current_x += block_width

        # Convert the PIL Image to bytes (PNG) and wrap in Home Assistant Image
        buffer = io.BytesIO()
        block_image.save(buffer, format="PNG")
        buffer.seek(0)
        content_bytes = buffer.getvalue()

        # Home Assistant Image requires content bytes and content_type
        self._cached_image = Image(content=content_bytes, content_type="image/png")
        self._attr_image_last_updated = dt_util.utcnow()
