from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    moderator = "moderator"


class ReviewStatus(str, enum.Enum):
    published = "published"
    pending = "pending"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.user)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    recipes = relationship("Recipe", back_populates="author", cascade="all,delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all,delete-orphan")
    shopping_items = relationship("ShoppingListItem", back_populates="user", cascade="all,delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all,delete-orphan")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(String, primary_key=True)
    author_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)

    cuisine = Column(String, nullable=True, index=True)
    dietary_tags_csv = Column(String, nullable=True)  # stored as CSV for SQLite simplicity

    cook_time_minutes = Column(Integer, nullable=True, index=True)
    difficulty = Column(String, nullable=True, index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    ingredients = relationship("Ingredient", back_populates="recipe", cascade="all,delete-orphan")
    steps = relationship("Step", back_populates="recipe", cascade="all,delete-orphan")
    reviews = relationship("Review", back_populates="recipe", cascade="all,delete-orphan")

    author = relationship("User", back_populates="recipes")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(String, primary_key=True)
    recipe_id = Column(String, ForeignKey("recipes.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    quantity = Column(String, nullable=True)

    recipe = relationship("Recipe", back_populates="ingredients")


class Step(Base):
    __tablename__ = "steps"

    id = Column(String, primary_key=True)
    recipe_id = Column(String, ForeignKey("recipes.id"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    recipe = relationship("Recipe", back_populates="steps")

    __table_args__ = (UniqueConstraint("recipe_id", "step_order", name="uq_steps_recipe_order"),)


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    recipe_id = Column(String, ForeignKey("recipes.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")

    __table_args__ = (UniqueConstraint("user_id", "recipe_id", name="uq_fav_user_recipe"),)


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    text = Column(String, nullable=False)
    checked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="shopping_items")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True)
    recipe_id = Column(String, ForeignKey("recipes.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(Enum(ReviewStatus), nullable=False, default=ReviewStatus.pending)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    recipe = relationship("Recipe", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        UniqueConstraint("recipe_id", "user_id", name="uq_review_recipe_user"),
    )
