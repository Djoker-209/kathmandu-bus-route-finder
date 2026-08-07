"""Minimal shared-secret auth for admin endpoints.

Not a real user auth system -- there's no login flow for this
project, just a single admin API key checked against a request
header. Good enough for a small internal tool used by the project
team; swap for real auth if this ever needs multiple admins.
"""

import secrets

from fastapi import Header, HTTPException, status

from .config import get_settings


def require_admin_key(x_admin_api_key: str = Header(..., alias="X-Admin-Api-Key")) -> None:
    """FastAPI dependency: raise 401 unless the header matches the
    configured admin key. Use `secrets.compare_digest` instead of `==`
    so the comparison runs in constant time and doesn't leak length
    information via a timing side-channel.
    """
    settings = get_settings()
    if not secrets.compare_digest(x_admin_api_key, settings.admin_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing admin API key.")
