import asyncio

from openai import AsyncOpenAI

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
        api_key=(settings.openai_api_key.get_secret_value()),
        timeout=settings.llm_timeout_seconds,
        max_retries=0,
    ) as client:
        gateway = OpenAILLMGateway(
            client=client,
            model=settings.llm_model,
            max_output_tokens=(settings.llm_max_output_tokens),
            max_attempts=(settings.llm_max_attempts),
            retry_initial_wait=(settings.llm_retry_initial_wait),
            retry_max_wait=(settings.llm_retry_max_wait),
        )

        assistant = OrderAssistantService(llm=gateway)

        result = await assistant.request_tool_call(
            "What is the status of order " "ORD-20261005-ABC123?"
        )

        print("text:", result.text)

        for tool_call in result.tool_calls:
            print("tool:", tool_call.name)
            print(
                "arguments:",
                tool_call.arguments,
            )
            print(
                "call_id:",
                tool_call.call_id,
            )


if __name__ == "__main__":
    asyncio.run(main())
