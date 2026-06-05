# Animated Scenes Functionality Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Animated Scenes more reliable, testable, and Home Assistant-native by fixing lifecycle/runtime-state drift, unifying validation contracts, making entities event-driven, and adding support surfaces.

**Architecture:** Keep the current integration shape, but introduce focused modules for scene-config normalization and diagnostics while tightening the runtime manager interface. Do the smallest useful split: config validation moves out of the config flow, switch/sensor entities subscribe to animation events, and the animation manager becomes responsible for explicit cleanup and lifecycle state. Preserve current service names, entity IDs, and existing config-entry data keys.

**Tech Stack:** Home Assistant custom integration, Python 3.14, voluptuous, pytest, pytest-homeassistant-custom-component, ruff, mypy, prek.

---

## File Structure

- Create: `custom_components/animated_scenes/scene_config.py`
  - Responsibility: shared defaults, input coercion, color-list conversion, and service/config-entry validation for animated scene configuration.
- Create: `custom_components/animated_scenes/diagnostics.py`
  - Responsibility: redacted config-entry diagnostics and runtime summary.
- Create: `AGENTS.md`
  - Responsibility: standalone repository instructions for future agents working in this project.
- Create: `tests/conftest.py`
  - Responsibility: Home Assistant pytest fixtures and integration auto-enable setup.
- Create: `tests/test_scene_config.py`
  - Responsibility: shared config normalization unit tests.
- Create: `tests/test_animations.py`
  - Responsibility: runtime manager ownership, lifecycle, service schema, and restoration tests.
- Create: `tests/test_switch.py`
  - Responsibility: switch readiness and event-driven state tests.
- Create: `tests/test_sensor.py`
  - Responsibility: activity sensor uniqueness and event-driven updates.
- Create: `tests/test_diagnostics.py`
  - Responsibility: diagnostics redaction and runtime-summary tests.
- Modify: every Python file under `custom_components/animated_scenes/`
  - Add or update meaningful file, class, public method, private method, and nested method docstrings. Method docstrings must use Google Style and explain intent, important invariants, side effects, arguments, raised exceptions, and return semantics where relevant.
- Modify: every Python test file under `tests/`
  - Add meaningful module, fixture, helper, and test docstrings. Test docstrings should explain the behavior being protected, not restate the test function name.
- Modify: `pyproject.toml`
  - Set the project/runtime target to Python 3.14, move all dependencies from `requirements*.txt` into project metadata or dependency groups, and update tool targets.
- Create: `prek.toml`
  - Responsibility: prek hook configuration replacing `.pre-commit-config.yaml`.
- Remove: `requirements.txt`
  - Runtime dependencies are represented in `pyproject.toml`.
- Remove: `requirements-dev.txt`
  - Development and test dependencies are represented in `pyproject.toml`.
- Remove: `requirements-lint.txt`
  - Lint/type dependencies are represented in `pyproject.toml`.
- Remove: `.pre-commit-config.yaml`
  - Hook configuration is represented in `prek.toml`.
- Modify: `custom_components/animated_scenes/__init__.py`
  - Register service schemas, create/reuse manager in `hass.data`, stop scene animations on unload, and remove services/listeners during integration unload when appropriate.
- Modify: `custom_components/animated_scenes/animations.py`
  - Use shared schemas from `scene_config.py`, clean up `light_owner`, make manager cleanup explicit, and expose event/listener hooks for entities.
- Modify: `custom_components/animated_scenes/config_flow.py`
  - Delegate repeated scene input normalization to `scene_config.py`, check activity sensor duplicates from config entries, and keep options flow behavior equivalent.
- Modify: `custom_components/animated_scenes/switch.py`
  - Build animation config synchronously before entity add, subscribe to animation events, and update HA state when services start/stop the scene.
- Modify: `custom_components/animated_scenes/sensor.py`
  - Subscribe to animation events and write state immediately instead of polling.
- Modify: `custom_components/animated_scenes/services.yaml`
  - Align advertised limits with runtime validation and mark optional fields correctly.
- Modify: `custom_components/animated_scenes/translations/en.json`
  - Add repair issue translations and diagnostics-safe user text if needed.
- Modify: `custom_components/animated_scenes/manifest.json`
  - Either add device support via `device_info` or change integration metadata if the final implementation chooses entity-only semantics.
- Modify: `README.MD`
  - Update activity sensor, service limits, and reload/lifecycle behavior notes.

## Execution Rules

- Work from branch `review/functionality-optimization-audit`, which must track `origin/review/functionality-optimization-audit`.
- Do not open a PR unless explicitly requested.
- Use `./.venv/bin/python`, `./.venv/bin/pytest`, `./.venv/bin/ruff`, `./.venv/bin/mypy`, and `./.venv/bin/prek`.
- Use Python 3.14 for the repository-local virtual environment.
- If `.venv` does not exist, create it and install requirements before Task 1:

```bash
python3.14 -m venv .venv
./.venv/bin/python -m pip install -U pip
./.venv/bin/python -m pip install -e ".[dev,lint,test]"
```

- After every task, run the task-specific tests and commit only that task's files.
- Every new or modified Python file must have a meaningful module docstring. Every class and method, including private and nested methods, must have a meaningful docstring. Method docstrings must follow Google Style with `Args:`, `Returns:`, `Raises:`, and `Yields:` sections when applicable. Avoid docstrings that only reword the method name or type signature.
- Final verification must run:

```bash
./.venv/bin/prek run -a
./.venv/bin/pytest
./.venv/bin/mypy custom_components/animated_scenes
git status --short --branch
git branch -vv
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

Expected final branch upstream: `origin/review/functionality-optimization-audit`.

---

### Task 1: Modernize Project Tooling and Agent Instructions

**Files:**

- Create: `AGENTS.md`
- Modify: `pyproject.toml`
- Create: `prek.toml`
- Remove: `requirements.txt`
- Remove: `requirements-dev.txt`
- Remove: `requirements-lint.txt`
- Remove: `.pre-commit-config.yaml`

- [ ] **Step 1: Write the failing tooling expectations**

Create `AGENTS.md`:

```markdown
# AGENTS.md

## Project Scope

This repository contains the Animated Scenes custom integration for Home Assistant.

## Development Environment

- Use Python 3.14.
- Use the repository-local virtual environment at `./.venv`.
- Install development tooling from `pyproject.toml` extras or dependency groups.
- Do not install tooling from `requirements*.txt`; those files should not exist in this repo.

## Tooling

- Use `prek`, not `pre-commit`.
- Hook configuration lives in `prek.toml`.
- Run `./.venv/bin/prek run -a` before final handoff.
- Run `./.venv/bin/pytest` for tests.
- Run `./.venv/bin/mypy custom_components/animated_scenes` for typing checks.

## Home Assistant Integration Rules

