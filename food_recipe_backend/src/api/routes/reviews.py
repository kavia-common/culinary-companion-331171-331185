from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.auth.security import get_current_user
from src.api.db.database import get_db_session
from src.api.db.models import Recipe, Review, ReviewStatus
from src.api.mappers import review_to_out
from src.api.schemas import ReviewCreateRequest

router = APIRouter(tags=["reviews"])


@router.get(
    "/recipes/{recipe_id}/reviews",
    summary="List reviews",
    description="List published reviews for a recipe.",
)
def list_reviews(recipe_id: str, db: Session = Depends(get_db_session)):
    """List reviews for recipe (published only)."""
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    reviews = db.scalars(
        select(Review).where((Review.recipe_id == recipe_id) & (Review.status == ReviewStatus.published))
    ).all()
    return [review_to_out(r).model_dump() for r in sorted(reviews, key=lambda x: x.created_at, reverse=True)]


@router.post(
    "/recipes/{recipe_id}/reviews",
    summary="Add review",
    description="Add a review for a recipe (creates a pending review requiring moderation).",
)
def add_review(
    recipe_id: str,
    body: ReviewCreateRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Create a pending review for moderation."""
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    review = Review(
        id=str(uuid.uuid4()),
        recipe_id=recipe_id,
        user_id=user.id,
        rating=body.rating,
        comment=body.comment,
        status=ReviewStatus.pending,
        created_at=datetime.utcnow(),
    )
    db.add(review)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already reviewed this recipe") from exc

    return review_to_out(review).model_dump()


@router.delete(
    "/my/reviews/{review_id}",
    summary="Delete my review",
    description="Delete the current user's review.",
    status_code=204,
)
def delete_my_review(review_id: str, user=Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Delete user's own review."""
    review = db.get(Review, review_id)
    if review is None:
        return None
    if review.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your review")
    db.delete(review)
    return None
