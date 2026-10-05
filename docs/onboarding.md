# Local onboarding acceptance

Install the released package in an isolated environment (`pipx install keep-mcp` or `uvx keep-mcp`) and configure your chosen client locally. Never send tokens in chat. Prefer a dedicated test account. Run `keep-mcp --check-config` outside the MCP client first; this reports presence and versions, never tests login. Missing/blank values fail before creating a Google client. Default MCP startup emits no diagnostic JSON.

## Checklist round trip

1. Start the installed server with UNSAFE_MODE=false in a real MCP client. Record client/server/Python/MCP/gkeepapi versions without account identifiers.
2. List tools, then create a uniquely named disposable checklist using `create_list` with one unchecked synthetic item. Record the returned note/item IDs immediately in a local ignored manifest.
3. Read it through `get_note`, update the item with `update_list_item` (`checked: true`), then read again. Confirm the same checked item independently in Google Keep and capture reviewed screenshots.
4. Verify a fixture without the keep-mcp label rejects a guarded write. Do not use unrelated account notes. If the client refuses to call the negative case, mark it unexercised and cite automated coverage separately.
5. Trash only the recorded disposable note IDs and independently verify cleanup. Do not delete the shared keep-mcp label.

Follow CONTRIBUTING and the keep-mcp-evidence skill for actual prompts/tool events, screenshots and cleanup. A success message or unit fixture is not real-account proof. Keep captures local/ignored and attach only reviewed screenshots to the draft PR.

## Failure diagnosis

- Configuration error: set missing/blank GOOGLE_EMAIL and GOOGLE_MASTER_TOKEN locally using the referenced gkeepapi flow.
- Login error: verify account/token locally; do not paste provider responses or tokens into an issue.
- Network error: check connectivity. The server drops the failed client; a subsequent deliberate call reauthenticates and reloads state.
- Non-JSON/API/sync error: the unofficial endpoint or account access may have changed. Report the redacted category and versions, not note content.
- Failed mutation: its remote outcome may be unknown. Read the authoritative note before retrying. No automatic retry/replay is performed.

## Compatibility evidence

The project requires Python>=3.10 and mcp>=1.2,<3. Current offline checkout verification uses Python3.11, MCP2.3.0 and gkeepapi0.17.1. CI's Python3.10/3.11/3.12 matrix verifies the dependency versions each install resolves; it is not proof that every permitted minimum/maximum dependency combination or every desktop client works. Fresh wheel/MCP discovery and real-account screenshots must be recorded separately. Do not widen compatibility claims without running those versions.

The current draft was built as a real wheel and installed with declared dependencies into a clean Python3.11 environment. `scripts/verify_install.py` initialized the installed server through an actual stdio MCP client and discovered24tools (MCP2.3.0/gkeepapi0.17.1), invoking no Google operations. The full offline suite passed66tests with98.02% coverage. This is packaging/protocol evidence, not dedicated-account round-trip evidence.