- Preserve existing config-entry data keys unless a migration is added.
- Keep service names stable: `start_animation`, `stop_animation`, `remove_lights`, and `add_lights_to_animation`.
- Do not manually edit Home Assistant `.storage` files.
- Prefer entity IDs over device IDs in examples and tests.
```

Add this shell check to verify the repository does not still rely on legacy requirements or pre-commit files:

```bash
test -f AGENTS.md
test -f pyproject.toml
test -f prek.toml
test ! -f requirements.txt
test ! -f requirements-dev.txt
test ! -f requirements-lint.txt
test ! -f .pre-commit-config.yaml
./.venv/bin/python - <<'PY'
from pathlib import Path
import tomllib

data = tomllib.loads(Path("pyproject.toml").read_text())
project = data["project"]
assert project["requires-python"] == ">=3.14"
optional = project["optional-dependencies"]
for group in ("dev", "lint", "test"):
    assert group in optional
ruff = data["tool"]["ruff"]
assert ruff["target-version"] == "py314"
assert "D" in data["tool"]["ruff"]["lint"]["select"]
mypy = data["tool"]["mypy"]
assert mypy["python_version"] == "3.14"
PY
```

Expected before implementation: FAIL because `AGENTS.md` and `prek.toml` do not exist, requirements files still exist, and `pyproject.toml` has not yet been bumped to Python 3.14.

- [ ] **Step 2: Move requirements into `pyproject.toml`**

Update `pyproject.toml` so it includes project metadata and dependency extras:

```toml
[project]
name = "hass-animated-scenes"
version = "2.1.1"
description = "Animated light scenes custom integration for Home Assistant"
readme = "README.MD"
requires-python = ">=3.14"
license = { text = "MIT" }
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "pytest-timeout",
    "pytest-homeassistant-custom-component",
]
lint = [
    "homeassistant-stubs",
    "mypy",
    "prek",
    "ruff",
    "rumdl",
    "types-cffi",
    "types-PyMySQL",
    "types-pyRFC3339",
    "types-python-dateutil",
    "types-PyYAML",
    "types-requests",
    "types-setuptools",
]
test = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "pytest-timeout",
    "pytest-homeassistant-custom-component",
]
```

Preserve the existing `[tool.pytest.ini_options]`, `[tool.coverage.*]`, `[tool.mypy]`, and `[tool.ruff.*]` sections.

Change existing tool targets:

```toml
[tool.mypy]
python_version = "3.14"
```

```toml
[tool.ruff]
target-version = "py314"
```

- [ ] **Step 3: Replace pre-commit with prek**

Create `prek.toml`:

```toml
minimum_pre_commit_version = "4.0.0"

default_language_version = { python = "python3.14" }

repos = [
  { repo = "https://github.com/astral-sh/ruff-pre-commit", rev = "v0.8.0", hooks = [
    { id = "ruff", args = ["--fix"] },
    { id = "ruff-format" },
  ] },
  { repo = "https://github.com/pre-commit/mirrors-mypy", rev = "v1.13.0", hooks = [
    { id = "mypy", args = ["custom_components/animated_scenes"], additional_dependencies = ["homeassistant-stubs"] },
  ] },
  { repo = "https://github.com/pre-commit/pre-commit-hooks", rev = "v5.0.0", hooks = [
    { id = "check-json" },
    { id = "check-toml" },
    { id = "check-yaml" },
    { id = "end-of-file-fixer" },
    { id = "trailing-whitespace" },
  ] },
]
```

If `.pre-commit-config.yaml` exists, delete it using:

```bash
trash .pre-commit-config.yaml
```

- [ ] **Step 4: Remove legacy requirement files**

After the dependency lists have been copied into `pyproject.toml`, remove the legacy files:

```bash
trash requirements.txt requirements-dev.txt requirements-lint.txt
```

- [ ] **Step 5: Recreate/install the Python 3.14 environment**

Run:

```bash
trash .venv
python3.14 -m venv .venv
./.venv/bin/python -m pip install -U pip
./.venv/bin/python -m pip install -e ".[dev,lint,test]"
./.venv/bin/python --version
```

Expected: Python reports `3.14.x`.

- [ ] **Step 6: Run tooling verification**

Run:

```bash
test -f AGENTS.md
test -f pyproject.toml
test -f prek.toml
test ! -f requirements.txt
test ! -f requirements-dev.txt
test ! -f requirements-lint.txt
test ! -f .pre-commit-config.yaml
./.venv/bin/python - <<'PY'
from pathlib import Path
import tomllib

data = tomllib.loads(Path("pyproject.toml").read_text())
project = data["project"]
assert project["requires-python"] == ">=3.14"
optional = project["optional-dependencies"]
for group in ("dev", "lint", "test"):
    assert group in optional
