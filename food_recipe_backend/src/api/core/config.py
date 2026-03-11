import os
import secrets
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables.

    Contract:
      - Inputs: environment variables (strings)
      - Outputs: strongly typed settings object
      - Errors: raises ValueError for invalid numeric values
      - Side effects: none (reads env only)
    """

    jwt_secret: str
    jwt_algorithm: str
    jwt_access_token_expires_minutes: int
    database_url: str
    cors_allow_origins: List[str]


def _env_first(*names: str) -> str | None:
    """Return the first non-empty environment variable from the provided names."""
    for name in names:
        val = os.getenv(name)
        if val is not None and str(val).strip() != "":
            return val
    return None


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load and validate application settings from environment variables.

    Notes for Kavia preview:
      - The preview runtime often injects `NEXT_PUBLIC_*` variables (shared with the frontend)
        rather than backend-specific ones. We accept those as fallbacks to avoid startup crashes.

    Preferred variables:
      - JWT_SECRET (preferred). If missing, we will fall back to NEXT_PUBLIC_* equivalents.
        If still missing, we generate a temporary random secret in non-production environments
        to allow the service to boot in preview/dev. Production deployments should always set
        JWT_SECRET explicitly.

    Optional:
      - JWT_ALGORITHM (default: HS256)
      - JWT_ACCESS_TOKEN_EXPIRES_MINUTES (default: 10080)
      - DATABASE_URL (default: sqlite:///./data/app.db)
      - CORS_ALLOW_ORIGINS (default: "*", or falls back to ALLOWED_ORIGINS)

    Returns:
      Settings: parsed settings.

    Raises:
      ValueError: if JWT_ACCESS_TOKEN_EXPIRES_MINUTES is not an integer.
    """
    node_env = (os.getenv("NODE_ENV") or os.getenv("NEXT_PUBLIC_NODE_ENV") or "").strip().lower()

    jwt_secret = _env_first("JWT_SECRET", "NEXT_PUBLIC_JWT_SECRET")
    if not jwt_secret:
        # Allow preview/dev to boot even when JWT_SECRET isn't wired.
        # This secret is process-local and will change on restart.
        if node_env in {"production", "prod"}:
            raise ValueError("JWT_SECRET is required (set it in the environment).")
        jwt_secret = secrets.token_urlsafe(48)

    jwt_algorithm = _env_first("JWT_ALGORITHM", "NEXT_PUBLIC_JWT_ALGORITHM") or "HS256"
    expires_raw = _env_first(
        "JWT_ACCESS_TOKEN_EXPIRES_MINUTES",
        "NEXT_PUBLIC_JWT_ACCESS_TOKEN_EXPIRES_MINUTES",
    ) or "10080"
    try:
        expires_minutes = int(expires_raw)
    except ValueError as exc:
        raise ValueError("JWT_ACCESS_TOKEN_EXPIRES_MINUTES must be an integer.") from exc

    database_url = _env_first("DATABASE_URL", "NEXT_PUBLIC_DATABASE_URL") or "sqlite:///./data/app.db"

    cors_raw = (_env_first("CORS_ALLOW_ORIGINS", "ALLOWED_ORIGINS", "NEXT_PUBLIC_CORS_ALLOW_ORIGINS") or "*").strip()
    if cors_raw == "*":
        cors_allow_origins = ["*"]
    else:
        cors_allow_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]

    return Settings(
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm,
        jwt_access_token_expires_minutes=expires_minutes,
        database_url=database_url,
        cors_allow_origins=cors_allow_origins,
    )
