# Checklist scenarios

Replace `<title>` with the unique run/scenario name and `<id>` with the actual
returned ID. Prompts are recipes, not evidence; record the actual invocation.
Use the specifically verified server, especially when a published server is also
configured in the client.

## Mixed checked states

Prompt: "Using the local keep-mcp server under test, create a checklist titled
<title> with 'Buy milk' unchecked and 'Pack bag' checked. Stop after creation."

Expect `create_list` with JSON boolean false/true. Inspect the result, then open
that checklist in Keep. Capture both states, expanding checked items if collapsed.
This proves the valid workflow; it does not prove rejection of a string boolean.

## Invalid checked state

Prompt: "Exercise validation on the keep-mcp server under test. Call create_list
with title <title> and items [{\"text\":\"Buy milk\",\"checked\":\"false\"}].
Preserve the string value exactly. Make one call only and stop after the error.
Do not repair the input or retry with a boolean."

Expect an actual invocation with the string and a tool error mentioning a boolean.
Capture the client exchange and a scoped Keep search for the unique title. If the
client's schema or model prevents this call, record **not exercised by this client**;
retain the automated regression test as separate coverage. An empty search alone
cannot prove that a rejected request reached the server.

## Rejected text replacement without partial mutation

Create a fresh checklist titled `<title>` with 'Buy milk' unchecked. Record its ID
and capture its starting state in Keep.

Prompt: "Using the keep-mcp server under test, call update_note for <id> with title
<title>-unexpected and text 'Replacement'. Make that call exactly once, then stop.
Do not use list-item tools as a fallback."

Expect an error directing the caller to checklist item tools. Verify the title is
still `<title>` and the item is still 'Buy milk', unchecked. Then ask the client to
pin this fixture with `pin_note`, which syncs cached changes, and reload Keep. The
original title and item must still be intact. Run rejection and pinning in the same
server process, including when using a CLI client. Capture the error exchange and final
Keep state, and record the extra sync step so the outcome is reproducible.

## Supported title update

On a fresh checklist, ask: "Rename checklist <id> to <title>-renamed using
update_note with only its title argument. Leave all checklist items unchanged."

Capture the actual tool call/result and Keep showing the new title and unchanged
items. Do not count the client's use of another tool as this scenario passing.

## Cleanup

Ask the client to trash only the recorded run fixture IDs. Do not empty Trash or
remove the shared keep-mcp label. Record any fixtures not cleaned up.
