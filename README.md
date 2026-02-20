# keep-mcp

MCP server for Google Keep

![keep-mcp](https://github.com/user-attachments/assets/f50c4ae6-4d35-4bb6-a494-51c67385f1b6)

## How to use

1. Add the MCP server to your MCP servers:

```json
  "mcpServers": {
    "keep-mcp-pipx": {
      "command": "pipx",
      "args": [
        "run",
        "keep-mcp"
      ],
      "env": {
        "GOOGLE_EMAIL": "Your Google Email",
        "GOOGLE_MASTER_TOKEN": "Your Google Master Token - see README.md"
      }
    }
  }
```

2. Add your credentials:
* `GOOGLE_EMAIL`: Your Google account email address
* `GOOGLE_MASTER_TOKEN`: Your Google account master token

Check https://gkeepapi.readthedocs.io/en/latest/#obtaining-a-master-token and https://github.com/simon-weber/gpsoauth?tab=readme-ov-file#alternative-flow for more information.

## Features

### Query and read tools
* `find`: Search notes with optional filters for labels, colors, pinned, archived, and trashed
* `get_note`: Get a single note by ID

### Creation and update tools
* `create_note`: Create a new note with title and text (automatically adds keep-mcp label)
* `create_list`: Create a checklist note
* `update_note`: Update a note's title and text
* `add_list_item`: Add an item to a checklist note
* `update_list_item`: Update checklist item text and checked state
* `delete_list_item`: Delete a checklist item

### Note state tools
* `pin_note`: Pin or unpin a note
* `archive_note`: Archive or unarchive a note
* `trash_note`: Move a note to trash
* `restore_note`: Restore a trashed/deleted note
* `delete_note`: Mark a note for deletion

### Labels, collaborators, and media tools
* `list_labels`: List labels
* `create_label`: Create a label
* `delete_label`: Delete a label
* `add_label_to_note`: Add a label to a note
* `remove_label_from_note`: Remove a label from a note
* `list_note_collaborators`: List collaborator emails for a note
* `add_note_collaborator`: Add a collaborator email to a note
* `remove_note_collaborator`: Remove a collaborator email from a note
* `list_note_media`: List media blobs for a note (with media links)

By default, all destructive and modification operations are restricted to notes that have were created by the MCP server (i.e. have the keep-mcp label). Set `UNSAFE_MODE` to `true` to bypass this restriction.

```
"env": {
  ...
  "UNSAFE_MODE": "true"
}
```

## Testing

The project includes a lightweight unit test suite under `tests/` that validates:
* note serialization shape for note and list objects (including labels, collaborators, media, and list items)
* modification safety behavior (`keep-mcp` label requirement and `UNSAFE_MODE=true` override)

Run locally:

```bash
pytest -q
```

A GitHub Actions CI workflow now runs this same suite for each pull request across Python 3.10, 3.11, and 3.12.

## Publishing

To publish a new version to PyPI:

1. Update the version in `pyproject.toml`
2. Build the package:
   ```bash
   pipx run build
   ```
3. Upload to PyPI:
   ```bash
   pipx run twine upload --repository pypi dist/*
   ```

## Troubleshooting

* If you get "DeviceManagementRequiredOrSyncDisabled" check https://admin.google.com/ac/devices/settings/general and turn "Turn off mobile management (Unmanaged)"
