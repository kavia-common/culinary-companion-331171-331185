"""
Error handling utilities for the FastAPI application.

We standardize error responses to make frontend integration predictable and debuggable.

Flow name: ApiErrorResponseFlow
Single entrypoint: install_error_handlers(app)

Contract:
  Inputs:
    - app: FastAPI instance
  Outputs:
    - Installs exception handlers that return a consistent JSON error body
  Error shape (JSON):
    {
      "error": {
        "message": string,
        "code": string,
        "details": any | null,
        "requestId": string | null
      }
    }
  Side effects:
    - Registers exception handlers on the FastAPI app
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _request_id_from_scope(request: Request) -> Optional[str]:
    """
    Attempt to read request id injected by middleware (or from header).
    """
    rid = request.state.__dict__.get("request_id")
    if isinstance(rid, str) and rid:
        return rid
    header_rid = request.headers.get("x-request-id")
    return header_rid or None


def _error_body(*, message: str, code: str, details: Any, request_id: Optional[str]) -> Dict[str, Any]:
    return {
        "error": {
            "message": message,
            "code": code,
            "details": details,
            "requestId": request_id,
        }
    }


# PUBLIC_INTERFACE
def install_error_handlers(app: FastAPI) -> None:
    """Install standardized exception handlers on a FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = _request_id_from_scope(request)
        # FastAPI uses "detail" for HTTPException, which can be str or any JSON-serializable payload.
        details = exc.detail
        message = details if isinstance(details, str) else "Request failed"
        code = "http_error"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(message=message, code=code, details=details, request_id=request_id),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = _request_id_from_scope(request)
        return JSONResponse(
            status_code=422,
            content=_error_body(
                message="Validation error",
                code="validation_error",
                details=exc.errors(),
                request_id=request_id,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = _request_id_from_scope(request)
        # Avoid leaking internals; provide details only as string for debuggability.
        return JSONResponse(
            status_code=500,
            content=_error_body(
                message="Internal server error",
                code="internal_error",
                details=str(exc),
                request_id=request_id,
            ),
        )
