# Credentials

This folder stores sensitive credentials and API keys for the ha_brain project.

## ⚠️ Important

**This folder's contents are ignored by git.** Only this README is tracked.

## Usage

Place your credential files here, for example:
- `ha_api.yaml` - Home Assistant API host and long-lived access token
- `api_keys.yaml` - Third-party API keys (OpenAI, weather services, etc.)
- `*.json` - Service account credentials
- `*.pem` / `*.key` - Private keys and certificates

## Example Structure

```
credentials/
├── README.md              # This file (tracked)
├── ha_api.yaml            # HA API host + token (ignored)
├── api_keys.yaml          # API keys (ignored)
└── google_service.json    # Service accounts (ignored)
```

## Template Files

Consider creating `.example` versions of your credential files with placeholder values that can be safely committed:

```yaml
# api_keys.yaml.example
openai_api_key: "sk-your-key-here"
weather_api_key: "your-weather-api-key"
```
