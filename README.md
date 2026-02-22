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
* `set_note_color`: Set a note color (valid values: DEFAULT, RED, ORANGE, YELLOW, GREEN, TEAL, BLUE, CERULEAN, PURPLE, PINK, BROWN, GRAY)
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

## Local development (uv + make)

If you prefer a JS-style workflow (`npm i`, `npm start`), use the included `Makefile`:

```bash
make install   # like npm i
make start     # like npm start
make test
make lint
```

Run the real-account smoke test with credentials:

```bash
GOOGLE_EMAIL="you@example.com" \
GOOGLE_MASTER_TOKEN="..." \
make smoke
```

Equivalent direct `uv` commands (without `make`):

```bash
UV_CACHE_DIR=/tmp/uv-cache uv venv --python 3.11 .venv
UV_CACHE_DIR=/tmp/uv-cache uv pip install --python .venv/bin/python -e .
UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync --python .venv/bin/python -m server
```

## Testing

### Unit tests (default)
The project includes a lightweight unit test suite under `tests/`.

It validates:
* note serialization shape for note and list objects (including labels, collaborators, media, and list items)
* modification safety behavior (`keep-mcp` label requirement and `UNSAFE_MODE=true` override)
* MCP tool behavior in `src/server/cli.py` using mocked Keep client objects (tool happy paths and key error paths)

Run locally:

```bash
make test
```

### Smoke test against a real Keep account
For additional confidence, run a basic lifecycle smoke test against a dedicated test account:

```bash
GOOGLE_EMAIL="you@example.com" \
GOOGLE_MASTER_TOKEN="..." \
make smoke
```

What it does:
* create note
* update note
* pin/unpin
* archive/unarchive
* trash/restore
* delete

This script is intended for manual verification and is not run in CI.

### CI checks
GitHub Actions runs on every pull request and executes:
* lint (`ruff check .`)
* unit tests with coverage (`pytest -q --cov=src/server --cov-report=term-missing --cov-fail-under=70`)
* bytecode sanity (`python -m compileall src`)

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

## Run locally with MCP clients

This is useful when you want a client to run this server from your local checkout instead of PyPI.

1. Create a local virtualenv and install in editable mode:

```bash
cd /ABSOLUTE/PATH/TO/keep-mcp
make install
```

2. Add the server to your MCP client config.

### `config.toml` clients (Codex, Goose, etc.)

```toml
[mcp_servers.keep_mcp]
command = "make"
args = ["-C", "/ABSOLUTE/PATH/TO/keep-mcp", "start"]

[mcp_servers.keep_mcp.env]
GOOGLE_EMAIL = "you@example.com"
GOOGLE_MASTER_TOKEN = "your-master-token"
UNSAFE_MODE = "false"
```

### JSON `mcpServers` clients (Claude Desktop, Cursor, Cline, etc.)

```json
{
  "mcpServers": {
    "keep-mcp-local": {
      "command": "make",
      "args": ["-C", "/ABSOLUTE/PATH/TO/keep-mcp", "start"],
      "env": {
        "GOOGLE_EMAIL": "you@example.com",
        "GOOGLE_MASTER_TOKEN": "your-master-token",
        "UNSAFE_MODE": "false"
      }
    }
  }
}
```

Alternative (without `make`):

```toml
[mcp_servers.keep_mcp]
command = "uv"
args = [
  "--directory", "/ABSOLUTE/PATH/TO/keep-mcp",
  "run", "--no-sync", "--python", ".venv/bin/python",
  "-m", "server"
]
```

Notes:
* Run `make install` once before starting from an MCP client.
* Only the repo root path is required (no absolute `/.venv/bin/python` path).
* Ensure `make` and `uv` are in your `PATH`.
* Restart your MCP client after updating config files.
* `UNSAFE_MODE` is optional; keep it `"false"` unless you explicitly want to modify non-`keep-mcp` notes.

## Troubleshooting

* If you get "DeviceManagementRequiredOrSyncDisabled" check https://admin.google.com/ac/devices/settings/general and turn "Turn off mobile management (Unmanaged)"