ruff = data["tool"]["ruff"]
assert ruff["target-version"] == "py314"
assert "D" in data["tool"]["ruff"]["lint"]["select"]
mypy = data["tool"]["mypy"]
assert mypy["python_version"] == "3.14"
PY
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add AGENTS.md pyproject.toml prek.toml
git add -u requirements.txt requirements-dev.txt requirements-lint.txt .pre-commit-config.yaml
git commit -m "chore: modernize animated scenes project tooling"
```

---

### Task 2: Establish Test Harness

**Files:**

- Create: `tests/conftest.py`
- Create: `tests/test_scene_config.py`

- [ ] **Step 1: Write the failing test-harness files**

Create `tests/conftest.py`:

```python
"""Shared pytest fixtures for Animated Scenes tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from custom_components.animated_scenes.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Generator[None]:
    """Enable custom integrations for every Home Assistant test."""
    yield


@pytest.fixture
def integration_domain() -> str:
    """Return the Animated Scenes integration domain."""
    return DOMAIN
```

Create `tests/test_scene_config.py` with an initial import test that fails until Task 2 creates the module:

```python
"""Tests for shared Animated Scenes configuration normalization."""

from __future__ import annotations

from custom_components.animated_scenes.const import (
    CONF_CHANGE_AMOUNT,
    CONF_LIGHTS,
)
from custom_components.animated_scenes.scene_config import normalize_scene_input


def test_normalize_scene_input_clamps_change_amount_to_all() -> None:
    """Normalize change_amount larger than selected lights to all."""
    result = normalize_scene_input(
        {
            "name": "Spooky",
            CONF_LIGHTS: ["light.one", "light.two"],
            CONF_CHANGE_AMOUNT: "3",
            "transition": "1",
            "change_frequency": "1",
            "brightness": "255",
        }
    )

    assert result[CONF_CHANGE_AMOUNT] == "all"
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
./.venv/bin/pytest tests/test_scene_config.py::test_normalize_scene_input_clamps_change_amount_to_all -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'custom_components.animated_scenes.scene_config'`.

- [ ] **Step 3: Commit the failing harness**

```bash
git add tests/conftest.py tests/test_scene_config.py
git commit -m "test: add animated scenes test harness"
```

---

### Task 3: Shared Scene Config Normalization

**Files:**

- Create: `custom_components/animated_scenes/scene_config.py`
- Modify: `custom_components/animated_scenes/config_flow.py`
- Modify: `custom_components/animated_scenes/animations.py`
- Test: `tests/test_scene_config.py`

- [ ] **Step 1: Expand failing tests**

Replace `tests/test_scene_config.py` with:

```python
"""Tests for shared Animated Scenes configuration normalization."""

from __future__ import annotations

import pytest
import voluptuous as vol

from homeassistant.const import CONF_BRIGHTNESS, CONF_LIGHTS, CONF_NAME

from custom_components.animated_scenes.const import (
    CONF_CHANGE_AMOUNT,
    CONF_CHANGE_FREQUENCY,
    CONF_COLORS,
    CONF_COLOR_RGB_DICT,
    CONF_TRANSITION,
    DEFAULT_ANIMATE_BRIGHTNESS,
    DEFAULT_ANIMATE_COLOR,
    DEFAULT_CHANGE_SEQUENCE,
    DEFAULT_IGNORE_OFF,
    DEFAULT_PRIORITY,
    DEFAULT_RESTORE,
    DEFAULT_RESTORE_POWER,
)
from custom_components.animated_scenes.scene_config import (
    build_colors_from_rgb_dict,
    normalize_scene_input,
    validate_start_service_data,
)


def _base_input() -> dict[str, object]:
    """Return minimal valid scene input."""
    return {
        CONF_NAME: "Spooky",
        CONF_LIGHTS: ["light.one", "light.two"],
        CONF_CHANGE_AMOUNT: "3",
        CONF_TRANSITION: "1",
        CONF_CHANGE_FREQUENCY: "1",
        CONF_BRIGHTNESS: "255",
        CONF_COLORS: [{"color_type": "rgb_color", "color": [255, 0, 0]}],
    }


def test_normalize_scene_input_clamps_change_amount_to_all() -> None:
    """Normalize change_amount larger than selected lights to all."""
    result = normalize_scene_input(_base_input())

    assert result[CONF_CHANGE_AMOUNT] == "all"


def test_normalize_scene_input_adds_defaults() -> None:
    """Add integration defaults exactly once in shared normalization."""
    result = normalize_scene_input(_base_input())

    assert result["animate_brightness"] is DEFAULT_ANIMATE_BRIGHTNESS
    assert result["animate_color"] is DEFAULT_ANIMATE_COLOR
    assert result["change_sequence"] is DEFAULT_CHANGE_SEQUENCE
    assert result["ignore_off"] is DEFAULT_IGNORE_OFF
    assert result["priority"] == DEFAULT_PRIORITY
    assert result["restore"] is DEFAULT_RESTORE
    assert result["restore_power"] is DEFAULT_RESTORE_POWER


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (CONF_CHANGE_AMOUNT, "bad", "change_amount_not_int_or_all"),
        (CONF_TRANSITION, "[1, bad]", "transition_not_int_or_range"),
        (CONF_CHANGE_FREQUENCY, "61", "change_frequency_not_int_or_range"),
        (CONF_BRIGHTNESS, "300", "brightness_not_int_or_range"),
    ],
)
def test_normalize_scene_input_reports_specific_errors(
    field: str, value: object, message: str
) -> None:
    """Return the same error keys used by config and options flows."""
    data = _base_input()
    data[field] = value

    with pytest.raises(vol.Invalid, match=message):
        normalize_scene_input(data)


def test_validate_start_service_data_accepts_normalized_scene_data() -> None:
    """Validate start service data through the shared runtime schema."""
    result = validate_start_service_data(_base_input())

    assert result[CONF_NAME] == "Spooky"
    assert result[CONF_CHANGE_AMOUNT] == "all"


def test_build_colors_from_rgb_dict_converts_to_color_list() -> None:
    """Convert config-flow RGB UI storage into runtime colors."""
    result = build_colors_from_rgb_dict(
        {
            "one": {"color": [1, 2, 3], "brightness": 200, "weight": 10},
            "two": {"color": [4, 5, 6], "brightness": [100, 255], "weight": 5},
        }
    )

    assert result == [
        {"color": [1, 2, 3], "brightness": 200, "weight": 10, "color_type": "rgb_color"},
        {
            "color": [4, 5, 6],
            "brightness": [100, 255],
            "weight": 5,
            "color_type": "rgb_color",
        },
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/pytest tests/test_scene_config.py -q
```

Expected: FAIL because `scene_config.py` does not exist.

- [ ] **Step 3: Create shared config module**

Create `custom_components/animated_scenes/scene_config.py`:

```python
"""Shared scene configuration normalization for Animated Scenes."""

from __future__ import annotations

import copy
from numbers import Number
from typing import Any

import voluptuous as vol

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
    vol.Optional(CONF_COLOR_NEARBY_COLORS, default=DEFAULT_COLOR_NEARBY_COLORS): vol.Range(
        min=0, max=10
    ),
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
        vol.Coerce(float),
        vol.Range(min=CHANGE_FREQUENCY_MIN, max=CHANGE_FREQUENCY_MAX),
        vol.All([vol.Coerce(float), vol.Range(min=CHANGE_FREQUENCY_MIN, max=CHANGE_FREQUENCY_MAX)]),
    ),
    vol.Optional(CONF_CHANGE_AMOUNT, default=DEFAULT_CHANGE_AMOUNT): vol.Any(
        "all",
        vol.All(vol.Coerce(int), vol.Range(min=CHANGE_AMOUNT_MIN, max=CHANGE_AMOUNT_MAX)),
        vol.All(
            [
                vol.All(vol.Coerce(int), vol.Range(min=CHANGE_AMOUNT_MIN, max=CHANGE_AMOUNT_MAX))
            ]
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
        vol.Optional("animated_scene_switch"): cv.entity_id,
    }
)
REMOVE_LIGHTS_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LIGHTS): cv.entity_ids,
        vol.Optional("skip_restore", default=False): bool,
    }
)


def is_int(value: Any) -> tuple[bool, Any]:
    """Return whether value is integer-like and its normalized value."""
    if value is None or not isinstance(value, Number | str):
        return False, value
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False, value
    if parsed.is_integer():
        return True, int(parsed)
    return False, value


def list_or_int_to_str(value: Any) -> Any:
    """Return UI string representation for an int or two-item list."""
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
        raise vol.Invalid("must_select_lights")

    change_ok, change_value = is_int_list_or_all(
        normalized.get(CONF_CHANGE_AMOUNT), CHANGE_AMOUNT_MIN, CHANGE_AMOUNT_MAX
    )
    if not change_ok:
        raise vol.Invalid(ERROR_CHANGE_AMOUNT_NOT_INT_OR_ALL)
    normalized[CONF_CHANGE_AMOUNT] = override_max_change_amount(
        change_value, len(normalized.get(CONF_LIGHTS, []))
    )

    transition_ok, transition_value = is_int_or_list(
        normalized.get(CONF_TRANSITION), TRANSITION_MIN, TRANSITION_MAX
    )
    if not transition_ok:
        raise vol.Invalid(ERROR_TRANSITION_NOT_INT_OR_RANGE)
    normalized[CONF_TRANSITION] = transition_value

    frequency_ok, frequency_value = is_int_or_list(
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
    return validate_start_service_data(normalized)


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
```

- [ ] **Step 4: Update imports without changing behavior**

In `custom_components/animated_scenes/animations.py`, remove local definitions of `COLOR_GROUP_SCHEMA`, `START_SERVICE_CONFIG`, `START_SERVICE_SCHEMA`, `STOP_SERVICE_SCHEMA`, `ADD_LIGHTS_TO_ANIMATION_SERVICE_SCHEMA`, and `REMOVE_LIGHTS_SERVICE_SCHEMA`. Import them instead:

```python
from .scene_config import (
    ADD_LIGHTS_TO_ANIMATION_SERVICE_SCHEMA,
    REMOVE_LIGHTS_SERVICE_SCHEMA,
    START_SERVICE_CONFIG,
    START_SERVICE_SCHEMA,
    STOP_SERVICE_SCHEMA,
)
```

In `custom_components/animated_scenes/config_flow.py`, import shared helpers:

```python
from .scene_config import (
    build_colors_from_rgb_dict,
    clean_color_rgb_dict,
    is_int_or_list,
    is_int_list_or_all,
    list_or_int_to_str,
    normalize_scene_input,
    override_max_change_amount,
)
```

Replace calls to old helper names:

```python
_if_list_or_int_to_str(...) -> list_or_int_to_str(...)
_is_int_or_list(...) -> is_int_or_list(...)
_is_int_list_or_all(...) -> is_int_list_or_all(...)
_overrride_max_change_amount(...) -> override_max_change_amount(...)
_clean_color_rgb_dict(...) -> clean_color_rgb_dict(...)
```

Then remove the old helper function definitions from `config_flow.py`: `_if_list_or_int_to_str`, `_strlist_to_list`, `_is_int`, `_is_int_or_list`, `_is_int_list_or_all`, `_overrride_max_change_amount`, and `_clean_color_rgb_dict`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/pytest tests/test_scene_config.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/animated_scenes/scene_config.py custom_components/animated_scenes/config_flow.py custom_components/animated_scenes/animations.py tests/test_scene_config.py
git commit -m "refactor: share animated scene config normalization"
```

---

### Task 4: Register Service Schemas and Align Service UI Contract

**Files:**

- Modify: `custom_components/animated_scenes/__init__.py`
- Modify: `custom_components/animated_scenes/services.yaml`
- Test: `tests/test_animations.py`

- [ ] **Step 1: Write failing service registration test**

Create `tests/test_animations.py`:

```python
"""Tests for Animated Scenes runtime manager and service setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.animated_scenes import async_setup
from custom_components.animated_scenes.const import DOMAIN


