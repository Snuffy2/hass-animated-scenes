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
