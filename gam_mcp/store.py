import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS proposals (
  proposal_id TEXT PRIMARY KEY,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  status TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  args_json TEXT NOT NULL,
  command_preview_json TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  approved_by INTEGER,
  approved_at INTEGER,
  executed_at INTEGER,
  exit_code INTEGER,
  stdout TEXT,
  stderr TEXT
);
"""


@dataclass
class Proposal:
    proposal_id: str
    created_at: int
    expires_at: int
    status: str
    tool_name: str
    args: Dict[str, Any]
    command_preview: list[str]
    fingerprint: str
    approved_by: Optional[int] = None
    approved_at: Optional[int] = None
    executed_at: Optional[int] = None
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class Store:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
        self.db_path = db_path
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def create_proposal(self, tool_name: str, args: Dict[str, Any], command_preview: list[str], fingerprint: str, ttl_seconds: int) -> Proposal:
        now = int(time.time())
        pid = str(uuid.uuid4())
        prop = Proposal(
            proposal_id=pid,
            created_at=now,
            expires_at=now + int(ttl_seconds),
            status='proposed',
            tool_name=tool_name,
            args=args,
            command_preview=command_preview,
            fingerprint=fingerprint,
        )
        with self._conn() as c:
            c.execute(
                """INSERT INTO proposals (proposal_id, created_at, expires_at, status, tool_name, args_json, command_preview_json, fingerprint)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prop.proposal_id,
                    prop.created_at,
                    prop.expires_at,
                    prop.status,
                    prop.tool_name,
                    json.dumps(prop.args, sort_keys=True),
                    json.dumps(prop.command_preview),
                    prop.fingerprint,
                ),
            )
        return prop

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM proposals WHERE proposal_id=?", (proposal_id,)).fetchone()
        return self._row_to_proposal(row) if row else None

    def approve(self, proposal_id: str, approved_by: int) -> None:
        now = int(time.time())
        with self._conn() as c:
            c.execute(
                "UPDATE proposals SET status='approved', approved_by=?, approved_at=? WHERE proposal_id=? AND status='proposed'",
                (approved_by, now, proposal_id),
            )

    def deny(self, proposal_id: str, denied_by: int) -> None:
        # store denied_by in approved_by field for simplicity (v1)
        now = int(time.time())
        with self._conn() as c:
            c.execute(
                "UPDATE proposals SET status='denied', approved_by=?, approved_at=? WHERE proposal_id=? AND status IN ('proposed','approved')",
                (denied_by, now, proposal_id),
            )

    def mark_executed(self, proposal_id: str, exit_code: int, stdout: str, stderr: str) -> None:
        now = int(time.time())
        with self._conn() as c:
            c.execute(
                "UPDATE proposals SET status='executed', executed_at=?, exit_code=?, stdout=?, stderr=? WHERE proposal_id=?",
                (now, int(exit_code), stdout, stderr, proposal_id),
            )

    def expire_old(self) -> int:
        now = int(time.time())
        with self._conn() as c:
            cur = c.execute("UPDATE proposals SET status='expired' WHERE status IN ('proposed','approved') AND expires_at <= ?", (now,))
            return cur.rowcount

    def _row_to_proposal(self, row) -> Proposal:
        (
            proposal_id,
            created_at,
            expires_at,
            status,
            tool_name,
            args_json,
            command_preview_json,
            fingerprint,
            approved_by,
            approved_at,
            executed_at,
            exit_code,
            stdout,
            stderr,
        ) = row
        return Proposal(
            proposal_id=proposal_id,
            created_at=created_at,
            expires_at=expires_at,
            status=status,
            tool_name=tool_name,
            args=json.loads(args_json),
            command_preview=json.loads(command_preview_json),
            fingerprint=fingerprint,
            approved_by=approved_by,
            approved_at=approved_at,
            executed_at=executed_at,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
        )
