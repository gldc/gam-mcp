"""MCP server entrypoint."""

import os

from gam_mcp.config import load_config
from gam_mcp.store import Store
from gam_mcp.tools import drive, groups, changes

from mcp.server.fastmcp import FastMCP


def main() -> None:
    cfg_path = os.environ.get('MCP_CONFIG', '/config/gam-mcp.json')
    cfg = load_config(cfg_path)
    db_path = os.environ.get('STORE_DB', '/data/proposals.sqlite')
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
    def _groups_prop_add(group_email: str, user_email: str, role: str):
        return groups.propose_add_member(cfg, store, group_email, user_email, role)

    @server.tool("groups.propose_remove_member")
    def _groups_prop_rm(group_email: str, user_email: str):
        return groups.propose_remove_member(cfg, store, group_email, user_email)

    @server.tool("changes.execute")
    def _changes_execute(approval_token: str, approved_by: int):
        return changes.execute(cfg, store, approval_token, approved_by)

    server.run(transport="streamable-http")


if __name__ == '__main__':
    main()
