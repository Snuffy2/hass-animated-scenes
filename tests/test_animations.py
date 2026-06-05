"""Tests for Animated Scenes runtime manager and service setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.animated_scenes import async_setup, async_unload_entry
from custom_components.animated_scenes.animations import Animation, Animations
from custom_components.animated_scenes.const import CONF_ENTITY_TYPE, DOMAIN, ENTITY_SCENE
from custom_components.animated_scenes.scene_config import (
    ADD_LIGHTS_TO_ANIMATION_SERVICE_SCHEMA,
    REMOVE_LIGHTS_SERVICE_SCHEMA,
    START_SERVICE_SCHEMA,
    STOP_SERVICE_SCHEMA,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


def _animation_config(name: str, lights: list[str], priority: int = 0) -> dict[str, object]:
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


def _scene_entry() -> ConfigEntry:
    """Return a scene config entry for unload lifecycle tests.

    Returns:
        A Home Assistant ``ConfigEntry`` carrying the minimal Animated Scenes
        scene data needed by ``async_unload_entry``.

    """
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Spooky",
        data={CONF_ENTITY_TYPE: ENTITY_SCENE, "name": "Spooky"},
        discovery_keys={},
        options={},
        source="user",
        subentries_data={},
        unique_id=None,
        entry_id="entry-spooky",
    )


@pytest.mark.asyncio
async def test_services_register_with_schema(hass: HomeAssistant) -> None:
    """Require each public service registration to enforce its shared schema.

    Home Assistant applies the schema passed to ``async_register`` before the
    service handler runs. This protects the runtime manager from receiving
    malformed service data through the public service API.
    """
    assert await async_setup(hass, {}) is True

    registrations = hass.services.async_services_internal()[DOMAIN]

    assert set(registrations) == {
        "start_animation",
        "stop_animation",
        "remove_lights",
        "add_lights_to_animation",
    }
    assert registrations["start_animation"].schema is START_SERVICE_SCHEMA
    assert registrations["stop_animation"].schema is STOP_SERVICE_SCHEMA
    assert registrations["remove_lights"].schema is REMOVE_LIGHTS_SERVICE_SCHEMA
    assert registrations["add_lights_to_animation"].schema is ADD_LIGHTS_TO_ANIMATION_SERVICE_SCHEMA


@pytest.mark.asyncio
async def test_release_light_removes_owner_when_no_successor(hass: HomeAssistant) -> None:
    """Remove all runtime ownership state after the final animation releases a light.

    A released light must not keep stale ``light_owner`` or
    ``_light_animations`` entries because later animations use those maps to
    decide whether a light is already owned.
    """
    manager = Animations(hass)
    Animations.instance = manager
    hass.states.async_set("light.one", "on", {"brightness": 100, "color_mode": "rgb"})
    animation = Animation(hass, _animation_config("Spooky", ["light.one"]))
    manager.animations[animation.name] = animation
    manager.light_owner["light.one"] = animation
    manager._light_animations["light.one"] = [animation]  # noqa: SLF001
    manager.store_state("light.one")

    with patch.object(manager, "refresh_listener", wraps=manager.refresh_listener) as refresh_listener:
        await manager.release_light(animation, "light.one")

    assert "light.one" not in manager.light_owner
    assert "light.one" not in manager._light_animations  # noqa: SLF001
    assert "light.one" not in manager.states
    refresh_listener.assert_called_once()


@pytest.mark.asyncio
async def test_release_light_hands_owner_to_next_priority(hass: HomeAssistant) -> None:
    """Transfer ownership to the next-highest-priority animation without restoring.

    When another animation still targets the same light, releasing the current
    owner should update ``light_owner`` and retain the stored original state so
    the final owner can restore it later.
    """
    manager = Animations(hass)
    Animations.instance = manager
    hass.states.async_set("light.one", "on", {"brightness": 100, "color_mode": "rgb"})
    low = Animation(hass, _animation_config("Low", ["light.one"], priority=1))
    high = Animation(hass, _animation_config("High", ["light.one"], priority=10))
    manager.animations[low.name] = low
    manager.animations[high.name] = high
    manager.light_owner["light.one"] = high
    manager._light_animations["light.one"] = [low, high]  # noqa: SLF001
    manager.store_state("light.one")

    await manager.release_light(high, "light.one")

    assert manager.light_owner["light.one"] is low
    assert "light.one" in manager.states


@pytest.mark.asyncio
async def test_release_light_skip_ownership_keeps_remaining_owner(
    hass: HomeAssistant,
) -> None:
    """Keep an existing owner when removal skips priority reassignment.

    The ``remove_lights`` service calls ``release_light`` with
    ``skip_ownership=True`` after removing a light from one animation. If
    another animation still tracks that light, the manager must retain a
    coherent owner so the remaining animation can keep ticking safely.
    """
    manager = Animations(hass)
    Animations.instance = manager
    hass.states.async_set("light.one", "on", {"brightness": 100, "color_mode": "rgb"})
    removed = Animation(hass, _animation_config("Removed", ["light.one"], priority=10))
    remaining = Animation(hass, _animation_config("Remaining", ["light.one"], priority=1))
    manager.animations[removed.name] = removed
    manager.animations[remaining.name] = remaining
    manager.light_owner["light.one"] = removed
    manager._light_animations["light.one"] = [remaining, removed]  # noqa: SLF001
    manager.store_state("light.one")

    await manager.release_light(removed, "light.one", skip_ownership=True)

    assert manager.light_owner["light.one"] is remaining
    assert manager._light_animations["light.one"] == [remaining]  # noqa: SLF001
    assert "light.one" in manager.states


@pytest.mark.asyncio
async def test_manager_stop_by_name_stops_running_animation(hass: HomeAssistant) -> None:
    """Stop a named animation without requiring service-call validation.

    Config-entry unload already has a trusted entry title/name, so it should be
    able to stop the matching runtime animation directly instead of fabricating
    service data for the public ``stop_animation`` handler.
    """
    manager = Animations(hass)
    animation = AsyncMock()
    animation.name = "Spooky"
    manager.animations["Spooky"] = animation

    await manager.stop_by_name("Spooky")

    animation.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_unload_entry_stops_scene_animation(hass: HomeAssistant) -> None:
    """Stop a running scene animation before unloading its config entry.

    A scene entity can be removed or reloaded while its animation is active.
    Unload must stop that runtime task so it does not continue controlling
    lights after Home Assistant removes the config entry's platform entity.
    """
    manager = Animations(hass)
    Animations.instance = manager
    animation = AsyncMock()
    animation.name = "Spooky"
    manager.animations["Spooky"] = animation
    entry = _scene_entry()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = dict(entry.data)

    with patch.object(hass.config_entries, "async_unload_platforms", return_value=True):
        assert await async_unload_entry(hass, entry) is True

    animation.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_unload_entry_handles_animation_release_cleanup(hass: HomeAssistant) -> None:
    """Avoid double-stop or double-delete when a stopped animation releases itself.

    Real animations remove themselves from ``manager.animations`` during their
    stop/release path. Last-entry unload must tolerate that self-cleanup before
    the final manager-wide teardown runs.
    """

    class ReleasingAnimation:
        """Animation stub that follows the real manager release contract."""

        name = "Spooky"

        def __init__(self, manager: Animations) -> None:
            """Store the manager and initialize stop accounting.

            Args:
                manager: Runtime manager that owns this stub animation.

            """
            self.manager = manager
            self.stop_count = 0

        async def stop(self) -> None:
            """Record one stop call and release from the manager.

            Returns:
                None. The method mirrors the real animation path that calls
                ``release_animation`` before control returns to unload cleanup.

            """
            self.stop_count += 1
            self.manager.release_animation(self)

    manager = Animations(hass)
    Animations.instance = manager
    animation = ReleasingAnimation(manager)
    manager.animations["Spooky"] = animation
    manager.states["light.one"] = object()
    manager.light_owner["light.one"] = animation  # type: ignore[assignment]
    manager._light_animations["light.one"] = [animation]  # noqa: SLF001
    entry = _scene_entry()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = dict(entry.data)

    with patch.object(hass.config_entries, "async_unload_platforms", return_value=True):
        assert await async_unload_entry(hass, entry) is True

    assert animation.stop_count == 1
    assert manager.animations == {}
    assert manager.states == {}
    assert manager.light_owner == {}
    assert manager._light_animations == {}  # noqa: SLF001
    assert Animations.instance is None


@pytest.mark.asyncio
async def test_unload_entry_keeps_animation_when_platform_unload_fails(
    hass: HomeAssistant,
) -> None:
    """Keep runtime animation active when Home Assistant cannot unload the entry.

    If platform unload fails, Home Assistant still considers the config entry
    loaded. Runtime cleanup must therefore wait until ``async_unload_platforms``
    succeeds.
    """
    manager = Animations(hass)
    Animations.instance = manager
    animation = AsyncMock()
    animation.name = "Spooky"
    manager.animations["Spooky"] = animation
    entry = _scene_entry()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = dict(entry.data)

    with patch.object(hass.config_entries, "async_unload_platforms", return_value=False):
        assert await async_unload_entry(hass, entry) is False

    animation.stop.assert_not_awaited()
    assert hass.data[DOMAIN][entry.entry_id]["name"] == "Spooky"
