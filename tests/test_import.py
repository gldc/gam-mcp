import os
import sys
import unittest

# Allow running tests without installing the package
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, ROOT)


class TestImport(unittest.TestCase):
    def test_import(self):
        import gam_mcp  # noqa: F401


if __name__ == '__main__':
    unittest.main()
