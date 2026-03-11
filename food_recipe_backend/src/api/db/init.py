from __future__ import annotations

import logging
import uuid

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.db.database import get_engine
from src.api.db.models import Base, User, UserRole

logger = logging.getLogger(__name__)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return _pwd_context.hash(password)


# PUBLIC_INTERFACE
def ensure_schema_and_seed(db: Session) -> None:
    """Create DB schema and seed minimal data if needed.

    Contract:
      - Inputs: db session (initialized and connected)
      - Outputs: schema exists; at least one admin user exists if DB was empty
      - Errors: SQLAlchemy errors bubble up with context from caller boundary
      - Side effects: creates tables; inserts seed admin user if required

    Seed behavior:
      - If there are zero users, creates:
        email: admin@example.com
        password: admin1234
        role: admin
      This is intended for development/demo only. Production should provision users differently.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    users_count = db.scalar(select(User).limit(1))
    if users_count is not None:
        return

    admin = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        password_hash=_hash_password("admin1234"),
        display_name="Admin",
        role=UserRole.admin,
    )
    db.add(admin)
    logger.warning(
        "Seeded default admin user admin@example.com with password admin1234 (development only)."
    )
