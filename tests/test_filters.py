import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)

from gam_mcp.config import AppConfig
from gam_mcp.gam import GamResult
from gam_mcp.store import Store
from gam_mcp.tools.filters import (
    _build_actions_argv,
    _build_criteria_argv,
    get_filter,
    list_filters,
    propose_create_filter,
    propose_delete_filter,
)


def _fake_runner(argv):
    return GamResult(exit_code=0, stdout="ok", stderr="")


class TestBuildArgv(unittest.TestCase):
    def test_criteria_simple(self):
        parts = _build_criteria_argv({"from": "a@b.com", "haswords": "CI failed"})
        self.assertIn("from", parts)
        self.assertIn("a@b.com", parts)
        self.assertIn("haswords", parts)
        self.assertIn("CI failed", parts)

    def test_criteria_bare_flag(self):
        parts = _build_criteria_argv({"hasattachment": True})
        self.assertEqual(parts, ["hasattachment"])

    def test_criteria_unknown_key(self):
        with self.assertRaises(ValueError) as ctx:
            _build_criteria_argv({"bogus": "val"})
        self.assertIn("bogus", str(ctx.exception))

    def test_actions_with_value(self):
        parts = _build_actions_argv({"label": "GitHub/CI", "forward": "x@y.com"})
        self.assertEqual(parts, ["label", "GitHub/CI", "forward", "x@y.com"])

    def test_actions_bool_flag(self):
        parts = _build_actions_argv({"archive": True, "markread": True})
        self.assertIn("archive", parts)
        self.assertIn("markread", parts)
        self.assertEqual(len(parts), 2)

    def test_actions_unknown_key(self):
        with self.assertRaises(ValueError) as ctx:
            _build_actions_argv({"nope": "val"})
        self.assertIn("nope", str(ctx.exception))


class TestReadOnlyTools(unittest.TestCase):
    def test_list_filters(self):
        result = list_filters("alice@example.com", runner=_fake_runner)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(
            result["argv"], ["gam", "user", "alice@example.com", "print", "filters", "formatjson"]
        )

    def test_get_filter(self):
        result = get_filter("alice@example.com", "ANe1Bmj5", runner=_fake_runner)
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("ANe1Bmj5", result["argv"])


class TestProposals(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        db = os.path.join(self._tmpdir.name, "test.sqlite")
        self.store = Store(db)
        self.cfg = AppConfig(allowed_domains_internal=["example.com"])

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_propose_create_filter(self):
        result = propose_create_filter(
            self.cfg,
            self.store,
            "alice@example.com",
            criteria={"from": "bot@example.com"},
            actions={"label": "Bots", "archive": True},
        )
        self.assertIn("proposal_id", result)
        self.assertIn("command_preview", result)
        argv = result["command_preview"]
        self.assertEqual(argv[:6], ["gam", "user", "alice@example.com", "create", "filter", "from"])

    def test_propose_create_filter_blocked_domain(self):
        with self.assertRaises(ValueError) as ctx:
            propose_create_filter(
                self.cfg,
                self.store,
                "alice@evil.com",
                criteria={"from": "x@y.com"},
                actions={"label": "X"},
            )
        self.assertIn("not allowlisted", str(ctx.exception))

    def test_propose_delete_filter(self):
        result = propose_delete_filter(self.cfg, self.store, "alice@example.com", "ANe1Bmj5")
        self.assertIn("proposal_id", result)
        self.assertEqual(
            result["command_preview"],
            ["gam", "user", "alice@example.com", "delete", "filters", "ANe1Bmj5"],
        )

    def test_propose_delete_filter_blocked_domain(self):
        with self.assertRaises(ValueError):
            propose_delete_filter(self.cfg, self.store, "alice@evil.com", "ANe1Bmj5")


if __name__ == "__main__":
    unittest.main()
