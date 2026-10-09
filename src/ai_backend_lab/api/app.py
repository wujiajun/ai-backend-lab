from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

import httpx
from fastapi import FastAPI
from openai import AsyncOpenAI

from ai_backend_lab.api.errors import register_exception_handlers
from ai_backend_lab.api.routers.order_assistant import router as order_assistant_router
from ai_backend_lab.api.routers.orders import router as orders_router
from ai_backend_lab.config import load_settings
from ai_backend_lab.infrastructure.database.database import engine
from ai_backend_lab.observability.logging import (
    configure_logging,
)
from ai_backend_lab.observability.middleware import (
    request_context_middleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = load_settings()
    configure_logging(settings.log_level)

    timeout = httpx.Timeout(
        connect=settings.risk_connect_timeout,
        read=settings.risk_read_timeout,
        write=settings.risk_write_timeout,
        pool=settings.risk_pool_timeout,
    )

    try:
        async with AsyncExitStack() as stack:
            http_client = await stack.enter_async_context(
                httpx.AsyncClient(
                    base_url=settings.risk_service_base_url,
                    timeout=timeout,
                )
            )

            openai_client = await stack.enter_async_context(
                AsyncOpenAI(
                    api_key=settings.openai_api_key.get_secret_value(),
                    timeout=settings.llm_timeout_seconds,
                    max_retries=0,
                )
            )
            app.state.http_client = http_client
            app.state.openai_client = openai_client

            yield
    finally:
        engine.dispose()


app = FastAPI(lifespan=lifespan)
app.middleware("http")(request_context_middleware)
register_exception_handlers(app=app)
app.include_router(orders_router)
app.include_router(order_assistant_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AI Backend Lab is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
