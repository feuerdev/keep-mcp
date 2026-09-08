# Contributing

Keep pull requests focused. Include regression tests for bug fixes and run
`make test` and `make lint` before submitting.

## Visual evidence

Every feature or bug-fix PR must include visual evidence that the changed behaviour
works, with screenshots at minimum. Put the screenshots in the PR description with
the steps and inputs used to reproduce the result.

Show the real MCP client prompt and actual tool invocation/result, paired with
screenshots of the corresponding Google Keep state. Prefer a CLI client when
available and quote its transcript in code blocks. Client UI screenshots are
optional. Record the client name/version and server build. An assistant's success
message alone does not prove that the operation worked.

Put test results and logs in code blocks. Screenshots of tests, terminals, source
code, or reconstructed interfaces do not satisfy the real-use requirement. If a
client cannot exercise a negative case, say so and provide its automated regression
coverage separately. Keep the PR draft while required real-use evidence is missing.

Use the client-neutral [keep-mcp-evidence skill](.agents/skills/keep-mcp-evidence/SKILL.md)
for scenario recipes, capture requirements and cleanup. Keep raw captures local in
`testing-evidence/`, then attach only reviewed screenshots to the PR.

Capture the failing case before the fix when practical, and the working case after
it. Videos can supplement screenshots. Remove credentials, tokens, and private note
content before uploading evidence.

Use a dedicated test account for Google Keep smoke tests. The smoke script creates,
updates, and deletes notes, lists, and labels.
