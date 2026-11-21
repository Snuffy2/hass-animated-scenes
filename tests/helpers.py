"""Shared helpers that exercise Animated Scenes through Home Assistant services."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.light import LIGHT_TURN_ON_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.animated_scenes.animations import Animation, Animations
from custom_components.animated_scenes.const import (
    COLOR_SELECTOR_YAML,
    CONF_COLOR_RGB_DICT,
    CONF_COLOR_SELECTOR_MODE,
    DOMAIN,
)


def register_light_services(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Register light services that enforce Home Assistant's real turn-on schema.

    Args:
        hass: Home Assistant test instance.

    Returns:
        A list that records each accepted ``light.turn_on`` payload.

    """
    calls: list[dict[str, Any]] = []

    async def _turn_on(call: ServiceCall) -> None:
        """Record a valid turn-on call and mark its lights as on."""
        calls.append(dict(call.data))
        for entity_id in call.data["entity_id"]:
            state = hass.states.get(entity_id)
            hass.states.async_set(
                entity_id,
                "on",
                dict(state.attributes) if state else {},
                context=call.context,
            )

    async def _turn_off(_: ServiceCall) -> None:
        """Accept a turn-off call."""

    hass.services.async_register(
        "light",
        "turn_on",
        _turn_on,
        schema=cv.make_entity_service_schema(LIGHT_TURN_ON_SCHEMA),  # type: ignore[arg-type, unused-ignore]
    )
    hass.services.async_register(
        "light",
        "turn_off",
        _turn_off,
        schema=cv.make_entity_service_schema({}),  # type: ignore[arg-type, unused-ignore]
    )
    return calls


def animation_tasks(name: str) -> list[asyncio.Task[Any]]:
    """Return unfinished animation loop tasks for a scene name."""
    return [
        task
        for task in asyncio.all_tasks()
        if task.get_name() == f"animated_scenes_{name}" and not task.done()
    ]


LIGHT_ON: dict[str, object] = {"color_mode": "rgb", "brightness": 100, "rgb_color": (1, 2, 3)}


def animation_config(name: str, lights: list[str], priority: int = 0) -> dict[str, object]:
    """Return a minimal validated runtime animation configuration.

    Args:
        name: Unique animation name used by the manager.
        lights: Light entity ids controlled by the animation.
        priority: Ownership priority used when animations overlap.

    Returns:
        A service-schema-compatible configuration dictionary for constructing
        an ``Animation`` directly in manager unit tests.

    """
    return {
        "name": name,
        "lights": lights,
        "colors": [{"color_type": "rgb_color", "color": (255, 0, 0)}],
        "ignore_off": True,
        "restore": True,
        "restore_power": False,
        "brightness": 255,
        "transition": 1,
        "change_frequency": 1,
        "change_amount": "all",
        "change_sequence": False,
        "animate_brightness": True,
        "animate_color": True,
        "priority": priority,
    }


def runtime_manager(hass: HomeAssistant) -> Animations:
    """Return a runtime manager registered as the active singleton."""
    manager = Animations(hass)
    Animations.instance = manager
    return manager


async def start_scene(
    manager: Animations, name: str, lights: list[str], **overrides: object
) -> Animation:
    """Start a scene whose loop stays idle and return its running animation.

    Args:
        manager: Runtime manager that starts the scene.
        name: Scene name.
        lights: Lights controlled by the scene.
        **overrides: Scene configuration values to override.

    Returns:
        The animation registered by the public manager start path.

    """
    await manager.start({**animation_config(name, lights), "change_frequency": 3600, **overrides})
    await asyncio.sleep(0)
    return manager.animations[name]


def full_scene_data(name: str = "Spooky") -> dict[str, object]:
    """Return stored data for a real scene config entry."""
    return {
        **animation_config(name, ["light.one"]),
        "colors": [{"color_type": "rgb_color", "color": [255, 0, 0]}],
        "change_frequency": 3600,
        "icon": "mdi:lightbulb",
        CONF_COLOR_SELECTOR_MODE: COLOR_SELECTOR_YAML,
        CONF_COLOR_RGB_DICT: {},
    }


async def setup_scene_entry(hass: HomeAssistant, data: dict[str, object]) -> MockConfigEntry:
    """Set up a real scene config entry and return it."""
    entry = MockConfigEntry(domain=DOMAIN, version=1, title=str(data[CONF_NAME]), data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
