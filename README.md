# gam-mcp

MCP server for Google Workspace administration via [GAM](https://github.com/GAM-team/GAM). Exposes Drive permission and Group membership management as MCP tools with a propose-approve-execute workflow.

## Features

- **Drive tools** — get file info, list permissions, propose ownership transfers / permission adds / permission removals
- **Groups tools** — get group info, list members, propose member adds / removals
- **Approval gate** — all mutations create a proposal that must be approved (by Telegram user ID) before execution
- **Policy engine** — domain allowlists, deny domain-wide / anyone permissions
- **SQLite store** — proposals with TTL expiry, status tracking, audit trail

## Quick start

```bash
# 1. Clone
git clone https://github.com/gldc/gam-mcp.git
cd gam-mcp

# 2. Create config
cp config.example.json config/gam-mcp.json
# Edit config/gam-mcp.json with your domains + approver Telegram IDs

# 3. Run with Docker
docker compose -f docker-compose.example.yml up --build
```

The server listens on port `9900` using streamable-http transport.

## Configuration

See `config.example.json` for all options:

| Key | Description |
|-----|-------------|
| `allowed_domains_internal` | Domains treated as internal (always allowed) |
| `allowed_domains_external` | External partner domains (allowed) |
| `deny_domain_wide_permissions` | Block domain-wide Drive sharing |
| `deny_anyone_permissions` | Block "anyone" Drive sharing |
| `approval_ttl_seconds` | How long a proposal stays valid |
| `approver_telegram_user_ids` | List of Telegram user IDs allowed to approve |

## Running locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export MCP_CONFIG=config/gam-mcp.json
export STORE_DB=data/proposals.sqlite
python -m gam_mcp.server
```

GAM must be installed and configured (`~/.gam/`) for mutation tools to work.

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/
```

## License

MIT
