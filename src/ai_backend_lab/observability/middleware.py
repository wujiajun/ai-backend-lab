import logging
import re
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import (
    RequestResponseEndpoint,
)

from ai_backend_lab.observability.context import (
    request_id_var,
)

logger = logging.getLogger("ai_backend_lab.http")


REQUEST_ID_HEADER = "X-Request-ID"

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


async def request_context_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    request_id = resolve_request_id(request)

    token = request_id_var.set(request_id)

    start = perf_counter()

    logger.info(
        "Request started method=%s path=%s",
        request.method,
        request.url.path,
    )

    try:
        response = await call_next(request)

        duration_ms = (perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "Request finished " "method=%s path=%s " "status=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response

    except Exception:
        duration_ms = (perf_counter() - start) * 1000

        logger.exception(
            "Request failed " "method=%s path=%s " "duration_ms=%.2f",
            request.method,
            request.url.path,
            duration_ms,
        )

        raise

    finally:
        request_id_var.reset(token)


def resolve_request_id(
    request: Request,
) -> str:
    incoming_request_id = request.headers.get(REQUEST_ID_HEADER)

    if incoming_request_id is not None and REQUEST_ID_PATTERN.fullmatch(
        incoming_request_id
    ):
        return incoming_request_id

    return uuid4().hex
