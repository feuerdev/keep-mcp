# keep-mcp

[![smithery badge](https://smithery.ai/badge/@feuerdev/keep-mcp)](https://smithery.ai/server/@feuerdev/keep-mcp)

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

* `find`: Search for notes based on a query string
* `create_note`: Create a new note with title and text (automatically adds keep-mcp label)
* `update_note`: Update a note's title and text
* `delete_note`: Mark a note for deletion

By default, all destructive and modification operations are restricted to notes that have were created by the MCP server (i.e. have the keep-mcp label). Set `UNSAFE_MODE` to `true` to bypass this restriction.

```
"env": {
  ...
  "UNSAFE_MODE": "true"
}
```

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
