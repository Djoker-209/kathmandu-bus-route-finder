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


# ---------------------------------------------------------------------------
# AdminUser login (password hashing + JWT) -- separate from require_admin_key
# above. require_admin_key stays as-is for the existing data-entry endpoints;
# this is additive, for the new per-admin login flow.
# ---------------------------------------------------------------------------
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AdminUser

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer_scheme = HTTPBearer()


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


def create_access_token(admin_id: int, username: str, role: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(admin_id), "username": username, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    """FastAPI dependency: decode the bearer token, load and return the
    AdminUser it names. Raises 401 on any invalid/expired/unknown token."""
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.") from exc

    admin = db.get(AdminUser, int(payload["sub"]))
    if admin is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin no longer exists.")
    return admin
