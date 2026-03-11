from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.auth.security import get_current_user
from src.api.db.database import get_db_session
from src.api.db.models import Favorite, Recipe
from src.api.mappers import recipe_to_summary_out
from src.api.schemas import FavoriteAddRequest

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get(
    "",
    summary="List favorites",
    description="List the current user's favorite recipes.",
)
def list_favorites(user=Depends(get_current_user), db: Session = Depends(get_db_session)):
    """List favorites."""
    favs = db.scalars(select(Favorite).where(Favorite.user_id == user.id)).all()
    recipe_ids = [f.recipe_id for f in favs]
    if not recipe_ids:
        return []
    recipes = db.scalars(select(Recipe).where(Recipe.id.in_(recipe_ids))).all()
    by_id = {r.id: r for r in recipes}
    # Preserve insertion order roughly by favorites list
    out = [recipe_to_summary_out(db, by_id[rid]).model_dump() for rid in recipe_ids if rid in by_id]
    return out


@router.post(
    "",
    summary="Add favorite",
    description="Favorite a recipe for the current user.",
    status_code=204,
)
def add_favorite(body: FavoriteAddRequest, user=Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Add favorite recipe."""
    recipe = db.get(Recipe, body.recipeId)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    fav = Favorite(id=str(uuid.uuid4()), user_id=user.id, recipe_id=body.recipeId)
    db.add(fav)
    try:
        db.flush()
    except IntegrityError:
        # Already favorited (unique constraint)
        db.rollback()
    return None


@router.delete(
    "/{recipe_id}",
    summary="Remove favorite",
    description="Unfavorite a recipe.",
    status_code=204,
)
def remove_favorite(recipe_id: str, user=Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Remove favorite."""
    fav = db.scalar(select(Favorite).where((Favorite.user_id == user.id) & (Favorite.recipe_id == recipe_id)))
    if fav is None:
        return None
    db.delete(fav)
    return None
