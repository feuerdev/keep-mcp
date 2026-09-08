# CLI evidence runs

Use an installed, authenticated MCP client. Codex exec and Cursor CLI are examples,
not required dependencies. Check the installed version's help before choosing flags.
The current agent can also be the client if its tools connect to the verified build.
Do not start a recursive agent workflow just to invoke an already available tool.

Keep the run bounded:

- Save the prompt before execution. Specify exact fixture IDs/titles, allowed tools,
  expected failure and a stopping condition. Prohibit repairing negative inputs,
  unrelated reads/writes, file edits and delegation.
- Prefer per-run configuration over modifying the user's global client setup.
  Enable only the server under test and the tools needed for the scenario. Supply
  existing authorised credentials through the environment, never prompt text or
  command-line arguments. Preserve safe mode.
- Resolve required tool approvals for the authorised run. An approval error means
  the server operation was not exercised. Do not disable approvals globally.
- Capture structured events when supported, including actual server/tool names,
  arguments, result/error and completion. Save stderr privately. A final assistant
  answer or a zero exit code alone does not establish success.
- Retain a server process across any sequence testing cached state. Resuming a CLI
  conversation may start a new server. Put the rejected update and follow-up sync
  in one invocation, or otherwise verify process continuity.
- Bound each run and inspect events before retrying after a timeout. A timed-out
  creation may already have made a note. Record every returned fixture ID before
  the next mutation and clean up only those IDs.

For Codex versions supporting these options, `codex exec --json --ephemeral`
accepts a prompt on stdin and produces JSONL events. `--ignore-user-config` and
per-run `-c` overrides can isolate the server selection without replacing saved
credentials. Check the effective configuration and tool events; do not assume
these flags remove every inherited integration. Record the launch command and
client version with the evidence.

Quote the saved prompt and decisive actual MCP events in the PR as code blocks.
Take Google Keep screenshots at the planned visible checkpoints. Do not drive or
screenshot a desktop client merely to restate the same transcript.
