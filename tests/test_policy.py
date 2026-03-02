import os
import sys
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, ROOT)

from gam_mcp.config import AppConfig
from gam_mcp.policy import email_domain, is_allowed_email, validate_grantee


class TestPolicy(unittest.TestCase):
    def test_email_domain(self):
        self.assertEqual(email_domain('A@Lunchbox.io'), 'lunchbox.io')
        with self.assertRaises(ValueError):
            email_domain('not-an-email')

    def test_allowlist(self):
        cfg = AppConfig(allowed_domains_internal=['lunchbox.io'], allowed_domains_external=[])
        self.assertTrue(is_allowed_email(cfg, 'x@lunchbox.io'))
        self.assertFalse(is_allowed_email(cfg, 'x@gmail.com'))

    def test_grantee_user(self):
        cfg = AppConfig(allowed_domains_internal=['lunchbox.io'])
        validate_grantee(cfg, {'type': 'user', 'email': 'a@lunchbox.io'})
        with self.assertRaises(ValueError):
            validate_grantee(cfg, {'type': 'user', 'email': 'a@gmail.com'})

    def test_grantee_domain_denied(self):
        cfg = AppConfig(allowed_domains_internal=['lunchbox.io'], deny_domain_wide_permissions=True)
        with self.assertRaises(ValueError):
            validate_grantee(cfg, {'type': 'domain', 'domain': 'lunchbox.io'})

    def test_grantee_anyone_denied(self):
        cfg = AppConfig(deny_anyone_permissions=True)
        with self.assertRaises(ValueError):
            validate_grantee(cfg, {'type': 'anyone'})


if __name__ == '__main__':
    unittest.main()
