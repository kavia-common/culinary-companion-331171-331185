import logging
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.config import Settings, get_settings
from src.api.core.errors import install_error_handlers
from src.api.core.request_id import install_request_id_middleware
from src.api.db.database import init_db, session_scope
from src.api.db.init import ensure_schema_and_seed
from src.api.routes import admin, auth, favorites, my_recipes, recipes, reviews, shopping_list

logger = logging.getLogger(__name__)

openapi_tags: List[dict] = [
    {"name": "health", "description": "Service health checks."},
    {"name": "auth", "description": "Authentication and user session endpoints."},
    {"name": "recipes", "description": "Public recipe browsing, search, and details."},
    {"name": "my-recipes", "description": "Create/update/delete recipes owned by the current user."},
    {"name": "favorites", "description": "Favorite recipes for the current user."},
    {"name": "shopping-list", "description": "Shopping list management for the current user."},
    {"name": "reviews", "description": "Recipe reviews and ratings (with moderation workflow)."},
    {"name": "admin", "description": "Admin/moderation endpoints (roles enforced)."},
]

app = FastAPI(
    title="Culinary Companion API",
    description=(
        "Backend REST API for the Culinary Companion app.\n\n"
        "Auth: Use `Authorization: Bearer <accessToken>` for protected endpoints.\n"
        "Roles: `user`, `moderator`, `admin`.\n"
        "Moderation: New reviews are created as `pending` and must be approved by an admin/moderator.\n\n"
        "Error shape:\n"
        "  {\"error\": {\"message\": str, \"code\": str, \"details\": any, \"requestId\": str|null}}\n"
        "Request tracing:\n"
        "  Every response includes an `x-request-id` header."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# Install cross-cutting concerns early so every route is covered.
install_request_id_middleware(app)
install_error_handlers(app)


def _configure_cors(settings: Settings) -> None:
    """
    Configure CORS for browser-based clients.

    Important invariant:
      - If allow_credentials=True, allow_origins cannot be ["*"].
        Browsers will reject credentialed CORS responses with wildcard origin.
    """
    allow_origins = settings.cors_allow_origins
    allow_credentials = True

    # Make wildcard safe by disabling credentials in that case.
    if "*" in allow_origins:
        allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-request-id"],
    )


@app.on_event("startup")
def _startup():
    """Initialize settings, database connection, schema, and seed data on startup."""
    settings = get_settings()
    _configure_cors(settings)
    init_db(settings)

    # Create schema + seed admin if DB is empty
    with session_scope() as db:
        ensure_schema_and_seed(db)


@app.get("/", tags=["health"], summary="Health check", description="Health check endpoint.")
def health_check():
    """Return a simple health payload."""
    return {"message": "Healthy"}


# Routers
app.include_router(auth.router)
app.include_router(recipes.router)
app.include_router(my_recipes.router)
app.include_router(favorites.router)
app.include_router(shopping_list.router)
app.include_router(reviews.router)
app.include_router(admin.router)
