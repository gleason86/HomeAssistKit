# ha-brain

Home Assistant configuration, custom integrations, and agent orchestration repository.

## Structure

- `homeassistant-config/` - All HA config, automations, packages, etc.
- `integrations/` - Custom HA integrations and shared libraries
- `agents/` - MCP servers and agent orchestration code
- `rules/` - Policy & behavior docs for Cursor + agents

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -U pip
   pip install -e ".[dev]"
   ```
3. Open `ha.code-workspace` in VSCode/Cursor

## Recommended VSCode Extensions

- Python
- YAML
- Home Assistant Config Helper
- Home Assistant
- Docker / Dev Containers (optional)

## Development Workflow

1. **Configuration**: Edit files in `homeassistant-config/` and sync to your HA instance
2. **Integrations**: Develop custom components in `integrations/`
3. **Agents**: Build MCP servers in `agents/` to enable AI-assisted management
4. **Rules**: Evolve policy documents in `rules/` to guide agent behavior

## Rules

See `rules/` directory for:
- `AGENT_RULES.md` - Global policy for MCP agents
- `HA_BEST_PRACTICES.md` - HA-specific constraints and patterns
- `.cursor/rules.md` - Cursor's local editing style

