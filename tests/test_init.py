"""Tests for Animated Scenes integration setup, migration, and unload."""

from __future__ import annotations

import asyncio
from types import MappingProxyType
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntry, DiscoveryKey
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.animated_scenes import (
    async_migrate_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.animated_scenes.animations import Animations
from custom_components.animated_scenes.const import (
    CONF_ENTITY_TYPE,
    DOMAIN,
    ENTITY_ACTIVITY_SENSOR,
    ENTITY_SCENE,
)

from .helpers import (
    LIGHT_ON,
    animation_config,
    animation_tasks,
    full_scene_data,
    register_light_services,
    runtime_manager,
    setup_scene_entry,
    start_scene,
)

DISCOVERY_KEYS: MappingProxyType[str, tuple[DiscoveryKey, ...]] = MappingProxyType({})


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
        discovery_keys=DISCOVERY_KEYS,
        options={},
        source="user",
        subentries_data={},
        unique_id=None,
        entry_id="entry-spooky",
    )


async def test_unload_stops_running_scene_and_keeps_services(hass: HomeAssistant) -> None:
    """Stop a scene on real entry unload while keeping public services available."""
    register_light_services(hass)
    hass.states.async_set("light.one", "on", LIGHT_ON)
    entry = await setup_scene_entry(hass, full_scene_data())
    manager = Animations.instance
    assert manager is not None
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.animated_scenes_spooky"}, blocking=True
    )
    await asyncio.sleep(0)
    assert len(animation_tasks("Spooky")) == 1

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert animation_tasks("Spooky") == []
    assert manager.animations == {}
    assert Animations.instance is manager

    await hass.services.async_call(
        DOMAIN,
        "start_animation",
        {**animation_config("Manual", ["light.one"]), "change_frequency": 3600},
        blocking=True,
    )
    assert "Manual" in manager.animations
    await manager.stop({CONF_NAME: "Manual"})


async def test_setup_entry_recreates_manager_after_last_entry_unload(
    hass: HomeAssistant,
) -> None:
    """Recreate the runtime manager when a reload sets up the entry again."""
    Animations.instance = None
    entry = _scene_entry()
    with patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()):
        assert await async_setup_entry(hass, entry) is True

    assert Animations.instance is not None


@pytest.mark.parametrize(
    ("data", "expected_type"),
    [
        ({CONF_NAME: "Legacy"}, ENTITY_SCENE),
        (
            {CONF_NAME: "Activity Sensor", CONF_ENTITY_TYPE: ENTITY_ACTIVITY_SENSOR},
            ENTITY_ACTIVITY_SENSOR,
        ),
    ],
)
async def test_migrate_entry_persists_entity_type(
    hass: HomeAssistant, data: dict[str, str], expected_type: str
) -> None:
    """Default legacy scenes while preserving explicit activity sensors."""
    entry = MockConfigEntry(domain=DOMAIN, data=data, version=1)
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == 2
    assert entry.data[CONF_ENTITY_TYPE] == expected_type


async def test_legacy_scene_migrates_runs_and_unloads(hass: HomeAssistant) -> None:
    """Run a legacy scene without a persisted entity type through its switch."""
    register_light_services(hass)
    hass.states.async_set("light.one", "on", LIGHT_ON)
    entry = await setup_scene_entry(hass, full_scene_data("Legacy"))
    manager = Animations.instance
    assert manager is not None

    assert entry.version == 2
    assert entry.data[CONF_ENTITY_TYPE] == ENTITY_SCENE
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.animated_scenes_legacy"}, blocking=True
    )
    assert "Legacy" in manager.animations

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert manager.animations == {}


async def test_unload_keeps_animation_when_platform_unload_fails(
    hass: HomeAssistant,
) -> None:
    """Keep the scene running when Home Assistant cannot unload its platform."""
    manager = runtime_manager(hass)
    register_light_services(hass)
    hass.states.async_set("light.one", "on", LIGHT_ON)
    await start_scene(manager, "Spooky", ["light.one"])
    entry = _scene_entry()

    with patch.object(hass.config_entries, "async_unload_platforms", return_value=False):
        assert await async_unload_entry(hass, entry) is False

    assert len(animation_tasks("Spooky")) == 1
    assert "Spooky" in manager.animations
    await manager.stop({CONF_NAME: "Spooky"})
