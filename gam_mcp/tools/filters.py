import hashlib
import json
from typing import Any, Callable, Dict, List

from ..config import AppConfig
from ..gam import GamResult, run_gam
from ..policy import is_allowed_email
from ..store import Store

Runner = Callable[[List[str]], GamResult]

VALID_CRITERIA_KEYS = frozenset(
    {
        "from",
        "to",
        "subject",
        "haswords",
        "nowords",
        "hasattachment",
        "size_larger",
        "size_smaller",
        "excludechats",
    }
)

VALID_ACTION_KEYS = frozenset(
    {
        "archive",
        "label",
        "markread",
        "star",
        "trash",
        "important",
        "notimportant",
        "neverspam",
        "forward",
        "category",
    }
)

# Actions that are bare flags (no value argument)
_BOOL_ACTION_KEYS = frozenset(
    {
        "archive",
        "markread",
        "star",
        "trash",
        "important",
        "notimportant",
        "neverspam",
    }
)


def _fingerprint(argv: List[str]) -> str:
    s = json.dumps(argv, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _build_criteria_argv(criteria: Dict[str, Any]) -> List[str]:
    unknown = set(criteria) - VALID_CRITERIA_KEYS
    if unknown:
        raise ValueError(f"Unknown criteria keys: {sorted(unknown)}")
    parts: List[str] = []
    for k, v in criteria.items():
        parts.append(k)
        # hasattachment / excludechats are bare flags
        if k not in ("hasattachment", "excludechats"):
            parts.append(str(v))
    return parts


def _build_actions_argv(actions: Dict[str, Any]) -> List[str]:
    unknown = set(actions) - VALID_ACTION_KEYS
    if unknown:
        raise ValueError(f"Unknown action keys: {sorted(unknown)}")
    parts: List[str] = []
    for k, v in actions.items():
        parts.append(k)
        if k not in _BOOL_ACTION_KEYS:
            parts.append(str(v))
    return parts


def list_filters(user_email: str, runner: Runner = run_gam) -> Dict[str, Any]:
    argv = ["gam", "user", user_email, "print", "filters", "formatjson"]
    r = runner(argv)
    return {"argv": argv, "exit_code": r.exit_code, "stdout": r.stdout, "stderr": r.stderr}


def get_filter(user_email: str, filter_id: str, runner: Runner = run_gam) -> Dict[str, Any]:
    argv = ["gam", "user", user_email, "info", "filters", filter_id, "formatjson"]
    r = runner(argv)
    return {"argv": argv, "exit_code": r.exit_code, "stdout": r.stdout, "stderr": r.stderr}


def propose_create_filter(
    cfg: AppConfig,
    store: Store,
    user_email: str,
    criteria: Dict[str, Any],
    actions: Dict[str, Any],
) -> Dict[str, Any]:
    if not is_allowed_email(cfg, user_email):
        raise ValueError("user_email domain not allowlisted")
    criteria_argv = _build_criteria_argv(criteria)
    actions_argv = _build_actions_argv(actions)
    argv = ["gam", "user", user_email, "create", "filter"] + criteria_argv + actions_argv
    fp = _fingerprint(argv)
    p = store.create_proposal(
        "filters.propose_create_filter",
        {"user_email": user_email, "criteria": criteria, "actions": actions},
        argv,
        fp,
        ttl_seconds=cfg.approval_ttl_seconds,
    )
    return {"proposal_id": p.proposal_id, "approval_token": p.proposal_id, "command_preview": argv}


def propose_delete_filter(
    cfg: AppConfig,
    store: Store,
    user_email: str,
    filter_id: str,
) -> Dict[str, Any]:
    if not is_allowed_email(cfg, user_email):
        raise ValueError("user_email domain not allowlisted")
    argv = ["gam", "user", user_email, "delete", "filters", filter_id]
    fp = _fingerprint(argv)
    p = store.create_proposal(
        "filters.propose_delete_filter",
        {"user_email": user_email, "filter_id": filter_id},
        argv,
        fp,
        ttl_seconds=cfg.approval_ttl_seconds,
    )
    return {"proposal_id": p.proposal_id, "approval_token": p.proposal_id, "command_preview": argv}
