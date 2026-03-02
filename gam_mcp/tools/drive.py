import hashlib
import json
from typing import Any, Callable, Dict, List, Optional

from ..config import AppConfig
from ..gam import GamResult, run_gam
from ..policy import validate_grantee
from ..store import Proposal, Store


Runner = Callable[[List[str]], GamResult]


def _fingerprint(argv: List[str]) -> str:
    s = json.dumps(argv, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def get_file(file_id: str, runner: Runner = run_gam) -> Dict[str, Any]:
    argv = ['gam', 'info', 'drivefile', file_id]
    r = runner(argv)
    return {'argv': argv, 'exit_code': r.exit_code, 'stdout': r.stdout, 'stderr': r.stderr}


def list_permissions(file_id: str, runner: Runner = run_gam) -> Dict[str, Any]:
    argv = ['gam', 'print', 'drivefileacl', file_id]
    r = runner(argv)
    return {'argv': argv, 'exit_code': r.exit_code, 'stdout': r.stdout, 'stderr': r.stderr}


def propose_transfer_ownership(cfg: AppConfig, store: Store, file_id: str, new_owner_email: str) -> Dict[str, Any]:
    # Treat as user grantee validation
    validate_grantee(cfg, {'type': 'user', 'email': new_owner_email})
    argv = ['gam', 'update', 'drivefile', file_id, 'newowner', new_owner_email]
    fp = _fingerprint(argv)
    p = store.create_proposal('drive.propose_transfer_ownership', {'file_id': file_id, 'new_owner_email': new_owner_email}, argv, fp, ttl_seconds=cfg.approval_ttl_seconds)
    return {'proposal_id': p.proposal_id, 'approval_token': p.proposal_id, 'command_preview': argv}


def propose_add_permission(cfg: AppConfig, store: Store, file_id: str, grantee: Dict[str, Any], role: str) -> Dict[str, Any]:
    validate_grantee(cfg, grantee)
    t = grantee['type'].lower()
    if t in ('domain', 'anyone'):
        raise ValueError('domain/anyone not allowed in v1')
    email = grantee['email']
    argv = ['gam', 'add', 'drivefileacl', file_id, t, email, 'role', role]
    fp = _fingerprint(argv)
    p = store.create_proposal('drive.propose_add_permission', {'file_id': file_id, 'grantee': grantee, 'role': role}, argv, fp, ttl_seconds=cfg.approval_ttl_seconds)
    return {'proposal_id': p.proposal_id, 'approval_token': p.proposal_id, 'command_preview': argv}


def propose_remove_permission(cfg: AppConfig, store: Store, file_id: str, permission_id: str) -> Dict[str, Any]:
    argv = ['gam', 'delete', 'drivefileacl', file_id, 'id', permission_id]
    fp = _fingerprint(argv)
    p = store.create_proposal('drive.propose_remove_permission', {'file_id': file_id, 'permission_id': permission_id}, argv, fp, ttl_seconds=cfg.approval_ttl_seconds)
    return {'proposal_id': p.proposal_id, 'approval_token': p.proposal_id, 'command_preview': argv}
