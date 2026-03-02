"""MCP server entrypoint."""

import json
import os
import traceback

from starlette.requests import Request
from starlette.responses import JSONResponse

from gam_mcp.config import AppConfig, load_config
from gam_mcp.store import Store
from gam_mcp.tools import drive, groups, filters, changes

from mcp.server.fastmcp import FastMCP


def register_rest_routes(server: FastMCP, cfg: AppConfig, store: Store) -> None:
    """Register REST endpoints for external approval integrations."""

    @server.custom_route("/approve", methods=["POST"])
    async def approve(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return JSONResponse({"ok": False, "error": "invalid JSON"}, status_code=400)

        proposal_id = body.get("proposal_id")
        approval_token = body.get("approval_token")
        approved_by = body.get("approved_by")
        if not proposal_id or not approval_token or approved_by is None:
            return JSONResponse(
                {
                    "ok": False,
                    "error": "missing proposal_id, approval_token, or approved_by",
                },
                status_code=400,
            )

        try:
            approved_by_int = int(approved_by)
        except (TypeError, ValueError):
            return JSONResponse(
                {"ok": False, "error": "approved_by must be numeric"}, status_code=400
            )

        try:
            result = changes.execute(cfg, store, approval_token, approved_by_int)
            return JSONResponse({"ok": True, "result": result})
        except PermissionError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=403)
        except ValueError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=409)
        except Exception as exc:
            traceback.print_exc()
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)

    @server.custom_route("/deny", methods=["POST"])
    async def deny(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return JSONResponse({"ok": False, "error": "invalid JSON"}, status_code=400)

        proposal_id = body.get("proposal_id")
        denied_by = body.get("denied_by")
        if not proposal_id or denied_by is None:
            return JSONResponse(
                {"ok": False, "error": "missing proposal_id or denied_by"},
                status_code=400,
            )

        try:
            denied_by_int = int(denied_by)
        except (TypeError, ValueError):
            return JSONResponse(
                {"ok": False, "error": "denied_by must be numeric"}, status_code=400
            )

        prop = store.get_proposal(proposal_id)
        if not prop:
            return JSONResponse({"ok": False, "error": "Unknown proposal"}, status_code=404)
        if prop.status not in ("proposed", "approved"):
            return JSONResponse(
                {
                    "ok": False,
                    "error": f"Proposal status is '{prop.status}', cannot deny",
                },
                status_code=409,
            )

        store.deny(proposal_id, denied_by_int)
        return JSONResponse({"ok": True})


def main() -> None:
    cfg_path = os.environ.get("MCP_CONFIG", "/config/gam-mcp.json")
    cfg = load_config(cfg_path)
    db_path = os.environ.get("STORE_DB", "/data/proposals.sqlite")
    store = Store(db_path)

    server = FastMCP("gam-mcp", host="0.0.0.0", port=9900)

    @server.tool("drive.get_file")
    def _drive_get_file(file_id: str):
        return drive.get_file(file_id)

    @server.tool("drive.list_permissions")
    def _drive_list_permissions(file_id: str):
        return drive.list_permissions(file_id)

    @server.tool("drive.propose_transfer_ownership")
    def _drive_prop_to(file_id: str, new_owner_email: str):
        return drive.propose_transfer_ownership(cfg, store, file_id, new_owner_email)

    @server.tool("drive.propose_add_permission")
    def _drive_prop_add(file_id: str, grantee: dict, role: str):
        return drive.propose_add_permission(cfg, store, file_id, grantee, role)

    @server.tool("drive.propose_remove_permission")
    def _drive_prop_rm(file_id: str, permission_id: str):
        return drive.propose_remove_permission(cfg, store, file_id, permission_id)

    @server.tool("groups.get")
    def _groups_get(group_email: str):
        return groups.get(group_email)

    @server.tool("groups.list_members")
    def _groups_list(group_email: str):
        return groups.list_members(group_email)

    @server.tool("groups.propose_add_member")
    def _groups_prop_add(group_email: str, user_email: str, role: str = "member"):
        """Propose adding a member to a Google Group.
        role must be 'member' (default), 'manager', or 'owner'."""
        return groups.propose_add_member(cfg, store, group_email, user_email, role)

    @server.tool("groups.propose_remove_member")
    def _groups_prop_rm(group_email: str, user_email: str):
        return groups.propose_remove_member(cfg, store, group_email, user_email)

    @server.tool("filters.list")
    def _filters_list(user_email: str):
        return filters.list_filters(user_email)

    @server.tool("filters.get")
    def _filters_get(user_email: str, filter_id: str):
        return filters.get_filter(user_email, filter_id)

    @server.tool("filters.propose_create")
    def _filters_prop_create(user_email: str, criteria: dict, actions: dict):
        return filters.propose_create_filter(cfg, store, user_email, criteria, actions)

    @server.tool("filters.propose_delete")
    def _filters_prop_delete(user_email: str, filter_id: str):
        return filters.propose_delete_filter(cfg, store, user_email, filter_id)

    @server.tool("changes.execute")
    def _changes_execute(approval_token: str, approved_by: int):
        return changes.execute(cfg, store, approval_token, approved_by)

    # Register REST approval endpoints as custom routes on the MCP server.
    register_rest_routes(server, cfg, store)

    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
