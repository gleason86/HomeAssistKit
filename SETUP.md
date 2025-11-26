# Setup Guide

## Initial Setup

1. **Initialize Git repository** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: HA brain repository structure"
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/Mac:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -U pip
   pip install -e ".[dev]"
   ```

4. **Open workspace in VSCode/Cursor**:
   - Open `ha.code-workspace` in VSCode or Cursor
   - Install recommended extensions when prompted

## Home Assistant Configuration

1. **Copy your existing HA config**:
   - Copy your `configuration.yaml` and other config files to `homeassistant-config/`
   - Consider splitting into packages over time

2. **Set up secrets**:
   ```bash
   cp homeassistant-config/secrets.yaml.example homeassistant-config/secrets.yaml
   # Edit secrets.yaml with your actual secrets
   ```

3. **Sync to your HA instance**:
   - Use rsync, git pull, or your preferred method to sync `homeassistant-config/` to your Home Assistant instance
   - Example rsync command:
     ```bash
     rsync -avz homeassistant-config/ user@ha-pi:/config/
     ```

## Custom Integration Development

1. **Customize the example integration**:
   - Edit `integrations/my_integration/` to match your needs
   - Update `manifest.json` with your details
   - Implement your API client in `integrations/shared_libs/my_devices/`

2. **Install in Home Assistant**:
   - Copy the integration to your HA's `custom_components/` directory, or
   - Use a symlink (if on the same machine):
     ```bash
     ln -s $(pwd)/integrations/my_integration/custom_components/my_integration /config/custom_components/my_integration
     ```

3. **Test your integration**:
   - Restart Home Assistant
   - Add the integration via Settings > Devices & Services
   - Check logs for any errors

## MCP Server Development

1. **Set up MCP server**:
   - Navigate to `agents/mcp_ha_server/`
   - Install MCP SDK dependencies
   - Configure Home Assistant connection (URL, token)

2. **Implement tools**:
   - Start with read-only tools (list entities, get state)
   - Add write tools with approval mechanisms

3. **Connect to Cursor**:
   - Configure Cursor to use your MCP server
   - Test tools via Cursor's MCP interface

## Next Steps

- Review and customize the rules in `rules/` directory
- Add your first automation in `homeassistant-config/automations/`
- Implement your first custom integration
- Build out the MCP server with your specific tools

