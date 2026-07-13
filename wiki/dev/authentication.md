---
title: "API Authentication"
tags: [api, authentication, security, auth]
created: 2026-06-26
updated: 2026-06-26
sources: [api-auth]
related: [api-design, mcp-server, production-readiness, pydantic-settings]
---

# API Authentication

API key authentication for mutating endpoints. Implementation in `src/api/auth.py` (18 lines).

## Overview

The API uses a simple API key header for authentication. In development mode (when `API_KEY` is not set), authentication is skipped entirely. This allows the system to run fully open for local development while supporting key-based auth in production.

## Authentication Mechanism

API key is passed via the `X-API-Key` header:

```bash
curl -H "X-API-Key: my-secret-key" http://localhost:8000/query -d '{"query": "tell me about Roswell"}'
```

### `verify_api_key(x_api_key: str = Header(default=None))`

FastAPI dependency that performs authentication:

1. **Dev mode check** — If `settings.API_KEY` is empty/unset, returns immediately (no auth required)
2. **Key validation** — Compares `x_api_key` header against `settings.API_KEY`
3. **Failure response** — Returns 401 with `"Invalid or missing API key"` detail
4. **Logging** — Logs unauthorized attempts with the first 4 characters of the key (partial masking)

```python
# src/api/auth.py
async def verify_api_key(x_api_key: str = Header(default=None)):
    if not settings.API_KEY:
        return  # Dev mode: no auth required
    if x_api_key != settings.API_KEY:
        logger.warning(f"Unauthorized API request with key: {x_api_key[:4]}...")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `API_KEY` | `""` (empty) | API key for authentication. When empty, auth is disabled (dev mode) |

Set via `.env`:
```bash
API_KEY=your-super-secret-api-key-here
```

## Usage

Apply the dependency to any endpoint:

```python
from fastapi import APIRouter
from src.api.auth import verify_api_key

router = APIRouter()

@router.post("/query")
async def submit_query(
    request: QueryRequest,
    _auth: None = Depends(verify_api_key)  # Auth applied to this endpoint
):
    ...
```

## Security Notes

- **Key strength** — The API key is compared as a plain string. Use a strong, randomly generated key in production.
- **Transport security** — In production, always use HTTPS to prevent key interception.
- **No rate limiting** — Authentication does not include rate limiting. See `production-readiness` for rate limiting considerations.
- **MCP server** — The MCP server uses the same API key auth mechanism (documented in `mcp-server`).

## See Also

- [[api-design]] — All API endpoints and models
- [[mcp-server]] — MCP server authentication
- [[production-readiness]] — Security checklist
- [[pydantic-settings]] — Configuration management
