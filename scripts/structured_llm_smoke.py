import asyncio

from openai import AsyncOpenAI

from ai_backend_lab.application.order_assistant.models import (
    OrderIntent,
)
from ai_backend_lab.application.order_assistant.service import (
    OrderAssistantService,
)
from ai_backend_lab.config import load_settings
from ai_backend_lab.infrastructure.llm.gateway import (
    OpenAILLMGateway,
)
from ai_backend_lab.observability.logging import (
    configure_logging,
)


async def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    async with AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=settings.llm_timeout_seconds,
        max_retries=0,
    ) as client:
        gateway = OpenAILLMGateway(
            client=client,
            model=settings.llm_model,
            max_output_tokens=settings.llm_max_output_tokens,
            max_attempts=2,
            retry_initial_wait=0.1,
            retry_max_wait=0.5,
        )
        assistant = OrderAssistantService(llm=gateway)

        order_intent: OrderIntent = await assistant.extract_intent(
            "Please cancel order ORD-20261003-ABC123."
        )

        print(order_intent)
        print(order_intent.action.value)
        print(order_intent.order_number)


if __name__ == "__main__":
    asyncio.run(main())
