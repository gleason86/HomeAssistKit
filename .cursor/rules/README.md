# HA Brain - Cursor Rules Index

This directory contains rules and guidelines for AI agents working with this Home Assistant repository.

## Rules Files

### 📘 `home-assistant.mdc`

**Home Assistant Configuration & Operations**

Essential patterns for:

- Template sensor best practices (especially energy sensors)
- Configuration management and deployment workflow
- YAML editing guidelines
- Statistics and history management
- Safety and risk assessment

**Key Topics:**

- `state_class: total_increasing` vs `total` for energy sensors
- SCP-based deployment pattern to `192.168.1.110`
- Avoiding negative energy totals
- MCP tool usage with Home Assistant

### 📁 `project-structure.mdc`

**Repository Organization & Workflow**

Covers:

- Three main domains: `homeassistant-config/`, `integrations/`, `agents/`
- Version control and commit guidelines
- Code style (Python, YAML)
- File naming conventions
- Testing and validation procedures

**Key Topics:**

- Scope awareness and domain identification
- Small, focused commits with clear messaging
- Deployment paths and environment differences

### 🤖 `agent-behavior.mdc`

**AI Agent Guidelines & Principles**

Defines:

- Core principles (read before write, environment awareness)
- Tool usage patterns (read-only → write → state-changing)
- Deployment workflow (local edit → SCP → deploy → validate)
- Risk assessment framework
- Communication style and templates

**Key Topics:**

- Never use SSH heredoc for file editing (always SCP)
- Risk categories and blast radius
- Explicit permission for state-changing operations
- Learning and knowledge capture

### 🌐 `environments.mdc`

**Environment Configuration & Shell**

Details:

- Production (Raspberry Pi) vs Development (Windows) environments
- PowerShell as default shell with command syntax
- SSH/SCP patterns from Windows to Linux
- Path handling and cross-platform considerations

**Key Topics:**

- PowerShell gotchas (piping, quoting, command differences)
- Bash vs PowerShell command equivalents
- Remote access patterns and file transfer
- Environment-specific paths and configurations

### 🧪 `testing.mdc`

**Testing & Validation Procedures**

Covers:

- YAML and configuration validation
- Template testing strategies
- Integration and automation testing
- Pre/post-deployment checklists
- Rollback procedures

**Key Topics:**

- Config check before deployment
- Dashboard and statistics validation
- Automated testing tools and patterns
- Safety testing for device-controlling automations

### 🚨 `troubleshooting.mdc`

**Incident Response & Common Issues**

Includes:

- Common failure modes and solutions
- Log analysis and debugging techniques
- Recovery procedures
- Known issues registry

**Key Topics:**

- Negative energy values (root cause & fix)
- Sensor unavailability troubleshooting
- Automation debugging with traces
- Database and performance issues

### 📊 `statistics.mdc`

**Energy Statistics & Data Management**

Comprehensive guide to:

- Energy sensor configuration requirements
- State class usage (`total` vs `total_increasing`)
- InfluxDB integration patterns
- Statistics backfilling procedures
- Energy dashboard setup

**Key Topics:**

- Battery efficiency calculations
- Preventing negative energy totals
- Backfill scripts for historical data
- Utility meters and tariff tracking
- Statistics debugging and correction

## Quick Reference

### Making Configuration Changes

```bash
# 1. Edit locally
vim homeassistant-config/configuration.yaml

# 2. Copy to remote
scp homeassistant-config/configuration.yaml david@192.168.1.110:/home/david/

# 3. Deploy on remote
ssh david@192.168.1.110
sudo cp /home/david/configuration.yaml /opt/homeassistant/config/
docker restart homeassistant
```

### Energy Sensor Template Pattern

```yaml
# ✅ CORRECT - Uses total_increasing
- name: "Energy Loss Sensor"
  state_class: total_increasing # Ignores decreases
  device_class: energy
  unit_of_measurement: "kWh"
  state: >
    {{ (states('sensor.source') | float(0) * 0.05) | round(3) }}
```

### Risk Assessment Template

```markdown
## Risk Assessment

**Blast Radius:** [single sensor | room | house-wide]
**Potential Issues:** [what could go wrong]
**Rollback:** [specific steps to revert]
**Validation:** [how to confirm it worked]
```

## Rules Versioning

These rules are **versioned policy**. When updating:

1. Propose changes as diffs with justification
2. Test the change pattern before committing rule updates
3. Document lessons learned from real incidents
4. Keep rules actionable and specific

## Contributing to Rules

When you discover new patterns or anti-patterns:

1. Add them to the relevant `.mdc` file
2. Include concrete examples
3. Explain why the pattern matters
4. Link to relevant documentation or incidents

---

**Last Updated:** December 10, 2024
**Maintainer:** AI agents + David
