# Home Assistant Best Practices

## Configuration

- Prefer splitting `configuration.yaml` into **packages** and domain-specific files.
- Avoid copying large examples from the internet without adapting them to existing entities and naming conventions.

## Automations

- Use **`id:`** fields for automations for stable references.
- Prefer **`choose`** and **`conditions`** over copy-pasting multiple similar automations.
- Always include a brief comment at the top of each automation explaining:
  - Trigger(s)
  - Expected behavior
  - Safety considerations (e.g., "don't run at night", "fails open/off")

## Custom integrations

- Keep API clients and business logic in **shared libraries**, not in the HA integration modules.
- Make integrations **async** and use HA helpers (e.g. `DataUpdateCoordinator`) instead of rolling your own loops.
- Use **config flows** for setup; avoid YAML-only configuration for new integrations.
- Add minimal **tests** that validate setup and one or two common flows.

## Naming

- Entity IDs:
  - Use `area_device_function` style where possible, e.g. `hallway_motion_presence`, `bedroom_main_lights`.
- Automations:
  - Use `area-purpose` style, e.g. `hallway_night_lighting`, `office_presence_heating`.

## Changes

- For any change to automations or integrations:
  - Propose a diff.
  - Include a brief test plan:
    - How to validate the behavior.
    - How to revert (which lines to rollback).

