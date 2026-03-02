import os
import sys
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, ROOT)

from gam_mcp.gam import run_gam


class TestGamRunner(unittest.TestCase):
    def test_reject_empty(self):
        with self.assertRaises(ValueError):
            run_gam([])

    def test_no_shell(self):
        # Just ensure it can run a harmless command.
        r = run_gam(['python3', '-c', 'print("ok")'])
        self.assertEqual(r.exit_code, 0)
        self.assertIn('ok', r.stdout)


if __name__ == '__main__':
    unittest.main()
