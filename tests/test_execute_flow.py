import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, ROOT)

from gam_mcp.config import AppConfig
from gam_mcp.store import Store
from gam_mcp.tools.drive import propose_add_permission
from gam_mcp.tools.changes import execute


class TestExecuteFlow(unittest.TestCase):
    def test_execute_requires_approver(self):
        cfg = AppConfig(allowed_domains_internal=['lunchbox.io'], approver_telegram_user_ids=[123])
        with tempfile.TemporaryDirectory() as td:
            s = Store(os.path.join(td, 'db.sqlite'))
            p = propose_add_permission(cfg, s, 'FILE', {'type': 'user', 'email': 'a@lunchbox.io'}, 'reader')
            with self.assertRaises(PermissionError):
                execute(cfg, s, p['approval_token'], approved_by=999)


if __name__ == '__main__':
    unittest.main()
