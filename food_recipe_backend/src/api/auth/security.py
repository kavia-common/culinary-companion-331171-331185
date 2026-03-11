from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.config import Settings, get_settings
from src.api.db.database import get_db_session
from src.api.db.models import User, UserRole

logger = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=False)


class TokenClaims(BaseModel):
    """JWT claims stored in access tokens."""
    sub: str = Field(..., description="User id (subject).")
    role: UserRole = Field(..., description="User role.")
    exp: int = Field(..., description="Expiration timestamp (unix seconds).")
    iat: int = Field(..., description="Issued-at timestamp (unix seconds).")


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return _pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return _pwd_context.verify(password, password_hash)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# PUBLIC_INTERFACE
def create_access_token(*, settings: Settings, user_id: str, role: UserRole) -> str:
    """Create a signed JWT access token.

    Contract:
      - Inputs: user_id, role, settings.jwt_secret, settings.jwt_algorithm, expiry minutes
      - Outputs: JWT string
      - Errors: jwt library exceptions bubble up (caller maps to 500 at boundary)
    """
    now = _utcnow()
    exp = now + timedelta(minutes=settings.jwt_access_token_expires_minutes)

    payload = {
        "sub": user_id,
        "role": role.value,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_token(settings: Settings, token: str) -> TokenClaims:
    try:
        decoded = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenClaims.model_validate(decoded)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


# PUBLIC_INTERFACE
def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    """FastAPI dependency to get the currently authenticated user.

    Accepts:
      - Authorization: Bearer <token>

    Returns:
      - User ORM object

    Errors:
      - 401 if token missing/invalid
      - 401 if user no longer exists
    """
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    claims = _decode_token(settings, creds.credentials)
    user = db.scalar(select(User).where(User.id == claims.sub))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# PUBLIC_INTERFACE
def require_role(*allowed: UserRole):
    """Create a dependency that enforces the current user has one of the allowed roles."""
    allowed_set = {r.value for r in allowed}

    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in allowed_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _dep
