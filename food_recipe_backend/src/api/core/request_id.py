"""
Request ID middleware.

Flow name: RequestIdFlow
Single entrypoint: install_request_id_middleware(app)

Contract:
  Inputs:
    - app: FastAPI instance
  Outputs:
    - Installs middleware that:
        - reads `X-Request-Id` header if provided, else generates UUID4
        - stores id in request.state.request_id
        - attaches `X-Request-Id` to the response header for all routes
  Side effects:
    - Adds middleware to the FastAPI app
"""

from __future__ import annotations

import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response


# PUBLIC_INTERFACE
def install_request_id_middleware(app: FastAPI) -> None:
    """Install request-id middleware on a FastAPI app."""

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Callable):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = rid

        response: Response = await call_next(request)
        response.headers["x-request-id"] = rid
        return response
