from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.orm import Session

from src.api.db.database import get_db_session
from src.api.db.models import Recipe
from src.api.mappers import recipe_to_out, recipe_to_summary_out

router = APIRouter(tags=["recipes"])


@router.get(
    "/recipes",
    summary="Search recipes",
    description="Browse/search recipes with filters and pagination.",
    response_model=dict,
)
def search_recipes(
    q: str | None = Query(default=None, description="Full-text-ish search in title/description."),
    cuisine: str | None = Query(default=None, description="Cuisine filter."),
    dietary: str | None = Query(default=None, description="Dietary tag filter (single tag)."),
    maxCookTimeMinutes: int | None = Query(default=None, ge=0, description="Maximum cook time minutes."),
    difficulty: str | None = Query(default=None, description="Difficulty: easy|medium|hard."),
    sort: str | None = Query(default="relevance", description="Sort: relevance|rating|newest."),
    page: int = Query(default=1, ge=1, description="Page number."),
    pageSize: int = Query(default=12, ge=1, le=100, description="Page size."),
    db: Session = Depends(get_db_session),
):
    """Search recipes.

    Note: For SQLite, we implement simple `LIKE` matching for q.
    """
    filters = []
    if q:
        like = f"%{q.strip()}%"
        filters.append(or_(Recipe.title.ilike(like), Recipe.description.ilike(like)))
    if cuisine:
        filters.append(Recipe.cuisine == cuisine)
    if dietary:
        like = f"%{dietary.strip()}%"
        filters.append(Recipe.dietary_tags_csv.ilike(like))
    if maxCookTimeMinutes is not None:
        filters.append(Recipe.cook_time_minutes <= maxCookTimeMinutes)
    if difficulty:
        filters.append(Recipe.difficulty == difficulty)

    where_clause = and_(*filters) if filters else None

    base_stmt = select(Recipe)
    if where_clause is not None:
        base_stmt = base_stmt.where(where_clause)

    if sort == "newest":
        base_stmt = base_stmt.order_by(desc(Recipe.created_at))
    else:
        # "relevance" and "rating" both default to newest for now; rating is computed per item in mapper.
        base_stmt = base_stmt.order_by(desc(Recipe.created_at))

    total = db.execute(
        select(Recipe.id).where(where_clause) if where_clause is not None else select(Recipe.id)
    ).all()
    total_count = len(total)

    offset = (page - 1) * pageSize
    items = db.scalars(base_stmt.offset(offset).limit(pageSize)).all()
    out_items = [recipe_to_summary_out(db, r) for r in items]

    return {"items": [i.model_dump() for i in out_items], "page": page, "pageSize": pageSize, "total": total_count}


@router.get(
    "/recipes/{recipe_id}",
    summary="Get recipe",
    description="Get a full recipe by id.",
)
def get_recipe(recipe_id: str, db: Session = Depends(get_db_session)):
    """Get a full recipe."""
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe_to_out(db, recipe).model_dump()
