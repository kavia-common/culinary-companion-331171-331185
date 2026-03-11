from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.auth.security import create_access_token, get_current_user, hash_password, verify_password
from src.api.core.config import Settings, get_settings
from src.api.db.database import get_db_session
from src.api.db.models import User, UserRole
from src.api.schemas import AuthResponse, AuthTokens, LoginRequest, RegisterRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _user_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        email=u.email,
        displayName=u.display_name,
        role=u.role.value,
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    summary="Register",
    description="Register a new user account and return an access token.",
    responses={
        409: {"description": "Email already registered"},
    },
)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    """Register a user.

    - Creates a new user with role `user`.
    - Returns a JWT access token and the created user profile.
    """
    existing = db.scalar(select(User).where(User.email == body.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.displayName,
        role=UserRole.user,
    )
    db.add(user)
    db.flush()  # ensure id is available

    token = create_access_token(settings=settings, user_id=user.id, role=user.role)
    return AuthResponse(tokens=AuthTokens(accessToken=token), user=_user_out(user))


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login",
    description="Login with email and password and return an access token.",
    responses={
        401: {"description": "Invalid credentials"},
    },
)
def login(body: LoginRequest, db: Session = Depends(get_db_session), settings: Settings = Depends(get_settings)):
    """Login a user and return JWT."""
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(settings=settings, user_id=user.id, role=user.role)
    return AuthResponse(tokens=AuthTokens(accessToken=token), user=_user_out(user))


@router.get(
    "/me",
    response_model=UserOut,
    summary="Current user",
    description="Return the current authenticated user's profile.",
)
def me(user: User = Depends(get_current_user)):
    """Return current user profile."""
    return _user_out(user)
