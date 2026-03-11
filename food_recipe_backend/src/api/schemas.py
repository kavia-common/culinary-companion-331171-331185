from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


Id = str
UserRole = Literal["user", "admin", "moderator"]
RecipeDifficulty = Literal["easy", "medium", "hard"]
ReviewStatus = Literal["published", "pending", "rejected"]


class UserOut(BaseModel):
    id: Id = Field(..., description="User id.")
    email: str = Field(..., description="User email.")
    displayName: Optional[str] = Field(None, description="Display name.")
    role: UserRole = Field(..., description="User role.")


class AuthTokens(BaseModel):
    accessToken: str = Field(..., description="JWT access token.")


class AuthResponse(BaseModel):
    tokens: AuthTokens = Field(..., description="Auth tokens.")
    user: UserOut = Field(..., description="Authenticated user profile.")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email.")
    password: str = Field(..., min_length=6, description="User password (min 6 chars).")
    displayName: Optional[str] = Field(None, description="Optional display name.")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email.")
    password: str = Field(..., description="User password.")


class IngredientIn(BaseModel):
    name: str = Field(..., description="Ingredient name.")
    quantity: Optional[str] = Field(None, description="Ingredient quantity (e.g. '2 tbsp').")


class StepIn(BaseModel):
    order: int = Field(..., ge=1, description="Step order (1..n).")
    text: str = Field(..., description="Step text.")


class RecipeSummaryOut(BaseModel):
    id: Id = Field(..., description="Recipe id.")
    title: str = Field(..., description="Recipe title.")
    description: Optional[str] = Field(None, description="Short description.")
    imageUrl: Optional[str] = Field(None, description="Image URL.")
    cuisine: Optional[str] = Field(None, description="Cuisine.")
    dietaryTags: Optional[List[str]] = Field(None, description="Dietary tags.")
    cookTimeMinutes: Optional[int] = Field(None, ge=0, description="Cook time in minutes.")
    difficulty: Optional[RecipeDifficulty] = Field(None, description="Difficulty.")
    averageRating: Optional[float] = Field(None, description="Average rating.")
    ratingsCount: Optional[int] = Field(None, ge=0, description="Number of ratings.")


class RecipeOut(RecipeSummaryOut):
    authorId: Optional[Id] = Field(None, description="Author user id.")
    ingredients: List[IngredientIn] = Field(..., description="Ingredients list.")
    steps: List[StepIn] = Field(..., description="Steps list.")


class RecipeCreateRequest(BaseModel):
    title: str = Field(..., description="Recipe title.")
    description: Optional[str] = Field(None, description="Recipe description.")
    imageUrl: Optional[str] = Field(None, description="Image URL.")
    cuisine: Optional[str] = Field(None, description="Cuisine.")
    dietaryTags: Optional[List[str]] = Field(None, description="Dietary tags.")
    cookTimeMinutes: Optional[int] = Field(None, ge=0, description="Cook time in minutes.")
    difficulty: Optional[RecipeDifficulty] = Field(None, description="Difficulty.")
    ingredients: List[IngredientIn] = Field(..., min_length=1, description="Ingredients list.")
    steps: List[StepIn] = Field(..., min_length=1, description="Steps list.")


class RecipeUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Recipe title.")
    description: Optional[str] = Field(None, description="Recipe description.")
    imageUrl: Optional[str] = Field(None, description="Image URL.")
    cuisine: Optional[str] = Field(None, description="Cuisine.")
    dietaryTags: Optional[List[str]] = Field(None, description="Dietary tags.")
    cookTimeMinutes: Optional[int] = Field(None, ge=0, description="Cook time in minutes.")
    difficulty: Optional[RecipeDifficulty] = Field(None, description="Difficulty.")
    ingredients: Optional[List[IngredientIn]] = Field(None, description="Replace ingredients list.")
    steps: Optional[List[StepIn]] = Field(None, description="Replace steps list.")


class Paginated(BaseModel):
    items: List[RecipeSummaryOut] = Field(..., description="Items for the requested page.")
    page: int = Field(..., ge=1, description="Current page number.")
    pageSize: int = Field(..., ge=1, le=100, description="Page size.")
    total: int = Field(..., ge=0, description="Total matching items.")


class FavoriteAddRequest(BaseModel):
    recipeId: Id = Field(..., description="Recipe to favorite.")


class ShoppingListItemOut(BaseModel):
    id: Id = Field(..., description="Shopping list item id.")
    text: str = Field(..., description="Item text.")
    checked: bool = Field(..., description="Whether the item is checked.")


class ShoppingListOut(BaseModel):
    items: List[ShoppingListItemOut] = Field(..., description="Shopping list items.")


class ShoppingAddFromRecipeRequest(BaseModel):
    recipeId: Id = Field(..., description="Recipe id to add ingredients from.")


class ShoppingToggleRequest(BaseModel):
    checked: bool = Field(..., description="New checked state.")


class ReviewOut(BaseModel):
    id: Id = Field(..., description="Review id.")
    recipeId: Id = Field(..., description="Recipe id.")
    userId: Id = Field(..., description="User id.")
    rating: int = Field(..., ge=1, le=5, description="Rating 1..5.")
    comment: Optional[str] = Field(None, description="Optional comment.")
    createdAt: datetime = Field(..., description="Created timestamp (UTC).")
    status: Optional[ReviewStatus] = Field(None, description="Moderation status.")


class ReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating 1..5.")
    comment: Optional[str] = Field(None, description="Optional comment.")


class ModerateReviewAction(BaseModel):
    action: Literal["approve", "reject"] = Field(..., description="Moderation action.")
