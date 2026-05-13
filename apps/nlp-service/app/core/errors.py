from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(HTTPException, _http_exception_handler)
