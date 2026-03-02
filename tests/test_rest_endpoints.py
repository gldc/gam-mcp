"""Tests for REST /approve and /deny endpoints."""

import pytest
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.routing import Route

from mcp.server.fastmcp import FastMCP

from gam_mcp.config import AppConfig
from gam_mcp.store import Store
from gam_mcp.server import register_rest_routes


@pytest.fixture
def cfg():
    return AppConfig(
        approver_telegram_user_ids=[111, 222],
        approval_ttl_seconds=600,
    )


@pytest.fixture
def store(tmp_path):
    return Store(str(tmp_path / "test.sqlite"))


@pytest.fixture
def client(cfg, store):
    """Build a test client from the custom routes registered on a FastMCP server."""
    server = FastMCP("test")
    register_rest_routes(server, cfg, store)
    # Extract the registered custom routes into a plain Starlette app for testing.
    routes = [Route(r.path, r.endpoint, methods=r.methods) for r in server._custom_starlette_routes]
    app = Starlette(routes=routes)
    return TestClient(app)


def _create_proposal(store: Store) -> str:
    prop = store.create_proposal(
        tool_name="drive.propose_transfer_ownership",
        args={"file_id": "abc", "new_owner_email": "x@example.com"},
        command_preview=["gam", "user", "x@example.com", "transfer", "drive", "abc"],
        fingerprint="deadbeef",
        ttl_seconds=600,
    )
    return prop.proposal_id


class TestApproveEndpoint:
    def test_missing_fields(self, client):
        resp = client.post("/approve", json={"proposal_id": "x"})
        assert resp.status_code == 400
        assert resp.json()["ok"] is False

    def test_invalid_json(self, client):
        resp = client.post(
            "/approve", content=b"not json", headers={"content-type": "application/json"}
        )
        assert resp.status_code == 400

    def test_unknown_proposal(self, client):
        resp = client.post(
            "/approve",
            json={"proposal_id": "nope", "approval_token": "nope", "approved_by": "111"},
        )
        assert resp.status_code == 409
        assert "Unknown proposal" in resp.json()["error"]

    def test_unauthorized_approver(self, client, store):
        pid = _create_proposal(store)
        resp = client.post(
            "/approve",
            json={"proposal_id": pid, "approval_token": pid, "approved_by": "999"},
        )
        assert resp.status_code == 403
        assert "approver" in resp.json()["error"].lower()

    def test_non_numeric_approved_by(self, client, store):
        pid = _create_proposal(store)
        resp = client.post(
            "/approve",
            json={"proposal_id": pid, "approval_token": pid, "approved_by": "abc"},
        )
        assert resp.status_code == 400
        assert "numeric" in resp.json()["error"]


class TestDenyEndpoint:
    def test_missing_fields(self, client):
        resp = client.post("/deny", json={"proposal_id": "x"})
        assert resp.status_code == 400
        assert resp.json()["ok"] is False

    def test_unknown_proposal(self, client):
        resp = client.post("/deny", json={"proposal_id": "nope", "denied_by": "111"})
        assert resp.status_code == 404

    def test_deny_success(self, client, store):
        pid = _create_proposal(store)
        resp = client.post("/deny", json={"proposal_id": pid, "denied_by": "111"})
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
        prop = store.get_proposal(pid)
        assert prop.status == "denied"

    def test_deny_already_denied(self, client, store):
        pid = _create_proposal(store)
        store.deny(pid, 111)
        resp = client.post("/deny", json={"proposal_id": pid, "denied_by": "111"})
        assert resp.status_code == 409
        assert "denied" in resp.json()["error"]

    def test_non_numeric_denied_by(self, client, store):
        pid = _create_proposal(store)
        resp = client.post("/deny", json={"proposal_id": pid, "denied_by": "abc"})
        assert resp.status_code == 400
        assert "numeric" in resp.json()["error"]
