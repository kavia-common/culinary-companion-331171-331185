from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.auth.security import get_current_user
from src.api.db.database import get_db_session
from src.api.db.models import Recipe
from src.api.mappers import (
    apply_recipe_body_to_orm,
    recipe_to_out,
    recipe_to_summary_out,
    replace_ingredients_and_steps,
)
from src.api.schemas import RecipeCreateRequest, RecipeUpdateRequest

router = APIRouter(prefix="/my/recipes", tags=["my-recipes"])


def _new_id() -> str:
    return str(uuid.uuid4())


@router.get(
    "",
    summary="List my recipes",
    description="List recipes authored by the current user.",
)
def list_my_recipes(user=Depends(get_current_user), db: Session = Depends(get_db_session)):
    """List current user's recipes."""
    recipes = db.scalars(select(Recipe).where(Recipe.author_id == user.id)).all()
    return [recipe_to_summary_out(db, r).model_dump() for r in recipes]


@router.post(
    "",
    summary="Create my recipe",
    description="Create a recipe owned by the current user.",
)
def create_my_recipe(
    body: RecipeCreateRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Create a new recipe for current user."""
    recipe = Recipe(id=_new_id(), author_id=user.id, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    apply_recipe_body_to_orm(recipe, body=body)
    replace_ingredients_and_steps(recipe, ingredients=body.ingredients, steps=body.steps, new_id_fn=_new_id)

    db.add(recipe)
    db.flush()

    return recipe_to_out(db, recipe).model_dump()


@router.patch(
    "/{recipe_id}",
    summary="Update my recipe",
    description="Update fields of a recipe owned by the current user.",
)
def update_my_recipe(
    recipe_id: str,
    body: RecipeUpdateRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Update recipe owned by current user."""
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    if recipe.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your recipe")

    apply_recipe_body_to_orm(recipe, body=body)
    recipe.updated_at = datetime.utcnow()

    if body.ingredients is not None and body.steps is not None:
        replace_ingredients_and_steps(recipe, ingredients=body.ingredients, steps=body.steps, new_id_fn=_new_id)
    elif body.ingredients is not None or body.steps is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="To replace ingredients/steps, provide both ingredients and steps.",
        )

    db.add(recipe)
    db.flush()
    return recipe_to_out(db, recipe).model_dump()


@router.delete(
    "/{recipe_id}",
    summary="Delete my recipe",
    description="Delete a recipe owned by the current user.",
    status_code=204,
)
def delete_my_recipe(recipe_id: str, user=Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Delete recipe owned by current user."""
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    if recipe.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your recipe")
    db.delete(recipe)
    return None
