from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.api.auth.security import get_current_user
from src.api.db.database import get_db_session
from src.api.db.models import Ingredient, Recipe, ShoppingListItem
from src.api.schemas import (
    ShoppingAddFromRecipeRequest,
    ShoppingListOut,
    ShoppingListItemOut,
    ShoppingToggleRequest,
)

router = APIRouter(prefix="/shopping-list", tags=["shopping-list"])


@router.get(
    "",
    response_model=ShoppingListOut,
    summary="Get shopping list",
    description="Get the current user's shopping list.",
)
def get_list(user=Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Get shopping list items."""
    items = db.scalars(select(ShoppingListItem).where(ShoppingListItem.user_id == user.id)).all()
    out = [
        ShoppingListItemOut(id=i.id, text=i.text, checked=bool(i.checked))
        for i in sorted(items, key=lambda x: x.created_at)
    ]
    return ShoppingListOut(items=out)


@router.post(
    "/from-recipe",
    summary="Add from recipe",
    description="Add recipe ingredients to the current user's shopping list.",
    status_code=204,
)
def add_from_recipe(
    body: ShoppingAddFromRecipeRequest, user=Depends(get_current_user), db: Session = Depends(get_db_session)
):
    """Add ingredients from recipe to shopping list."""
    recipe = db.get(Recipe, body.recipeId)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    ingredients = db.scalars(select(Ingredient).where(Ingredient.recipe_id == recipe.id)).all()
    for ing in ingredients:
        text = ing.name if not ing.quantity else f"{ing.quantity} {ing.name}"
        db.add(ShoppingListItem(id=str(uuid.uuid4()), user_id=user.id, text=text, checked=False))
    db.flush()
    return None


@router.patch(
    "/{item_id}",
    summary="Toggle item",
    description="Toggle checked state for a shopping list item.",
    status_code=204,
)
def toggle_item(
    item_id: str,
    body: ShoppingToggleRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Toggle a shopping list item."""
    item = db.get(ShoppingListItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    item.checked = bool(body.checked)
    db.add(item)
    return None


@router.delete(
    "/{item_id}",
    summary="Remove item",
    description="Remove a shopping list item.",
    status_code=204,
)
def remove_item(item_id: str, user=Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Remove item."""
    item = db.get(ShoppingListItem, item_id)
    if item is None or item.user_id != user.id:
        return None
    db.delete(item)
    return None


@router.post(
    "/clear-checked",
    summary="Clear checked",
    description="Remove all checked items from the shopping list.",
    status_code=204,
)
def clear_checked(user=Depends(get_current_user), db: Session = Depends(get_db_session)):
    """Clear checked items."""
    db.execute(delete(ShoppingListItem).where((ShoppingListItem.user_id == user.id) & (ShoppingListItem.checked == True)))  # noqa: E712
    return None