@pytest.mark.asyncio
async def test_services_register_with_schema(hass: HomeAssistant) -> None:
    """Register all Animated Scenes services with voluptuous schemas."""
    with patch.object(hass.services, "async_register", wraps=hass.services.async_register) as register:
        assert await async_setup(hass, {}) is True

    registrations = {
        call.args[1]: call.kwargs.get("schema")
        for call in register.mock_calls
        if call.args and call.args[0] == DOMAIN
    }

    assert set(registrations) == {
        "start_animation",
        "stop_animation",
        "remove_lights",
        "add_lights_to_animation",
    }
    assert registrations["start_animation"] is not None
    assert registrations["stop_animation"] is not None
    assert registrations["remove_lights"] is not None
    assert registrations["add_lights_to_animation"] is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/pytest tests/test_animations.py::test_services_register_with_schema -q
```

Expected: FAIL because current `async_register()` calls do not pass `schema=`.

- [ ] **Step 3: Register schemas in setup**

Modify `custom_components/animated_scenes/__init__.py` imports:

```python
from .scene_config import (
    ADD_LIGHTS_TO_ANIMATION_SERVICE_SCHEMA,
    REMOVE_LIGHTS_SERVICE_SCHEMA,
    START_SERVICE_SCHEMA,
    STOP_SERVICE_SCHEMA,
)
```

Replace the four service registrations:

```python
hass.services.async_register(
    DOMAIN, "start_animation", start_animation, schema=START_SERVICE_SCHEMA
)
hass.services.async_register(DOMAIN, "stop_animation", stop_animation, schema=STOP_SERVICE_SCHEMA)
hass.services.async_register(
    DOMAIN, "remove_lights", remove_lights, schema=REMOVE_LIGHTS_SERVICE_SCHEMA
)
hass.services.async_register(
    DOMAIN,
    "add_lights_to_animation",
    add_lights_to_animation,
    schema=ADD_LIGHTS_TO_ANIMATION_SERVICE_SCHEMA,
)
```

- [ ] **Step 4: Align `services.yaml` limits**

In `custom_components/animated_scenes/services.yaml`:

```yaml
    priority:
      required: false
      default: 0
```

```yaml
    transition:
      required: false
      default: 1
      selector:
        number:
          min: 0
          max: 6553
          step: 0.1
          unit_of_measurement: seconds
```

```yaml
    change_frequency:
      required: false
      default: 1
      selector:
        number:
          min: 0
          max: 60
          step: 0.1
          unit_of_measurement: seconds
```

Set `required: false` for all start fields that have defaults: `priority`, `transition`, `change_frequency`, `ignore_off`, `restore`, `restore_power`, `change_sequence`, `animate_brightness`, `animate_color`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/pytest tests/test_animations.py::test_services_register_with_schema -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/animated_scenes/__init__.py custom_components/animated_scenes/services.yaml tests/test_animations.py
git commit -m "fix: validate animated scenes service calls at registration"
```

---

### Task 5: Fix Animation Manager Ownership Cleanup

**Files:**

- Modify: `custom_components/animated_scenes/animations.py`
- Test: `tests/test_animations.py`

- [ ] **Step 1: Add failing ownership cleanup tests**

Append to `tests/test_animations.py`:

