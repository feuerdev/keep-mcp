# Contributing

Keep pull requests focused. Include regression tests for bug fixes and run
`make test` and `make lint` before submitting.

## Visual evidence

Every feature or bug-fix PR must include visual evidence that the changed behaviour
works, with screenshots at minimum. Put the screenshots in the PR description with
the steps and inputs used to reproduce the result.

Show real use in both the MCP client and Google Keep: the prompt, actual tool
invocation/result, and the corresponding visible Keep state. Use whichever client
is being tested and record its name/version and the server build. An assistant's
success message alone does not prove that the operation worked.

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
