from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.db.models import Ingredient, Recipe, Review, ReviewStatus, Step
from src.api.schemas import IngredientIn, RecipeOut, RecipeSummaryOut, ReviewOut, StepIn


def _split_csv(csv: Optional[str]) -> Optional[List[str]]:
    if not csv:
        return None
    parts = [p.strip() for p in csv.split(",") if p.strip()]
    return parts or None


def _join_csv(items: Optional[List[str]]) -> Optional[str]:
    if not items:
        return None
    cleaned = [i.strip() for i in items if i and i.strip()]
    return ",".join(cleaned) if cleaned else None


# PUBLIC_INTERFACE
def recipe_to_out(db: Session, recipe: Recipe) -> RecipeOut:
    """Map a Recipe ORM object to the public RecipeOut API schema.

    Includes computed fields:
      - averageRating
      - ratingsCount
    """
    avg, cnt = _rating_stats(db, recipe.id)
    ingredients = [IngredientIn(name=i.name, quantity=i.quantity) for i in sorted(recipe.ingredients, key=lambda x: x.name)]
    steps = [
        StepIn(order=s.step_order, text=s.text)
        for s in sorted(recipe.steps, key=lambda x: x.step_order)
    ]
    return RecipeOut(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description,
        imageUrl=recipe.image_url,
        cuisine=recipe.cuisine,
        dietaryTags=_split_csv(recipe.dietary_tags_csv),
        cookTimeMinutes=recipe.cook_time_minutes,
        difficulty=recipe.difficulty,
        averageRating=avg,
        ratingsCount=cnt,
        authorId=recipe.author_id,
        ingredients=ingredients,
        steps=steps,
    )


# PUBLIC_INTERFACE
def recipe_to_summary_out(db: Session, recipe: Recipe) -> RecipeSummaryOut:
    """Map a Recipe ORM object to a public RecipeSummaryOut API schema."""
    avg, cnt = _rating_stats(db, recipe.id)
    return RecipeSummaryOut(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description,
        imageUrl=recipe.image_url,
        cuisine=recipe.cuisine,
        dietaryTags=_split_csv(recipe.dietary_tags_csv),
        cookTimeMinutes=recipe.cook_time_minutes,
        difficulty=recipe.difficulty,
        averageRating=avg,
        ratingsCount=cnt,
    )


def _rating_stats(db: Session, recipe_id: str) -> Tuple[Optional[float], int]:
    published = ReviewStatus.published
    row = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(
            (Review.recipe_id == recipe_id) & (Review.status == published)
        )
    ).one()
    avg = float(row[0]) if row[0] is not None else None
    cnt = int(row[1] or 0)
    return avg, cnt


# PUBLIC_INTERFACE
def review_to_out(review: Review) -> ReviewOut:
    """Map Review ORM object to ReviewOut."""
    return ReviewOut(
        id=review.id,
        recipeId=review.recipe_id,
        userId=review.user_id,
        rating=review.rating,
        comment=review.comment,
        createdAt=review.created_at,
        status=review.status.value if review.status is not None else None,
    )


# PUBLIC_INTERFACE
def apply_recipe_body_to_orm(recipe: Recipe, *, body) -> None:
    """Apply create/update body fields to a Recipe ORM object.

    body can be RecipeCreateRequest or RecipeUpdateRequest-like.
    """
    if getattr(body, "title", None) is not None:
        recipe.title = body.title
    if getattr(body, "description", None) is not None:
        recipe.description = body.description
    if getattr(body, "imageUrl", None) is not None:
        recipe.image_url = body.imageUrl
    if getattr(body, "cuisine", None) is not None:
        recipe.cuisine = body.cuisine
    if getattr(body, "dietaryTags", None) is not None:
        recipe.dietary_tags_csv = _join_csv(body.dietaryTags)
    if getattr(body, "cookTimeMinutes", None) is not None:
        recipe.cook_time_minutes = body.cookTimeMinutes
    if getattr(body, "difficulty", None) is not None:
        recipe.difficulty = body.difficulty


# PUBLIC_INTERFACE
def replace_ingredients_and_steps(
    recipe: Recipe,
    *,
    ingredients: List[IngredientIn],
    steps: List[StepIn],
    new_id_fn,
) -> None:
    """Replace ingredients and steps collections for a recipe."""
    recipe.ingredients = [Ingredient(id=new_id_fn(), name=i.name, quantity=i.quantity) for i in ingredients]
    recipe.steps = [Step(id=new_id_fn(), step_order=s.order, text=s.text) for s in steps]