```python
from custom_components.animated_scenes.animations import Animation, Animations


def _animation_config(name: str, lights: list[str], priority: int = 0) -> dict[str, object]:
    """Return a valid runtime animation config."""
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


@pytest.mark.asyncio
async def test_release_light_removes_owner_when_no_successor(hass: HomeAssistant) -> None:
    """Release removes stale light_owner entries when no animation remains."""
    manager = Animations(hass)
    Animations.instance = manager
    hass.states.async_set("light.one", "on", {"brightness": 100, "color_mode": "rgb"})
    animation = Animation(hass, _animation_config("Spooky", ["light.one"]))
    manager.animations[animation.name] = animation
    manager.light_owner["light.one"] = animation
    manager._light_animations["light.one"] = [animation]  # noqa: SLF001
    manager.store_state("light.one")

    await manager.release_light(animation, "light.one")

    assert "light.one" not in manager.light_owner
    assert "light.one" not in manager._light_animations  # noqa: SLF001
    assert "light.one" not in manager.states


@pytest.mark.asyncio
async def test_release_light_hands_owner_to_next_priority(hass: HomeAssistant) -> None:
    """Release transfers ownership to the next highest-priority animation."""
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/pytest tests/test_animations.py::test_release_light_removes_owner_when_no_successor tests/test_animations.py::test_release_light_hands_owner_to_next_priority -q
```

Expected: first test FAILS because `light_owner` is not deleted.

- [ ] **Step 3: Implement cleanup**

In `custom_components/animated_scenes/animations.py`, replace `release_light()` body with:

```python
async def release_light(
    self,
    animation: Animation,
    entity_id: str,
    skip_ownership: bool = False,
    skip_restore: bool = False,
) -> None:
    """Release ownership of a light for a given animation."""
    animations_for_light = self._light_animations.get(entity_id, [])
    if animation in animations_for_light:
        animations_for_light.remove(animation)

    current_owner = self.light_owner.get(entity_id)
    if current_owner is not None and current_owner != animation:
        _LOGGER.info(
            "Not releasing light %s as it is owned by another animation %s",
            entity_id,
            current_owner.name,
        )
        return

    if animations_for_light and not skip_ownership:
        light_owner = self.refresh_animation_for_light(entity_id)
        if light_owner:
            self.light_owner[entity_id] = light_owner
            _LOGGER.info("Changing owner from %s to %s", animation.name, light_owner.name)
            return

    if animation.restore and not skip_restore and entity_id in self.states:
        previous_state = self.states[entity_id]
        if previous_state.state == "on":
            await safe_call(
                self.hass,
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                self.build_attributes_from_state(previous_state),
            )
        elif animation.restore_power:
            await safe_call(self.hass, LIGHT_DOMAIN, SERVICE_TURN_OFF, {"entity_id": entity_id})

    self.states.pop(entity_id, None)
    self.light_owner.pop(entity_id, None)
    if not animations_for_light:
        self._light_animations.pop(entity_id, None)
    self.refresh_listener()
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/pytest tests/test_animations.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/animated_scenes/animations.py tests/test_animations.py
git commit -m "fix: clear stale animated scene light ownership"
```

---

### Task 6: Align Config Entry Reload/Unload with Runtime Cleanup

**Files:**

- Modify: `custom_components/animated_scenes/animations.py`
- Modify: `custom_components/animated_scenes/__init__.py`
- Test: `tests/test_animations.py`

- [ ] **Step 1: Add failing lifecycle cleanup tests**

Append to `tests/test_animations.py`:

```python
from homeassistant.config_entries import ConfigEntry

from custom_components.animated_scenes import async_unload_entry
from custom_components.animated_scenes.const import CONF_ENTITY_TYPE, ENTITY_SCENE


@pytest.mark.asyncio
async def test_manager_stop_by_name_stops_running_animation(hass: HomeAssistant) -> None:
    """Manager can stop a scene by name during config-entry unload."""
    manager = Animations(hass)
    animation = AsyncMock()
    animation.name = "Spooky"
    manager.animations["Spooky"] = animation

    await manager.stop_by_name("Spooky")

    animation.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_unload_entry_stops_scene_animation(hass: HomeAssistant) -> None:
    """Unloading a scene config entry stops its matching runtime animation."""
    manager = Animations(hass)
    Animations.instance = manager
    animation = AsyncMock()
    animation.name = "Spooky"
    manager.animations["Spooky"] = animation
    entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Spooky",
        data={CONF_ENTITY_TYPE: ENTITY_SCENE, "name": "Spooky"},
        source="user",
        entry_id="entry-spooky",
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = dict(entry.data)
    with patch.object(hass.config_entries, "async_unload_platforms", return_value=True):
        assert await async_unload_entry(hass, entry) is True

    animation.stop.assert_awaited_once()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/pytest tests/test_animations.py::test_manager_stop_by_name_stops_running_animation tests/test_animations.py::test_unload_entry_stops_scene_animation -q
```

Expected: FAIL because `stop_by_name()` does not exist and unload does not stop runtime animations.

- [ ] **Step 3: Add manager cleanup methods**

In `custom_components/animated_scenes/animations.py`, add these methods to `Animations`:

```python
async def stop_by_name(self, name: str) -> None:
    """Stop a running animation by name if it exists."""
    animation = self.animations.get(name)
    if animation is not None:
        await animation.stop()


async def stop_all(self) -> None:
    """Stop all running animations managed by this integration."""
    animations = list(self.animations.values())
    await asyncio.gather(*(animation.stop() for animation in animations))


def clear_runtime_state(self) -> None:
    """Clear listeners and runtime ownership maps."""
    if self._external_light_listener is not None:
        self._external_light_listener()
        self._external_light_listener = None
    self.animations.clear()
    self.states.clear()
    self._light_animations.clear()
    self.light_owner.clear()
    self._conflicted_lights.clear()
```

- [ ] **Step 4: Stop scene runtime on unload**

In `custom_components/animated_scenes/__init__.py`, before platform unload in `async_unload_entry()`:

```python
manager = Animations.instance
if manager and entry.data.get(CONF_ENTITY_TYPE, ENTITY_SCENE) == ENTITY_SCENE:
    name = entry.data.get("name")
    if name:
        await manager.stop_by_name(name)
```

After data removal, if no config entries for the domain remain loaded, call:

```python
if unload_ok and not hass.data.get(DOMAIN):
    if Animations.instance:
        await Animations.instance.stop_all()
        Animations.instance.clear_runtime_state()
    Animations.instance = None
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/pytest tests/test_animations.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/animated_scenes/__init__.py custom_components/animated_scenes/animations.py tests/test_animations.py
git commit -m "fix: stop animations during config entry unload"
```

---

### Task 7: Make Switch Entity Ready and Event-Driven

**Files:**

- Modify: `custom_components/animated_scenes/switch.py`
- Modify: `custom_components/animated_scenes/animations.py`
- Test: `tests/test_switch.py`

- [ ] **Step 1: Write failing switch tests**

Create `tests/test_switch.py`:

