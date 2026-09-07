# Contributing

Keep pull requests focused. Include regression tests for bug fixes and run
`make test` and `make lint` before submitting.

## Visual evidence

Every feature or bug-fix PR must include visual evidence that the changed behaviour
works, with screenshots at minimum. Put the screenshots in the PR description with
the steps and inputs used to reproduce the result.

Show the actual result in Google Keep or the MCP client when the change affects
those interfaces. For protocol, validation, or backend-only changes, screenshots
of the actual request/response or regression-test execution are acceptable. State
which dependencies were mocked and whether a real account was used. A screenshot
of code or an unsupported "tests passed" claim is not evidence.

Capture the failing case before the fix when practical, and the working case after
it. Videos can supplement screenshots. Remove credentials, tokens, and private note
content before uploading evidence.

Use a dedicated test account for Google Keep smoke tests. The smoke script creates,
updates, and deletes notes, lists, and labels.
