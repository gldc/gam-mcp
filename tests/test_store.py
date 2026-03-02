import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, ROOT)

from gam_mcp.store import Store


class TestStore(unittest.TestCase):
    def test_create_get_expire(self):
        with tempfile.TemporaryDirectory() as td:
            db = os.path.join(td, 'db.sqlite')
            s = Store(db)
            p = s.create_proposal('tool', {'a': 1}, ['gam', 'info'], 'fp', ttl_seconds=1)
            got = s.get_proposal(p.proposal_id)
            self.assertIsNotNone(got)
            self.assertEqual(got.status, 'proposed')
            time.sleep(1.2)
            s.expire_old()
            got2 = s.get_proposal(p.proposal_id)
            self.assertEqual(got2.status, 'expired')


if __name__ == '__main__':
    unittest.main()
