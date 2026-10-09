import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from time import perf_counter
from typing import TypeVar

import openai
from openai import AsyncOpenAI
from openai.types.responses import (
    EasyInputMessageParam,
    FunctionToolParam,
    ResponseInputItemParam,
)
from openai.types.responses.response_input_param import (
    FunctionCallOutput,
)
from pydantic import BaseModel, ValidationError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ai_backend_lab.application.exceptions import (
    LLMIntegrationError,
    LLMOutputError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMUnavailableError,
)
from ai_backend_lab.application.ports.llm import (
    LLMGateway,
    LLMRequest,
    LLMResult,
    LLMToolCall,
    LLMToolDefinition,
    LLMUsage,
    StructuredLLMResult,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R")


class _RetryableLLMUnavailableError(Exception):
    pass


class _RetryableLLMRateLimitError(Exception):
    pass


class OpenAILLMGateway(LLMGateway):
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        max_output_tokens: int,
        max_attempts: int,
        retry_initial_wait: float,
        retry_max_wait: float,
    ):
        self._client = client
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._max_attempts = max_attempts
        self._retry_initial_wait = retry_initial_wait
        self._retry_max_wait = retry_max_wait

    async def generate(self, request: LLMRequest) -> LLMResult:
        start = perf_counter()
        response = await self._execute_with_retry(
            lambda: self._client.responses.create(
                model=self._model,
                instructions=request.instructions,
                input=self._map_input(request),
                tools=self._map_tools(request.tools),
                max_output_tokens=self._max_output_tokens,
                previous_response_id=request.continuation_id,
            )
        )
        duration_ms = (perf_counter() - start) * 1000

        usage = self._map_usage(response.usage)

        tool_calls = []

        for item in response.output:
            if item.type == "function_call":
                tool_calls.append(
                    LLMToolCall(
                        call_id=item.call_id,
                        name=item.name,
                        arguments=item.arguments,
                    )
                )

        self._log_success(
            status=response.status,
            usage=usage,
            duration_ms=duration_ms,
            provider_request_id=response._request_id,
        )

        return LLMResult(
            text=response.output_text,
            usage=usage,
            status=response.status,
            incomplete_reason=self._map_incomplete_reason(response),
            tool_calls=tool_calls,
            continuation_id=response.id if hasattr(response, "id") else None,
        )

    async def generate_structured(
        self,
        request: LLMRequest,
        output_type: type[T],
    ) -> StructuredLLMResult[T]:
        start = perf_counter()

        try:
            response = await self._execute_with_retry(
                lambda: self._client.responses.parse(
                    model=self._model,
                    instructions=request.instructions,
                    input=[
                        {
                            "role": message.role.value,
                            "content": message.content,
                        }
                        for message in request.messages
                    ],
                    text_format=output_type,
                    max_output_tokens=self._max_output_tokens,
                )
            )
        except ValidationError as exc:
            raise LLMOutputError("LLM returned invalid structured output.") from exc

        duration_ms = (perf_counter() - start) * 1000

        parsed = response.output_parsed
        if parsed is None:
            raise LLMOutputError("LLM response did not contain structured output.")

        usage = self._map_usage(response.usage)

        self._log_success(
            status=response.status,
            usage=usage,
            duration_ms=duration_ms,
            provider_request_id=response._request_id,
        )

        return StructuredLLMResult(
            value=parsed,
            usage=usage,
            status=response.status,
            incomplete_reason=self._map_incomplete_reason(response),
        )

    @staticmethod
    def _map_usage(
        usage,
    ) -> LLMUsage | None:
        if usage is None:
            return None
        return LLMUsage(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cached_tokens=usage.input_tokens_details.cached_tokens,
            reasoning_tokens=usage.output_tokens_details.reasoning_tokens,
        )

    @staticmethod
    def _map_incomplete_reason(
        response,
    ) -> str | None:
        if response.incomplete_details is None:
            return None
        return response.incomplete_details.reason

    async def _execute_once(
        self,
        operation: Callable[[], Awaitable[R]],
    ) -> R:
        try:
            return await operation()

        except openai.RateLimitError as exc:
            if exc.code in {
                "credit_balance_exhausted",
                "insufficient_quota",
            }:
                raise LLMQuotaExceededError("LLM quota is unavailable.") from exc

            raise _RetryableLLMRateLimitError(
                "LLM provider rate limit reached."
            ) from exc
        except (
            openai.APITimeoutError,
            openai.APIConnectionError,
        ) as exc:
            raise _RetryableLLMUnavailableError("LLM provider request failed.") from exc
        except openai.APIStatusError as exc:
            if exc.status_code in {408, 409} or exc.status_code >= 500:
                raise _RetryableLLMUnavailableError(
                    "LLM provider is temporarily unavailable."
                ) from exc
            raise LLMIntegrationError("LLM provider rejected the request.") from exc
        except openai.APIResponseValidationError as exc:
            raise LLMIntegrationError(
                "LLM provider returned an invalid API response."
            ) from exc

    async def _execute_with_retry(
        self,
        operation: Callable[[], Awaitable[R]],
    ) -> R:
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self._max_attempts),
                wait=wait_exponential_jitter(
                    initial=self._retry_initial_wait,
                    max=self._retry_max_wait,
                ),
                retry=retry_if_exception_type(
                    (
                        _RetryableLLMUnavailableError,
                        _RetryableLLMRateLimitError,
                    )
                ),
                reraise=True,
            ):
                with attempt:
                    return await self._execute_once(operation)

        except _RetryableLLMRateLimitError as exc:
            raise LLMRateLimitError("LLM provider is rate limited.") from exc

        except _RetryableLLMUnavailableError as exc:
            raise LLMUnavailableError(
                "LLM provider is temporarily unavailable."
            ) from exc

        raise RuntimeError("LLM retry loop exited unexpectedly.")

    def _log_success(
        self,
        *,
        status: str | None,
        usage: LLMUsage | None,
        duration_ms: float,
        provider_request_id: str | None,
    ) -> None:
        logger.info(
            "LLM request completed "
            "model=%s status=%s "
            "input_tokens=%s output_tokens=%s "
            "total_tokens=%s "
            "duration_ms=%.2f "
            "provider_request_id=%s",
            self._model,
            status,
            usage.input_tokens if usage else None,
            usage.output_tokens if usage else None,
            usage.total_tokens if usage else None,
            duration_ms,
            provider_request_id,
        )

    async def stream(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]:
        start = perf_counter()
        stream = await self._client.responses.create(
            model=self._model,
            instructions=request.instructions,
            input=[
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in request.messages
            ],
            max_output_tokens=self._max_output_tokens,
            stream=True,
        )

        async for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta
            elif event.type == "response.completed":
                duration_ms = (perf_counter() - start) * 1000
                response = event.response
                usage = self._map_usage(response.usage)
                self._log_success(
                    status=response.status,
                    usage=usage,
                    duration_ms=duration_ms,
                    provider_request_id=(
                        response._request_id
                        if hasattr(
                            response,
                            "_request_id",
                        )
                        else None
                    ),
                )

    def _map_tools(
        self,
        tools: list[LLMToolDefinition],
    ) -> list[FunctionToolParam]:
        return [
            FunctionToolParam(
                type="function",
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
                strict=True,
            )
            for tool in tools
        ]

    def _map_input(
        self,
        request: LLMRequest,
    ) -> list[ResponseInputItemParam]:
        items: list[ResponseInputItemParam] = []

        for message in request.messages:
            message_item: EasyInputMessageParam = {
                "role": message.role.value,
                "content": message.content,
            }

            items.append(message_item)

        for tool_output in request.tool_outputs:
            tool_output_item: FunctionCallOutput = {
                "type": "function_call_output",
                "call_id": tool_output.call_id,
                "output": tool_output.output,
            }

            items.append(tool_output_item)

        return items