```python
"""Tests for Animated Scene switch entities."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from homeassistant.core import HomeAssistant

from custom_components.animated_scenes.animations import Animations
from custom_components.animated_scenes.const import (
    CONF_COLOR_RGB_DICT,
    CONF_COLOR_SELECTOR_MODE,
    COLOR_SELECTOR_RGB_UI,
    EVENT_NAME_CHANGE,
    EVENT_STATE_STARTED,
    EVENT_STATE_STOPPED,
)
from custom_components.animated_scenes.switch import AnimatedSceneSwitch


def _switch_config() -> dict[str, object]:
    """Return a valid switch config-entry payload."""
    return {
        "name": "Spooky",
        "icon": "mdi:lightbulb",
        "lights": ["light.one"],
        "colors": {},
        CONF_COLOR_SELECTOR_MODE: COLOR_SELECTOR_RGB_UI,
        CONF_COLOR_RGB_DICT: {
            "one": {"color": [255, 0, 0], "brightness": 255, "weight": 10}
        },
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
        "priority": 0,
        "entity_type": "scene",
    }


@pytest.mark.asyncio
async def test_switch_animation_config_ready_in_constructor(hass: HomeAssistant) -> None:
    """Switch has a prepared animation config before it can be turned on."""
    switch = AnimatedSceneSwitch(hass, _switch_config(), "entry-id")

    assert switch._animation_config["colors"] == [  # noqa: SLF001
        {
            "color": [255, 0, 0],
            "brightness": 255,
            "weight": 10,
            "color_type": "rgb_color",
        }
    ]


@pytest.mark.asyncio
async def test_switch_tracks_animation_events(hass: HomeAssistant) -> None:
    """Switch state follows service-started and service-stopped events."""
    switch = AnimatedSceneSwitch(hass, _switch_config(), "entry-id")
    switch.hass = hass
    switch.async_write_ha_state = AsyncMock()  # type: ignore[method-assign]
    await switch.async_added_to_hass()

    hass.bus.async_fire(
        EVENT_NAME_CHANGE,
        {"animation": "Spooky", "state": EVENT_STATE_STARTED},
    )
    await hass.async_block_till_done()

    assert switch.is_on is True
    switch.async_write_ha_state.assert_called()

    hass.bus.async_fire(
        EVENT_NAME_CHANGE,
        {"animation": "Spooky", "state": EVENT_STATE_STOPPED},
    )
    await hass.async_block_till_done()

    assert switch.is_on is False
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/pytest tests/test_switch.py -q
```

Expected: FAIL because `_animation_config` is built in a background task and switch does not subscribe to events.

- [ ] **Step 3: Make config construction synchronous**

In `custom_components/animated_scenes/switch.py`, replace constructor scheduling:

```python
self._animation_config: dict[str, Any] = self._build_animation_config()
```

Add:

```python
def _build_animation_config(self) -> dict[str, Any]:
    """Build runtime animation config from config-entry data."""
    if self._config.get(CONF_COLOR_SELECTOR_MODE) == COLOR_SELECTOR_RGB_UI:
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
```

Import `build_colors_from_rgb_dict`:

```python
from .scene_config import build_colors_from_rgb_dict
```

Remove `_async_setup_animation_fields()` and `_async_build_colors_from_rgb_dict()`.

- [ ] **Step 4: Subscribe to animation events**

Add property and lifecycle method to `AnimatedSceneSwitch`:

```python
@property
def is_on(self) -> bool:
    """Return whether the animated scene is currently active."""
    return self._attr_is_on


async def async_added_to_hass(self) -> None:
    """Subscribe to animation lifecycle events."""
    self.async_on_remove(
        self.hass.bus.async_listen(EVENT_NAME_CHANGE, self._handle_animation_event)
    )


@callback
def _handle_animation_event(self, event: Event) -> None:
    """Update switch state when services start or stop this animation."""
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
```

Add imports:

```python
from homeassistant.core import Event, callback

from .const import EVENT_NAME_CHANGE, EVENT_STATE_STARTED, EVENT_STATE_STOPPED
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/pytest tests/test_switch.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/animated_scenes/switch.py tests/test_switch.py
git commit -m "fix: make animated scene switches event driven"
```

---

### Task 8: Make Activity Sensor Unique and Event-Driven

**Files:**

- Modify: `custom_components/animated_scenes/config_flow.py`
- Modify: `custom_components/animated_scenes/sensor.py`
- Test: `tests/test_sensor.py`

- [ ] **Step 1: Write failing sensor tests**

Create `tests/test_sensor.py`:

```python
"""Tests for Animated Scenes activity sensor."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.animated_scenes.animations import Animations
from custom_components.animated_scenes.config_flow import AnimatedScenesConfigFlow
from custom_components.animated_scenes.const import (
    CONF_ENTITY_TYPE,
    DOMAIN,
    ENTITY_ACTIVITY_SENSOR,
    EVENT_NAME_CHANGE,
    EVENT_STATE_STARTED,
)
from custom_components.animated_scenes.sensor import AnimatedScenesSensor


@pytest.mark.asyncio
async def test_activity_sensor_writes_state_on_animation_event(hass: HomeAssistant) -> None:
    """Activity sensor updates immediately when animation events fire."""
    manager = Animations(hass)
    Animations.instance = manager
    sensor = AnimatedScenesSensor(hass)
    sensor.hass = hass
    sensor.async_write_ha_state = AsyncMock()  # type: ignore[method-assign]
    await sensor.async_added_to_hass()

    hass.bus.async_fire(EVENT_NAME_CHANGE, {"animation": "Spooky", "state": EVENT_STATE_STARTED})
    await hass.async_block_till_done()

    sensor.async_write_ha_state.assert_called_once()


@pytest.mark.asyncio
async def test_activity_sensor_duplicate_check_uses_config_entries(hass: HomeAssistant) -> None:
    """Config flow detects existing activity sensor from config entries."""
    entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Activity Sensor",
        data={CONF_ENTITY_TYPE: ENTITY_ACTIVITY_SENSOR},
        source="user",
        entry_id="activity",
    )
    entry.add_to_hass(hass)
    flow = AnimatedScenesConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()

    assert result["type"] == "form"
    assert result["step_id"] == "scene"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/pytest tests/test_sensor.py -q
```

Expected: FAIL because the sensor does not subscribe to events and duplicate check only uses `hass.data`.

- [ ] **Step 3: Update sensor lifecycle**

In `custom_components/animated_scenes/sensor.py`, add imports:

```python
from homeassistant.core import Event, callback

from .const import DEFAULT_ACTIVITY_SENSOR_ICON, EVENT_NAME_CHANGE
```

Remove `self._scan_interval`.

Add to `AnimatedScenesSensor`:

