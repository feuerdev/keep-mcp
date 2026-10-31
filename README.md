# keep-mcp

MCP server for Google Keep

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and required visual evidence.

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

Or with `uvx`:

```json
  "mcpServers": {
    "keep-mcp": {
      "command": "uvx",
      "args": [
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

### Obtain a Google master token

`keep-mcp` uses [gkeepapi](https://gkeepapi.readthedocs.io/), which connects to Google Keep through an unofficial private API. A Google master token has full access to your account. Treat it like a password and never commit or share it.

You need [Docker](https://docs.docker.com/get-started/get-docker/) and a desktop browser.

1. Open https://accounts.google.com/EmbeddedSetup and sign in with the Google account you use for Keep.
2. Click **I agree**. The page may keep loading forever. Leave it open and continue.
3. Copy the `oauth_token` cookie:
   * **Chrome or Edge:** Press F12, open the **Application** tab, then **Cookies** → `https://accounts.google.com`.
   * **Firefox:** Press F12, open the **Storage** tab, then **Cookies** → `https://accounts.google.com`.

   Find the row named `oauth_token` and copy its value. It starts with `oauth2_4/`.
4. Right away, run this in a terminal and paste your email and the cookie value when asked:

   ```bash
   docker run --rm -it ghcr.io/astral-sh/uv:python3.13-bookworm-slim uv run --no-project --with gpsoauth python -c "import gpsoauth; r = gpsoauth.exchange_token(input('Email: '), input('oauth_token: '), '0123456789abcdef'); print(r.get('Token', r))"
   ```

   Without Docker, install [uv](https://docs.astral.sh/uv/getting-started/installation/) and run the same command without the `docker run --rm -it ghcr.io/astral-sh/uv:python3.13-bookworm-slim` part.

5. The command prints your master token. It starts with `aas_et/`. Use it as `GOOGLE_MASTER_TOKEN`.

If it prints an error such as `BadAuthentication` instead, the cookie has expired. Repeat steps 1 to 4 to get a fresh one.

#### More details

* [`gpsoauth`'s alternative flow](https://github.com/simon-weber/gpsoauth#alternative-flow) describes the token exchange.
* [gkeepapi's "Obtaining a Master Token" instructions](https://gkeepapi.readthedocs.io/en/latest/#obtaining-a-master-token) describe the same exchange.

Older instructions may ask for your Google password or an app password and call `perform_master_login()`. That flow is unreliable and can return `BadAuthentication`. Use the browser-assisted flow above instead.

## Features

### Query and read tools
* `find`: Search notes (case-insensitive by default) with optional filters for labels, colors, pinned, archived, trashed, creation/update date ranges (ISO 8601, UTC), and a result limit
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
* `download_media`: Download a note's media (images, drawings, audio) to a local directory through the authenticated session (the raw media links answer 403 to plain HTTP clients)

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

### Automatic publish on merge to `main` (GitHub Actions)

This repo includes a release workflow at `.github/workflows/release.yml` that runs on every push to `main` (including merged PRs).

It will:
* inspect commits since the last release tag (`vX.Y.Z`)
* compute the next semantic version from Conventional Commit types
* skip publishing when there are no releasable commit types
* run lint and unit tests
* build `dist/*`
* publish to PyPI
* create a GitHub release/tag `v<computed-version>` with generated notes

Version bump rules:
* major: commit subject with `!` (example: `feat!:` or `fix(api)!:`) or commit body containing `BREAKING CHANGE`
* minor: `feat:`
* patch: `fix:`, `perf:`, `revert:`
* no release: `docs:`, `chore:`, `ci:`, `test:`, `refactor:` (unless the commit is marked as breaking)

Required repository secret:
* `PYPI_API_TOKEN`: a PyPI API token (recommended scope: this project only)

### Manual publish

To publish manually to PyPI:

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

## Running over Streamable HTTP

`keep-mcp` supports the MCP Streamable HTTP transport (`/mcp` endpoint) in addition to the default `stdio` transport:

```bash
# Start Streamable HTTP server on localhost (default: 127.0.0.1:8000)
keep-mcp --transport streamable-http

# Customize host or port
keep-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

> [!NOTE]
> `keep-mcp` binds to `127.0.0.1` by default with DNS rebinding protection enabled. To expose the server to remote or web clients (such as Gemini web), place an authenticating proxy (such as [mcp-auth-proxy](https://github.com/sigbit/mcp-auth-proxy)) in front of the server.

## Troubleshooting

* If you get "DeviceManagementRequiredOrSyncDisabled" check https://admin.google.com/ac/devices/settings/general and turn "Turn off mobile management (Unmanaged)"
