---
name: keep-mcp-evidence
description: Capture reproducible real-use evidence for keep-mcp features and fixes through an MCP client and the Google Keep interface. Use when preparing PR screenshots or verifying a Keep workflow end to end.
---

# keep-mcp evidence

Prove the action through the actual MCP client and verify its effect independently
in Google Keep. Test output belongs in code blocks, never screenshot substitutes.
Prefer a CLI-based MCP client when available. Use the current agent's connected
MCP tools if they target the verified build, otherwise use a bounded CLI invocation
such as Codex exec or Cursor CLI. Honour the user's client choice and record its
name/version. A desktop client is a fallback, not a requirement.

Save the exact prompt and actual MCP call/result events as text. CLI transcripts
belong in code blocks; client screenshots are optional. Google Keep screenshots
still provide the independent visual evidence. Read [cli-runs.md](references/cli-runs.md)
when using a CLI client.

## Preflight

- Read the diff and choose concrete visible outcomes. Read
  [scenarios.md](references/scenarios.md) for the checklist scenarios from PR #19.
- Verify the client's keep-mcp launch command resolves to the checkout/build under
  test. Record commit, dirty status, interpreter, SDK version and transport without
  logging environment values. Restart/reconnect the server after changes. A checked
  out commit alone does not establish which server an already-running client uses.
- If multiple Keep servers are configured, target the exact server under test and
  inspect every invocation. Do not silently fall back to another server.
- Open Google Keep in an isolated authenticated browser session when available.
  Confirm it is the same account as the configured server, without publishing the
  account identifier. Prefer a dedicated test account. If login is needed, leave
  the page open and ask the user to sign in. Continue independent preparation while
  waiting. Never request tokens/passwords in chat or copy browser credentials.
- Use `UNSAFE_MODE=false`. Operate only on fixtures created for this run, with names
  `keep-mcp-evidence-<UTC timestamp>-<random suffix>-<scenario>`. Record returned note
  IDs immediately. Keep a local manifest of IDs and cleanup status. Never delete
  unrelated notes or the shared `keep-mcp` label.

## Run and capture

1. Write down the exact prompt, expected MCP operation/arguments, expected visible
   state and timeout. Use a fresh fixture per scenario. Fixture setup also goes
   through the client when feasible; identify any separate setup method explicitly.
2. Plan only the Keep checkpoints needed to prove the visible outcome. Use the
   client transcript for intermediate checks. Batch independent final fixture
   checks into one scoped Keep view when readable. Capture a before state when
   needed to demonstrate a change; do not take a screenshot after every tool call.
3. Submit the saved prompt through the real MCP client. With a CLI, retain its
   structured tool-call events and results. With a desktop client, expand the tool
   details and capture them. An assistant's success message alone is insufficient.
4. Match actual arguments and returned note ID against the scenario. If the model
   corrects invalid input, substitutes another tool, or refuses to call, mark that
   negative case **not exercised**. One clarified retry is reasonable; don't keep
   creating notes or replace the invocation with a Python call to manufacture proof.
5. In Keep, find/open the exact fixture and wait for synchronization, refreshing
   when necessary. Assert the visible title, item text and checked state. Bound the
   wait, for example to 60 seconds. A timeout is inconclusive, not proof of absence.
   For failed updates, also make a benign supported update and reload: this helps
   expose unintended cached mutations that could be synced on a later request.
   Keep the rejected update and follow-up sync in the same server process; a fresh
   CLI invocation can discard the very cached mutation this scenario tests.
6. Capture the resulting Keep state. Capture before-build evidence on separate
   fixtures when practical; don't confuse a starting state with reproduction on an
   old build. Never stage expected UI using browser edits or mock pages.
7. Inspect every image for legibility and private content. Frame the fixture and
   client exchange tightly, excluding unrelated notes, conversations, account menus
   and credentials. Cropping/redaction may hide private content, but must not alter
   the behavior shown. Never publish browser storage, tokens or raw private logs.
8. Clean up only recorded fixture IDs, preferably by moving them to recoverable
   trash through the client. Verify cleanup and record any leftover IDs. If a call
   times out, search for the unique title before retrying creation or cleanup.

Use browser/computer tools for Keep checkpoints and screenshot capture, not to
drive a client that has a usable CLI. Stop inspecting once a checkpoint is clear.
Use screenshots from supported browser/native capture tools. Load the relevant
browser skill when available. No generated screenshots, reconstructed conversations,
or screenshots of pytest/terminal output in place of real use.

## Delivery and reproducibility

Use [evidence-template.md](references/evidence-template.md). Keep captures and raw
observations in an ignored local `testing-evidence/<PR>/<run-id>/` directory. The
manifest records client/build, fixture IDs, prompts, actual calls, timestamps,
assertions, screenshot filenames, coverage gaps and cleanup. Never include secrets.
Publish only reviewed screenshots and selected non-sensitive facts to the requested
PR when authorized. Attach screenshots directly to the PR and quote decisive CLI
output in collapsible code blocks in its description or a comment. Keep run-specific
screenshots, transcripts and reports out of version control unless the user explicitly
requests otherwise. Do not create a repository evidence folder as an upload workaround.
If attachments are blocked, preserve the files locally and report the blocker.
Offer the files for manual attachment instead of escalating into desktop automation.
Reusable recipes belong in the skill; individual run results belong in the PR.

If login, client access or build provenance is unavailable, report the exact blocker,
leave the PR draft, and preserve the recipe for resumption. Do not mark the screenshot
requirement satisfied or substitute automated tests. A skill passing static validation
is not evidence that the live workflow has passed.