```python
@property
def should_poll(self) -> bool:
    """Disable polling because animation events push updates."""
    return False


async def async_added_to_hass(self) -> None:
    """Subscribe to animation lifecycle events."""
    self.async_on_remove(
        self.hass.bus.async_listen(EVENT_NAME_CHANGE, self._handle_animation_event)
    )


@callback
def _handle_animation_event(self, _: Event) -> None:
    """Write sensor state immediately after animation changes."""
    self.async_write_ha_state()
```

- [ ] **Step 4: Update duplicate check**

In `custom_components/animated_scenes/config_flow.py`, replace activity sensor existence check in `async_step_user()` with:

```python
activity_sensor_exists = any(
    entry.data.get(CONF_ENTITY_TYPE, ENTITY_SCENE) == ENTITY_ACTIVITY_SENSOR
    for entry in self.hass.config_entries.async_entries(DOMAIN)
)
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/pytest tests/test_sensor.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/animated_scenes/config_flow.py custom_components/animated_scenes/sensor.py tests/test_sensor.py
git commit -m "fix: make animated scenes activity sensor event driven"
```

---

### Task 9: Add Diagnostics and HA Support Metadata

**Files:**

- Create: `custom_components/animated_scenes/diagnostics.py`
- Modify: `custom_components/animated_scenes/switch.py`
- Modify: `custom_components/animated_scenes/sensor.py`
- Modify: `custom_components/animated_scenes/translations/en.json`
- Test: `tests/test_diagnostics.py`

- [ ] **Step 1: Write failing diagnostics test**

Create `tests/test_diagnostics.py`:

```python
"""Tests for Animated Scenes diagnostics."""

from __future__ import annotations

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.animated_scenes.animations import Animations
from custom_components.animated_scenes.const import DOMAIN
from custom_components.animated_scenes.diagnostics import async_get_config_entry_diagnostics


@pytest.mark.asyncio
async def test_diagnostics_redacts_entity_ids_and_reports_runtime(hass: HomeAssistant) -> None:
    """Diagnostics include runtime summary without exposing entity ids."""
    manager = Animations(hass)
    Animations.instance = manager
    manager.light_owner["light.kitchen"] = object()  # type: ignore[assignment]
    entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Spooky",
        data={"name": "Spooky", "lights": ["light.kitchen"], "colors": []},
        source="user",
        entry_id="spooky",
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["data"]["lights"] == "**REDACTED**"
    assert diagnostics["runtime"]["active_light_count"] == 1
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/pytest tests/test_diagnostics.py -q
```

Expected: FAIL because `diagnostics.py` does not exist.

- [ ] **Step 3: Create diagnostics module**

Create `custom_components/animated_scenes/diagnostics.py`:

```python
"""Diagnostics support for Animated Scenes."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .animations import Animations

TO_REDACT = {"lights", "entity_id", "animated_scene_switch"}


def _redact(value: Any) -> Any:
    """Redact entity identifiers from diagnostics payloads."""
    if isinstance(value, dict):
        return {key: ("**REDACTED**" if key in TO_REDACT else _redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for an Animated Scenes config entry."""
    manager = Animations.instance
    runtime = {
        "active_animation_count": len(manager.animations) if manager else 0,
        "active_light_count": len(manager.light_owner) if manager else 0,
        "stored_state_count": len(manager.states) if manager else 0,
    }
    return {
        "entry": {
            "title": entry.title,
            "data": _redact(dict(entry.data)),
            "options": _redact(dict(entry.options)),
        },
        "runtime": runtime,
    }
```

- [ ] **Step 4: Add device info or correct metadata**

If keeping `integration_type: "device"`, add this property to both `AnimatedSceneSwitch` and `AnimatedScenesSensor`:

```python
@property
def device_info(self) -> dict[str, object]:
    """Return device info for the Animated Scenes integration device."""
    return {
        "identifiers": {(DOMAIN, "animated_scenes")},
        "name": "Animated Scenes",
        "manufacturer": "Animated Scenes",
    }
```

Import `DOMAIN` where needed.

If deciding not to expose a device, change `manifest.json`:

```json
"integration_type": "helper"
```

Use only one of these approaches. Prefer `device_info` if Home Assistant accepts the current custom-integration metadata.

- [ ] **Step 5: Add repair issue translations**

In `custom_components/animated_scenes/translations/en.json`, add top-level `issues`:

```json
"issues": {
  "deprecated_yaml": {
    "title": "Animated Scenes YAML configuration is deprecated",
    "description": "The {integration_title} YAML configuration for {domain} is deprecated. Import the entry through the integration UI and manage it from Settings > Devices & Services."
  }
}
```

Keep valid JSON punctuation.

- [ ] **Step 6: Run focused tests**

Run:

```bash
./.venv/bin/pytest tests/test_diagnostics.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add custom_components/animated_scenes/diagnostics.py custom_components/animated_scenes/switch.py custom_components/animated_scenes/sensor.py custom_components/animated_scenes/translations/en.json custom_components/animated_scenes/manifest.json tests/test_diagnostics.py
git commit -m "feat: add animated scenes diagnostics and support metadata"
```

---

### Task 10: Docstring Modernization

**Files:**

- Modify: `custom_components/animated_scenes/__init__.py`
- Modify: `custom_components/animated_scenes/animations.py`
- Modify: `custom_components/animated_scenes/config_flow.py`
- Modify: `custom_components/animated_scenes/const.py`
- Modify: `custom_components/animated_scenes/diagnostics.py`
- Modify: `custom_components/animated_scenes/scene_config.py`
- Modify: `custom_components/animated_scenes/sensor.py`
- Modify: `custom_components/animated_scenes/service.py`
- Modify: `custom_components/animated_scenes/switch.py`
- Modify: `tests/conftest.py`
- Modify: `tests/test_animations.py`
- Modify: `tests/test_diagnostics.py`
- Modify: `tests/test_scene_config.py`
- Modify: `tests/test_sensor.py`
- Modify: `tests/test_switch.py`

- [ ] **Step 1: Run docstring lint to identify gaps**

Run:

```bash
./.venv/bin/ruff check custom_components/animated_scenes tests --select D --output-format=concise
```

Expected before implementation: FAIL if any file, class, method, private method, nested method, fixture, helper, or test is missing a docstring or has a malformed docstring.

- [ ] **Step 2: Update module and class docstrings**

For every Python file under `custom_components/animated_scenes/` and `tests/`, ensure the module docstring answers:

```text
What responsibility does this file own?
What Home Assistant surface or runtime behavior does it support?
What should future maintainers look here for, and what should they not put here?
```

For every class docstring, include the class role, key collaborators, lifecycle expectations, and important invariants. Use this style for runtime classes:

```python
class Animations:
    """Coordinate running Animated Scenes and light ownership.

    The manager owns runtime-only state for active animations, stored light
    states, and the mapping from light entity IDs to the animation currently
    allowed to update them. It is intentionally separate from config-entry
    persistence; callers must stop or clear the manager during config-entry
    unloads to avoid stale ownership surviving reloads.
    """
```

