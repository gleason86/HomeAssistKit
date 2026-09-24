---
name: Voice-HA-MCP POC
overview: Append original plan with the new bridge/Windows POC focus and add ruleset work item.
todos:
  - id: write-ruleset
    content: Add voice assistant rules to voice_assistant/.cursor/rules
    status: completed
---

# Plan: Voice Assistant POC (combined)

## Goals

- Build a Windows desktop voice POC: wake word → capture/VAD → Whisper API → ChatGPT API with MCP tools → Home Assistant → Edge TTS.
- Validate and, if needed, improve the MCP→HA bridge (existing `mcp_ha_server`) and scan alternatives.
- Capture consistency rules in `voice_assistant/.cursor/rules` for future work.
- Use findings to inform hardware choices before purchase.

## Steps

1) Research and lessons

- Gather community feedback on wake word, VAD/AEC, Whisper sizing, mic arrays (Windows quirks), and HA control patterns.

2) Define POC architecture (Windows)

- Select components: wake word (openWakeWord/Porcupine), VAD (WebRTC), ASR (Whisper API or faster-whisper), LLM (ChatGPT API), MCP client/server for HA, TTS (Edge TTS or Piper).
- Specify message/intent flow, latency targets, and fallback behaviors.

3) MCP→HA bridge

- Validate `ha_brain/agents/mcp_ha_server` with long-lived token; run smoke tests (tests/test_all_tools.py) and note auth/whitelist/error handling.
- Scan alternative MCP→HA servers (hass-mcp, advanced-homeassistant-mcp, etc.) and note pros/cons vs current.

4) Windows POC loop

- Implement wake→capture/VAD→Whisper API→ChatGPT API with MCP tools→HA→Edge TTS; add basic logging and self-wake mitigation.
- Test end-to-end and record latency/reliability metrics.

5) Hardware decision prep

- Map POC metrics + research to short list of mic arrays and compute targets within budget; note Windows driver/AEC considerations.

6) Consistency rules

- Create `C:/Users/david/Repos/ha_brain/voice_assistant/.cursor/rules` capturing conventions, token handling, testing steps, and safety for HA service calls.

## Todos

- research-feedback (done) 
- define-arch (done)
- implement-poc (done)
- build-mcp-ha (done)
- e2e-test (done)
- hw-options (done)
- validate-bridge (done)
- research-bridge-alt (done)
- outline-win-loop (done)
- write-ruleset: Add voice assistant rules to `voice_assistant/.cursor/rules`
- asr-followup: Capture ASR integration plan and config hooks for future local STT

## ASR Follow-up (for later integration)

- Current focus: ChatGPT API + Whisper API (no local ASR required yet).
- Add config switches to swap STT backends later (e.g., faster-whisper server URL/model).
- Keep TTS backend selectable (Edge TTS now; Piper/local later) via config.
- Provide placeholder config files so STT/TTS targets can change without code edits.

