from typing import Any, Dict, List

from ..config import AppConfig
from ..gam import run_gam
from ..store import Store


def execute(cfg: AppConfig, store: Store, approval_token: str, approved_by: int) -> Dict[str, Any]:
    # In v1, approval_token == proposal_id. (We can upgrade to HMAC tokens later.)
    pid = approval_token
    prop = store.get_proposal(pid)
    if not prop:
        raise ValueError('Unknown proposal')

    store.expire_old()
    prop = store.get_proposal(pid)

    if prop.status == 'expired':
        raise ValueError('Proposal expired')
    if prop.status == 'denied':
        raise ValueError('Proposal denied')
    if prop.status == 'executed':
        raise ValueError('Proposal already executed')

    if approved_by not in cfg.approver_telegram_user_ids:
        raise PermissionError('Not an allowed approver')

    # Mark approved if still proposed
    if prop.status == 'proposed':
        store.approve(pid, approved_by=approved_by)
        prop = store.get_proposal(pid)

    if prop.status != 'approved':
        raise ValueError('Proposal not approved')

    r = run_gam(prop.command_preview)
    store.mark_executed(pid, exit_code=r.exit_code, stdout=r.stdout, stderr=r.stderr)

    return {'proposal_id': pid, 'exit_code': r.exit_code, 'stdout': r.stdout, 'stderr': r.stderr}
