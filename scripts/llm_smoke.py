import asyncio

from openai import AsyncOpenAI

from ai_backend_lab.application.ports.llm import (
    LLMMessage,
    LLMRequest,
    LLMRole,
)
from ai_backend_lab.config import load_settings
from ai_backend_lab.infrastructure.llm.gateway import (
    OpenAILLMGateway,
)


async def main() -> None:
    settings = load_settings()

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

        result = await gateway.generate(
            LLMRequest(
                messages=[
                    LLMMessage(
                        role=LLMRole.USER,
                        content=(
                            "Reply with exactly one short sentence "
                            "confirming that the LLM connection works."
                        ),
                    )
                ]
            )
        )

        print(result.text)

        if result.usage is not None:
            print(
                "tokens:",
                result.usage.total_tokens,
            )


if __name__ == "__main__":
    asyncio.run(main())