Use this style for entity classes:

```python
class AnimatedSceneSwitch(SwitchEntity):
    """Represent one configured animation as a Home Assistant switch.

    The switch adapts persisted config-entry data into runtime animation
    config and mirrors animation lifecycle events so UI state stays aligned
    whether the animation was started from the entity or from a domain
    service call.
    """
```

- [ ] **Step 3: Update method docstrings in Google Style**

For every public, private, and nested method or function, write a meaningful Google Style docstring. Include sections only when applicable:

```python
def normalize_scene_input(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize user-facing scene input into runtime service data.

    Config and options flows accept several user-friendly forms, including
    integer-like strings and two-item range strings. This function applies
    integration defaults, coerces those forms into runtime values, clamps
    change amounts to the selected light count, and validates the final data
    against the same schema used by service calls.

    Args:
        data: Raw scene data from a config flow, options flow, YAML import, or
            service call.

    Returns:
        A normalized copy of the input suitable for constructing an
        ``Animation``.

    Raises:
        vol.Invalid: If any numeric/range field is malformed, no lights are
            selected, or the final runtime schema rejects the data.
    """
```

For side-effect-only methods, explain the side effects instead of writing a trivial return sentence:

```python
async def stop_by_name(self, name: str) -> None:
    """Stop a running animation during config-entry unload or reload.

    This method is idempotent so lifecycle cleanup can call it even when the
    scene is not active. When the animation exists, stopping it releases light
    ownership and restores stored light state through the normal animation
    shutdown path.

    Args:
        name: Configured animation name from the scene config entry.
    """
```

For tests, explain the protected behavior:

```python
def test_release_light_removes_owner_when_no_successor(hass: HomeAssistant) -> None:
    """Protect against stale light ownership after the final animation stops."""
```

- [ ] **Step 4: Remove misleading or low-value docstrings**

Replace docstrings that only repeat the name or type signature. Examples that must be rewritten:

```python
"""Return the animation's configured name."""
"""Initialize."""
"""Options callback."""
"""Return None."""
```

Use docstrings that capture invariants, HA lifecycle expectations, or why the method exists. Do not add filler just to satisfy lint.

- [ ] **Step 5: Run docstring lint**

Run:

```bash
./.venv/bin/ruff check custom_components/animated_scenes tests --select D --output-format=concise
```

Expected: PASS.

- [ ] **Step 6: Run full focused validation**

Run:

```bash
./.venv/bin/pytest
./.venv/bin/mypy custom_components/animated_scenes
```

Expected: both commands exit `0`.

- [ ] **Step 7: Commit**

```bash
git add custom_components/animated_scenes tests
git commit -m "docs: improve animated scenes python docstrings"
```

---

### Task 11: Documentation and Final Verification

**Files:**

- Modify: `README.MD`
- Modify: `MEMORY.md`

- [ ] **Step 1: Update README behavior notes**

In `README.MD`, update the activity sensor paragraph around line 187 from polling language to event-driven language:

```markdown
The Activity sensor updates when animations start or stop. The attributes are:

- active: A list of currently running animations.
- active_lights: A list of lights currently in use by animations.
```

Add a service limits subsection after "Automation Configuration":

```markdown
### Service Limits

The integration validates service calls before runtime:

- `transition`: 0 to 6553 seconds
- `change_frequency`: 0 to 60 seconds
- `change_amount`: an integer, a two-item range like `[1, 3]`, or `all`
- `brightness`: 0 to 255, or a two-item range like `[70, 255]`

Values configured through the UI and values passed to services use the same validation rules.
```

Add a reload behavior note:

```markdown
When a scene config entry is reloaded or unloaded, any matching running animation is stopped and its light ownership is released before the entity is removed.
```

Add a development tooling note:

```markdown
## Development

- Use Python 3.14.
- Install local development dependencies from `pyproject.toml` with `./.venv/bin/python -m pip install -e ".[dev,lint,test]"`.
- Use `prek` for hooks; hook configuration lives in `prek.toml`.
- This repository intentionally does not use `requirements*.txt` files or `.pre-commit-config.yaml`.
- Future agent instructions live in `AGENTS.md`.
- Python files must include meaningful file, class, and method docstrings. Method docstrings, including private and nested methods, use Google Style and explain intent, invariants, side effects, arguments, raised exceptions, and return semantics where relevant.
```

- [ ] **Step 2: Update project memory**

Append to `MEMORY.md`:

```markdown
## 2026-06-05

- Created `docs/superpowers/plans/2026-06-05-animated-scenes-functionality-optimization.md` for implementing the repo functionality optimization review.
- Scope includes standalone `AGENTS.md`, Python 3.14, dependency consolidation into `pyproject.toml`, `prek.toml` replacing `.pre-commit-config.yaml`, meaningful Google Style docstrings for files/classes/methods including private and nested methods, lifecycle cleanup, stale light-owner cleanup, event-driven switch/sensor state, shared config validation, service schema registration, diagnostics, support metadata, tests, and README updates.
```

- [ ] **Step 3: Run full verification**

Run:

```bash
./.venv/bin/prek run -a
./.venv/bin/pytest
./.venv/bin/mypy custom_components/animated_scenes
```

Expected: all commands exit `0`. If `prek` reports cache or `.DS_Store` warnings but exits `0`, treat those warnings as non-blocking.

- [ ] **Step 4: Run branch hard gate**

Run:

```bash
git status --short --branch
git branch -vv
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

Expected:

```text
## review/functionality-optimization-audit...origin/review/functionality-optimization-audit
origin/review/functionality-optimization-audit
```

- [ ] **Step 5: Commit**

```bash
git add README.MD MEMORY.md
git commit -m "docs: document animated scenes runtime improvements"
```

---

## Self-Review

**Spec coverage:** The plan covers all review findings and requested tooling/documentation updates: standalone `AGENTS.md`, Python 3.14, dependency consolidation into `pyproject.toml`, `prek.toml` replacing `.pre-commit-config.yaml`, meaningful Google Style docstrings for files/classes/methods including private and nested methods, lifecycle cleanup, stale light ownership, switch state and readiness, activity sensor duplicates/reactivity, service/config/runtime contract drift, integration metadata, repair translations, diagnostics, tests, README, and project memory.

**Placeholder scan:** No banned placeholder wording or unspecified test tasks remain. Each code-changing step includes exact files and concrete code or replacement instructions.

**Type consistency:** New helper names are consistent across tasks: `normalize_scene_input`, `validate_start_service_data`, `build_colors_from_rgb_dict`, `clean_color_rgb_dict`, `stop_by_name`, `stop_all`, and `clear_runtime_state`. Docstring lint is explicitly verified with `ruff check --select D`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-05-animated-scenes-functionality-optimization.md`. Two execution options:

**1. Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
