import hashlib
import json
from typing import Any, Callable, Dict, List

from ..config import AppConfig
from ..gam import GamResult, run_gam
from ..policy import is_allowed_email
from ..store import Store

Runner = Callable[[List[str]], GamResult]


def _fingerprint(argv: List[str]) -> str:
    s = json.dumps(argv, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def get(group_email: str, runner: Runner = run_gam) -> Dict[str, Any]:
    argv = ['gam', 'info', 'group', group_email]
    r = runner(argv)
    return {'argv': argv, 'exit_code': r.exit_code, 'stdout': r.stdout, 'stderr': r.stderr}


def list_members(group_email: str, runner: Runner = run_gam) -> Dict[str, Any]:
    argv = ['gam', 'print', 'group-members', 'group', group_email]
    r = runner(argv)
    return {'argv': argv, 'exit_code': r.exit_code, 'stdout': r.stdout, 'stderr': r.stderr}


def propose_add_member(cfg: AppConfig, store: Store, group_email: str, user_email: str, role: str) -> Dict[str, Any]:
    if not is_allowed_email(cfg, user_email):
        raise ValueError('user_email domain not allowlisted')
    argv = ['gam', 'update', 'group', group_email, 'add', 'member', user_email, 'role', role]
    fp = _fingerprint(argv)
    p = store.create_proposal('groups.propose_add_member', {'group_email': group_email, 'user_email': user_email, 'role': role}, argv, fp, ttl_seconds=cfg.approval_ttl_seconds)
    return {'proposal_id': p.proposal_id, 'approval_token': p.proposal_id, 'command_preview': argv}


def propose_remove_member(cfg: AppConfig, store: Store, group_email: str, user_email: str) -> Dict[str, Any]:
    if not is_allowed_email(cfg, user_email):
        raise ValueError('user_email domain not allowlisted')
    argv = ['gam', 'update', 'group', group_email, 'remove', 'member', user_email]
    fp = _fingerprint(argv)
    p = store.create_proposal('groups.propose_remove_member', {'group_email': group_email, 'user_email': user_email}, argv, fp, ttl_seconds=cfg.approval_ttl_seconds)
    return {'proposal_id': p.proposal_id, 'approval_token': p.proposal_id, 'command_preview': argv}
