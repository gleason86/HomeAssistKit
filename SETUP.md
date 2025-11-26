# Setup Guide

## Prerequisites

- **Python 3.12+** (installed via winget or python.org)
- **Git** (for version control and pre-commit hooks)
- **VS Code or Cursor** (recommended IDE)

## Initial Setup

### 1. Install Python (if not already installed)

**Windows (via winget):**
```powershell
winget install Python.Python.3.12
# Restart your terminal after installation
```

**macOS (via Homebrew):**
```bash
brew install python@3.12
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install python3.12 python3.12-venv python3-pip
```

### 2. Clone and setup virtual environment

```powershell
# Clone the repository
git clone <your-repo-url>
cd ha_brain

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Windows CMD:
.venv\Scripts\activate.bat
# On Linux/Mac:
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

### 3. Install dependencies

```bash
# Install all dependencies including development tools
pip install -e ".[dev]"
```

### 4. Setup pre-commit hooks

```bash
pre-commit install
```

### 5. Open workspace in VS Code/Cursor

- Open `ha.code-workspace` in VS Code or Cursor
- Install recommended extensions when prompted
- The workspace includes pre-configured settings for:
  - Python linting with Ruff
  - Type checking with MyPy
  - YAML validation
  - Testing with pytest

## Development Tools

The following tools are automatically installed with `pip install -e ".[dev]"`:

| Tool | Purpose | Usage |
|------|---------|-------|
| **Ruff** | Fast Python linter & formatter | `ruff check .` / `ruff format .` |
| **MyPy** | Static type checking | `mypy agents integrations` |
| **Pytest** | Testing framework | `pytest` |
| **pytest-cov** | Test coverage | `pytest --cov` |
| **pytest-asyncio** | Async test support | Built-in |
| **pre-commit** | Git hooks | `pre-commit run --all-files` |
| **yamllint** | YAML validation | `yamllint homeassistant-config/` |

### Running linting and formatting

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Type check
mypy agents integrations
```

### Running tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_example.py

# Run in parallel
pytest -n auto
```

## Home Assistant Configuration

### 1. Set up secrets

```bash
# Copy the example secrets file
cp homeassistant-config/secrets.yaml.example homeassistant-config/secrets.yaml

# Edit secrets.yaml with your actual secrets
```

> ⚠️ **Important:** `secrets.yaml` is gitignored to prevent accidental exposure of credentials.

### 2. Sync to your HA instance

Use the provided sync scripts:

```powershell
# Pull latest config from HA
.\sync-pull.ps1

# Push changes to HA
.\sync-push.ps1
```

Or use rsync manually (Linux/Mac):
```bash
rsync -avz homeassistant-config/ user@ha-pi:/config/
```

## Custom Integration Development

### 1. Create a new integration

1. Copy the example integration from `integrations/my_integration/`
2. Update `manifest.json` with your details
3. Implement your API client in `integrations/shared_libs/`

### 2. Install in Home Assistant

```bash
# Copy to your HA custom_components
scp -r integrations/my_integration/custom_components/my_integration user@ha-pi:/config/custom_components/
```

### 3. Restart Home Assistant

Add the integration via Settings > Devices & Services and check logs for errors.

## MCP Server Development

### 1. Configure the MCP server

Navigate to `agents/mcp_ha_server/` and configure:
- Home Assistant URL
- Long-lived access token

### 2. Run the MCP server

```bash
python -m agents.mcp_ha_server.src
```

### 3. Connect to Cursor

Configure Cursor to use your MCP server via the `mcp.json` file.

## VS Code Tasks

The workspace includes pre-configured tasks (Ctrl+Shift+P → "Run Task"):

- **Install Dependencies** - Install all project dependencies
- **Run Tests** - Execute pytest test suite
- **Lint with Ruff** - Check code for issues
- **Format with Ruff** - Auto-format code
- **Type Check with MyPy** - Run static type analysis
- **YAML Lint HA Config** - Validate YAML files
- **Pre-commit Run All** - Run all pre-commit hooks

## Troubleshooting

### Python not found after installation

Restart your terminal or refresh PATH:
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

### Pre-commit hooks failing

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Run hooks manually to see detailed errors
pre-commit run --all-files --verbose
```

### Virtual environment issues

```bash
# Recreate virtual environment
Remove-Item -Recurse -Force .venv  # Windows
# rm -rf .venv  # Linux/Mac

python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -e ".[dev]"
pre-commit install
```
