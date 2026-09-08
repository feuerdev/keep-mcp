# Evidence run template

Store a filled copy locally for each run. Omit account identifiers and secrets.
Unexecuted scenarios remain pending, never prefilled as passed.

- Run ID and UTC time:
- PR and server commit / dirty changes:
- Client name and version:
- Server name selected in client:
- Verified launch command, interpreter, SDK version, transport:
- How the running process/build was verified:
- Browser session and account match confirmed (no email):
- UNSAFE_MODE:

For each scenario:

- Fixture title and returned note ID:
- Exact prompt:
- Actual MCP tool, arguments, result/error:
- Keep starting state:
- Keep observed state after refresh/sync:
- Assertion and outcome (passed / failed / not exercised / blocked):
- Screenshot filenames and capture times:
- Cleanup action and result:

## PR excerpt

Client: <name/version>. Server: <commit and SDK>. Transport: <transport>.

Reproduction: <fixture setup, prompt and any extra sync step>.

- <Observed result supported by actual screenshots>
  <Client prompt and expanded MCP invocation screenshot>
  <Corresponding Google Keep screenshot>

Automated test results go in a fenced code block, copied from execution output.
State any scenario not exercised and why. Link only captures actually produced and
visually inspected. Do not leave invented image links or successful outcome examples.
