from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.auth.security import require_role
from src.api.db.database import get_db_session
from src.api.db.models import Review, ReviewStatus, User, UserRole
from src.api.mappers import review_to_out
from src.api.schemas import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/reviews/pending",
    summary="List pending reviews",
    description="List reviews awaiting moderation (admin/moderator only).",
)
def list_pending_reviews(
    _admin_or_mod=Depends(require_role(UserRole.admin, UserRole.moderator)),
    db: Session = Depends(get_db_session),
):
    """List pending reviews."""
    reviews = db.scalars(select(Review).where(Review.status == ReviewStatus.pending)).all()
    return [review_to_out(r).model_dump() for r in sorted(reviews, key=lambda x: x.created_at, reverse=True)]


@router.post(
    "/reviews/{review_id}/approve",
    summary="Approve review",
    description="Approve a pending review (admin/moderator only).",
    status_code=204,
)
def approve_review(
    review_id: str,
    _admin_or_mod=Depends(require_role(UserRole.admin, UserRole.moderator)),
    db: Session = Depends(get_db_session),
):
    """Approve a review."""
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    review.status = ReviewStatus.published
    db.add(review)
    return None


@router.post(
    "/reviews/{review_id}/reject",
    summary="Reject review",
    description="Reject a pending review (admin/moderator only).",
    status_code=204,
)
def reject_review(
    review_id: str,
    _admin_or_mod=Depends(require_role(UserRole.admin, UserRole.moderator)),
    db: Session = Depends(get_db_session),
):
    """Reject a review."""
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    review.status = ReviewStatus.rejected
    db.add(review)
    return None


@router.get(
    "/users",
    summary="List users",
    description="List users (admin only).",
)
def list_users(
    _admin=Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db_session),
):
    """List all users."""
    users = db.scalars(select(User)).all()
    return [
        UserOut(id=u.id, email=u.email, displayName=u.display_name, role=u.role.value).model_dump()
        for u in sorted(users, key=lambda x: x.created_at)
    ]
