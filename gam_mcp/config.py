import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AppConfig:
    allowed_domains_internal: List[str] = field(default_factory=list)
    allowed_domains_external: List[str] = field(default_factory=list)
    deny_domain_wide_permissions: bool = True
    deny_anyone_permissions: bool = True
    approval_ttl_seconds: int = 600
    approver_telegram_user_ids: List[int] = field(default_factory=list)


def load_config(path: str) -> AppConfig:
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    return AppConfig(
        allowed_domains_internal=raw.get('allowed_domains_internal', []),
        allowed_domains_external=raw.get('allowed_domains_external', []),
        deny_domain_wide_permissions=bool(raw.get('deny_domain_wide_permissions', True)),
        deny_anyone_permissions=bool(raw.get('deny_anyone_permissions', True)),
        approval_ttl_seconds=int(raw.get('approval_ttl_seconds', 600)),
        approver_telegram_user_ids=[int(x) for x in raw.get('approver_telegram_user_ids', [])],
    )
