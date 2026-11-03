# Auth Proxy Deployment Example (Caddy + Streamable HTTP Reverse Proxy)

This directory contains configuration files and deployment templates for running a two-tier **Caddy Auth Proxy + keep-mcp** architecture on **Fly.io** using an isolated pair of VMs communicating over a private 6PN WireGuard mesh.

---

## Architecture Overview

```
MCP Clients (Gemini, Cursor, Claude, etc.)
                   │
                   ▼ HTTPS (Public Ingress)
    ┌──────────────────────────────────┐
    │       Caddy Auth Proxy           │
    │  - Port 8080 (Public)            │
    │  - Validates API Key             │
    │  - Zero-buffering for SSE/HTTP   │
    │  - Health probe on /healthz      │
    └──────────────────┬───────────────┘
                       │ Private Network / 6PN Mesh
                       ▼
    ┌──────────────────────────────────┐
    │       keep-mcp Backend           │
    │  - Port 8080 (Private VM)        │
    │  - No public IP / inaccessible   │
    │  - Google Keep sync session      │
    └──────────────────────────────────┘
```

---

## Features

- **Unbuffered Streaming Delivery:** Configured with `flush_interval -1` to guarantee immediate, streaming response chunks for MCP Server-Sent Events (`sse`) and Streamable HTTP (`streamable-http`).
- **Flexible Key Ingestion:** Accepts authentication tokens through:
  - `Authorization: Bearer <MCP_API_KEY>`
  - `X-API-Key: <MCP_API_KEY>`
  - `?token=<MCP_API_KEY>` (URL parameter for clients with single URL inputs)
- **Health Checks:** Serves unauthenticated `200 OK` on `/healthz` for platform liveness and readiness probes.
- **Minimal Footprint:** Alpine Caddy base image (~15 MB).

---

## Configuration Variables

| Variable | Target App | Description | Default |
|---|---|---|---|
| `MCP_API_KEY` | Proxy | Secret token required to authenticate MCP requests | *(Required)* |
| `BACKEND_URL` | Proxy | Address of internal `keep-mcp` service | `http://keep-mcp-backend.internal:8080` |
| `GOOGLE_EMAIL` | Backend | Google account email address | *(Required)* |
| `GOOGLE_MASTER_TOKEN` | Backend | Google Master Token (`aas_et/...`) | *(Required)* |
| `MCP_TRANSPORT` | Backend | Transport type (`streamable-http` or `sse`) | `streamable-http` |
| `PORT` | Both | Port to listen on (assigned dynamically) | `8080` |

---

## Deploying on Fly.io (Pair of Private + Public Machines)

Fly.io allows running two separate Machine apps that communicate over Fly's private encrypted WireGuard mesh (`.internal` DNS). The backend VM has **no public IP address**, meaning only your Caddy proxy VM can reach it.

### Step 1: Deploy the Backend VM (`keep-mcp-backend`)

From the repo root:

1. **Launch the backend app without deploying immediately:**
   ```bash
   fly launch --config docs/deployments/auth-proxy/fly.backend.toml --no-deploy
   ```
   *(Optionally rename the app in `fly.backend.toml` if the name is already taken).*

2. **Set the Keep credentials as encrypted Fly secrets:**
   ```bash
   fly secrets set \
     GOOGLE_EMAIL="your-email@gmail.com" \
     GOOGLE_MASTER_TOKEN="aas_et/..." \
     --config docs/deployments/auth-proxy/fly.backend.toml
   ```

3. **Deploy the backend machine:**
   ```bash
   fly deploy --config docs/deployments/auth-proxy/fly.backend.toml
   ```

4. **Ensure the backend has no public IPs:**
   ```bash
   fly ips list --config docs/deployments/auth-proxy/fly.backend.toml
   ```
   *(If any public IPv4/IPv6 was allocated, run `fly ips release <ip>` to remove it).*

---

### Step 2: Deploy the Public Proxy VM (`keep-mcp-proxy`)

1. **Launch the proxy app:**
   ```bash
   fly launch --config docs/deployments/auth-proxy/fly.proxy.toml --no-deploy
   ```

2. **Set the proxy API key secret:**
   ```bash
   fly secrets set \
     MCP_API_KEY="your-secret-api-key" \
     --config docs/deployments/auth-proxy/fly.proxy.toml
   ```

3. **Update `BACKEND_URL` in `fly.proxy.toml` if you changed the backend app name:**
   ```toml
   [env]
     BACKEND_URL = "http://<your-backend-app-name>.internal:8080"
   ```

4. **Deploy the proxy:**
   ```bash
   fly deploy docs/deployments/auth-proxy --config docs/deployments/auth-proxy/fly.proxy.toml
   ```

5. **Allocate public IPs for the gateway:**
   ```bash
   fly ips allocate-v6 --config docs/deployments/auth-proxy/fly.proxy.toml
   fly ips allocate-v4 --shared --config docs/deployments/auth-proxy/fly.proxy.toml
   ```

Your MCP endpoint is now reachable securely at:
```text
https://<your-proxy-app-name>.fly.dev/mcp?token=<your-secret-api-key>
```
Or via HTTP headers:
- `Authorization: Bearer <your-secret-api-key>`
- `X-API-Key: <your-secret-api-key>`
