import os
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


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load and validate application settings from environment variables.

    Required:
      - JWT_SECRET

    Optional:
      - JWT_ALGORITHM (default: HS256)
      - JWT_ACCESS_TOKEN_EXPIRES_MINUTES (default: 10080)
      - DATABASE_URL (default: sqlite:///./data/app.db)
      - CORS_ALLOW_ORIGINS (default: "*")

    Returns:
      Settings: parsed settings.

    Raises:
      ValueError: if JWT_ACCESS_TOKEN_EXPIRES_MINUTES is not an integer, or JWT_SECRET missing.
    """
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise ValueError("JWT_SECRET is required (set it in the environment).")

    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expires_raw = os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "10080")
    try:
        expires_minutes = int(expires_raw)
    except ValueError as exc:
        raise ValueError("JWT_ACCESS_TOKEN_EXPIRES_MINUTES must be an integer.") from exc

    database_url = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

    cors_raw = os.getenv("CORS_ALLOW_ORIGINS", "*").strip()
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
