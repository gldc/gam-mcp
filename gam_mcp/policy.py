import re
from dataclasses import dataclass
from typing import Dict, Optional

from .config import AppConfig


EMAIL_RE = re.compile(r"^[^@\s]+@([^@\s]+)$")


def email_domain(email: str) -> str:
    m = EMAIL_RE.match(email.strip().lower())
    if not m:
        raise ValueError(f"Invalid email: {email!r}")
    return m.group(1)


def is_allowed_email(cfg: AppConfig, email: str) -> bool:
    d = email_domain(email)
    allowed = set([x.lower() for x in cfg.allowed_domains_internal + cfg.allowed_domains_external])
    return d in allowed


def validate_grantee(cfg: AppConfig, grantee: Dict) -> None:
    """grantee: {type: user|group|domain|anyone, email?|domain?}"""
    t = (grantee.get('type') or '').lower()
    if t in ('domain',):
        if cfg.deny_domain_wide_permissions:
            raise ValueError('Domain-wide permissions are disabled by policy')
        domain = (grantee.get('domain') or '').lower()
        allowed = set([x.lower() for x in cfg.allowed_domains_internal + cfg.allowed_domains_external])
        if domain not in allowed:
            raise ValueError(f"Domain {domain} not in allowlist")
        return
    if t in ('anyone',):
        if cfg.deny_anyone_permissions:
            raise ValueError('Anyone permissions are disabled by policy')
        return
    if t in ('user', 'group'):
        email = grantee.get('email')
        if not email:
            raise ValueError('Missing grantee.email')
        if not is_allowed_email(cfg, email):
            raise ValueError(f"Email domain not allowlisted: {email}")
        return
    raise ValueError(f"Unknown grantee.type: {t!r}")
