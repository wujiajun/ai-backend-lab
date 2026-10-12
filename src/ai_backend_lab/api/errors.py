from dataclasses import dataclass
from enum import StrEnum

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ai_backend_lab.application.exceptions import (
    RiskServiceIntegrationError,
    RiskServiceUnavailableError,
)
from ai_backend_lab.application.order_agent.exceptions import (
    AgentRunConflictError,
    AgentRunNotFoundError,
    AgentRunStateError,
)
from ai_backend_lab.domain.exceptions import (
    DuplicateOrderError,
    OrderCannotBeCancelledError,
    OrderNotFoundError,
    OrderRejectedError,
)


class ErrorCode(StrEnum):
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    ORDER_CANNOT_BE_CANCELLED = "ORDER_CANNOT_BE_CANCELLED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DUPLICATE_ORDER = "DUPLICATE_ORDER"
    ORDER_REJECTED = "ORDER_REJECTED"
    RISK_SERVICE_UNAVAILABLE = "RISK_SERVICE_UNAVAILABLE"
    RISK_SERVICE_INTEGRATION_ERROR = "RISK_SERVICE_INTEGRATION_ERROR"

    AGENT_RUN_NOT_FOUND = "AGENT_RUN_NOT_FOUND"
    AGENT_RUN_CONFLICT = "AGENT_RUN_CONFLICT"
    AGENT_RUN_STATE_ERROR = "AGENT_RUN_STATE_ERROR"


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    code: ErrorCode
    message: str
    details: list[ErrorDetail] | None = None


@dataclass(frozen=True)
class ErrorDefinition:
    status_code: int
    code: ErrorCode


ERROR_MAPPINGS: dict[type[Exception], ErrorDefinition] = {
    OrderNotFoundError: ErrorDefinition(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.ORDER_NOT_FOUND,
    ),
    OrderCannotBeCancelledError: ErrorDefinition(
        status_code=status.HTTP_409_CONFLICT,
        code=ErrorCode.ORDER_CANNOT_BE_CANCELLED,
    ),
    DuplicateOrderError: ErrorDefinition(
        status_code=status.HTTP_409_CONFLICT,
        code=ErrorCode.DUPLICATE_ORDER,
    ),
    OrderRejectedError: ErrorDefinition(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code=ErrorCode.ORDER_REJECTED,
    ),
    RiskServiceUnavailableError: ErrorDefinition(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code=ErrorCode.RISK_SERVICE_UNAVAILABLE,
    ),
    RiskServiceIntegrationError: ErrorDefinition(
        status_code=status.HTTP_502_BAD_GATEWAY,
        code=ErrorCode.RISK_SERVICE_INTEGRATION_ERROR,
    ),
    AgentRunNotFoundError: ErrorDefinition(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.AGENT_RUN_NOT_FOUND,
    ),
    AgentRunConflictError: ErrorDefinition(
        status_code=status.HTTP_409_CONFLICT,
        code=ErrorCode.AGENT_RUN_CONFLICT,
    ),
    AgentRunStateError: ErrorDefinition(
        status_code=status.HTTP_409_CONFLICT,
        code=ErrorCode.AGENT_RUN_STATE_ERROR,
    ),
}


async def handle_application_error(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    definition = ERROR_MAPPINGS[type(exc)]

    error = ErrorResponse(
        code=definition.code,
        message=str(exc),
    )

    return JSONResponse(
        status_code=definition.status_code,
        content=error.model_dump(mode="json"),
    )


async def handle_validation_error(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    assert isinstance(
        exc,
        RequestValidationError,
    )

    details = [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"] if part != "body"),
            message=error["msg"],
        )
        for error in exc.errors()
    ]

    response = ErrorResponse(
        code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed.",
        details=details,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response.model_dump(mode="json"),
    )


def register_exception_handlers(
    app: FastAPI,
) -> None:
    for exception_type in ERROR_MAPPINGS:
        app.add_exception_handler(
            exception_type,
            handle_application_error,
        )

    app.add_exception_handler(
        RequestValidationError,
        handle_validation_error,
    )
