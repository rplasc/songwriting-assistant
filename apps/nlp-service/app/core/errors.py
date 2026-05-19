from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.languages.base import UnsupportedModeError
from app.services.language_router import UnsupportedLanguageError


def _envelope(code: str, message: str, details: list | None = None, status_code: int = 400) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "details": details or []}}
    return JSONResponse(status_code=status_code, content=body)


async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _envelope(
        code="validation_error",
        message="Request payload failed validation.",
        details=jsonable_encoder(exc.errors(), custom_encoder={Exception: str}),
        status_code=422,
    )


async def _http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return _envelope(
        code="http_error",
        message=str(exc.detail) if exc.detail else "Request failed.",
        status_code=exc.status_code,
    )


async def _unsupported_language_handler(
    _: Request, exc: UnsupportedLanguageError
) -> JSONResponse:
    return _envelope(
        code="unsupported_language",
        message=str(exc),
        details=[{"language": exc.code, "supported": list(exc.supported)}],
        status_code=422,
    )


async def _unsupported_mode_handler(
    _: Request, exc: UnsupportedModeError
) -> JSONResponse:
    return _envelope(
        code="unsupported_mode",
        message=str(exc),
        status_code=422,
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(UnsupportedLanguageError, _unsupported_language_handler)
    app.add_exception_handler(UnsupportedModeError, _unsupported_mode_handler)
