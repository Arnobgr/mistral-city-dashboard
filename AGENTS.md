# AGENTS.md

## API References — read before implementing any integration
- Mistral function calling format: see `docs/mistral` md files
- datagouv MCP tool signatures: see `docs/datagouvmcp.md`, github repo available at https://github.com/datagouv/datagouv-mcp
- ElevenLabs TTS endpoint: see `docs/elevenlabs` md files

## Rules
- Never guess parameter names for these APIs. Always read the relevant doc file first.
- MCP calls use JSON-RPC 2.0 POST to /mcp with method `tools/call`.
- The ElevenLabs model for French is `eleven_multilingual_v2`, not `eleven_monolingual_v1`.